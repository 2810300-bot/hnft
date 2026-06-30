#!/usr/bin/env python3
"""
花果畈厨余垃圾收运量月度数据分析构建器 v3.2

用法:
  # 默认：金山文档直读（推荐）
  python3 monthly_analysis_builder.py                                # 默认 kdocs 源
  python3 monthly_analysis_builder.py --month 2026-06                # 指定月份
  python3 monthly_analysis_builder.py --month 2026-06 --validate     # 仅校验已有数据

  # 回退：本地周数据
  python3 monthly_analysis_builder.py --source local                 # 本地 JSON 源
  python3 monthly_analysis_builder.py --source local --month 2026-06

数据源:
  kdocs: 通过 kdocs-cli 从金山文档 "每日数据-花果畈" 目录直读日数据文件
         优势: 无需等待周数据聚合，实时直读；支持车辆排名
  local: 读取本地 hnft-site/weekly-analysis/wXX_data.json
         优势: 离线可用; 劣势: 依赖周数据预生成

v3.2 更新:
  - kdocs 模式支持车辆排名：从每日文件车牌号字段解析并聚合月度TOP10/Bottom10

v3.1 更新:
  - DataValidator 数据校验框架（9类自动检测）
  - pending天排除：avg_daily 计算、weekday_pattern 均排除 pending
  - region trips 计数修复（按实际车次而非文件数）
  - weekly_breakdown date_range/trend_label 填充
  - mom环比自比Bug修复
  - 月度数据归档 (archive/)
  - HTML 数据质量警报

输出:  monthly_analysis.json + index.html
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, date, timedelta

# ============================================================
# 路径配置
# ============================================================
DEFAULT_WEEKLY_DIR = os.path.expanduser("~/.workbuddy/hnft-site/weekly-analysis")
DEFAULT_OUTPUT_DIR = os.path.expanduser("~/.workbuddy/hnft-site/monthly-analysis")
DEFAULT_DATA_DIR = os.path.expanduser("~/.workbuddy/reports")


def get_target_month(args):
    """解析目标月份，默认上月"""
    if args.month:
        parts = args.month.split("-")
        return int(parts[0]), int(parts[1])
    # 默认上月
    today = date.today()
    first = today.replace(day=1) - timedelta(days=1)
    return first.year, first.month


def find_weekly_files(weekly_dir, year, month):
    """找到属于目标月的所有周数据文件"""
    from calendar import monthrange
    
    _, last_day = monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)
    
    files = []
    if not os.path.isdir(weekly_dir):
        print(f"[WARN] 周数据目录不存在: {weekly_dir}")
        return files
    
    for fname in sorted(os.listdir(weekly_dir)):
        if not fname.startswith("w") or not fname.endswith("_data.json"):
            continue
        fpath = os.path.join(weekly_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[WARN] 读取失败: {fname}: {e}")
            continue
        
        # 检查 date_start / date_end 是否与目标月重叠
        ds = data.get("date_start", "")
        de = data.get("date_end", "")
        if not ds or not de:
            continue
        
        try:
            s = date.fromisoformat(ds)
            e = date.fromisoformat(de)
        except ValueError:
            continue
        
        # 周与月有重叠即可
        if s <= month_end and e >= month_start:
            files.append((fpath, data, s, e))
    
    return files


def aggregate_daily_data(weeks_data, year, month):
    """聚合所有周的 daily 数组为月度 daily 数组"""
    daily_map = {}  # date_str -> {total_kg, trips, weekday, week}
    
    weekdays_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    
    for week_num, wdata in weeks_data:
        for d in wdata.get("daily", []):
            date_str = d.get("date", "")  # e.g. "6月1日"
            if not date_str:
                continue
            # Parse date to get month info
            try:
                parts = date_str.replace("月", " ").replace("日", "").split()
                m = int(parts[0])
                day = int(parts[1])
                if m != month:
                    # Sometimes a week can span two months
                    try:
                        s = wdata.get("date_start", "")
                        e = wdata.get("date_end", "")
                        # If date is before date_start, it might be from a different parse
                        full_date = date(year, m, day)
                    except ValueError:
                        continue
                full_date = date(year, m, day)
                wd = weekdays_cn[full_date.weekday()]
            except (ValueError, IndexError):
                # fallback to provided weekday
                wd = d.get("weekday", "?")
                pass
            
            daily_map[date_str] = {
                "date": date_str,
                "weekday": d.get("weekday", wd),
                "total_kg": d.get("total", 0),
                "trips": d.get("trips", 0),
                "week": week_num
            }
    
    # Sort by date
    def sort_key(item):
        d = item[0]
        try:
            parts = d.replace("月", " ").replace("日", "").split()
            return (int(parts[0]), int(parts[1]))
        except:
            return (0, 0)
    
    sorted_daily = sorted(daily_map.items(), key=sort_key)
    return [v for k, v in sorted_daily]


def fill_missing_days(daily_list, year, month):
    """补齐当月缺失天数并标记 pending 状态
    
    当周数据文件尚未生成时（例如月末最后几天归属下一周，但该周数据未生成），
    自动检测当月应有天数与实际已有天数的差异，对缺失的过去日期以占位方式引入。
    未来日期不补齐（例如当天是6月29日，6月30日暂不补齐）。
    
    Args:
        daily_list: 已聚合的日数据列表
        year, month: 目标年月
    
    Returns:
        completed_list: 补齐后的日数据列表（含 pending 标记）
        pending_dates: 缺失的日期列表（作为 pending 状态标记）
    """
    from calendar import monthrange
    
    _, days_in_month = monthrange(year, month)
    today = date.today()
    
    # Build existing date set
    existing_dates = set()
    for item in daily_list:
        existing_dates.add(item.get("date", ""))
    
    pending_dates = []
    completed_list = list(daily_list)  # copy
    
    weekdays_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    month_label_map = {
        1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6",
        7: "7", 8: "8", 9: "9", 10: "10", 11: "11", 12: "12"
    }
    m_label = month_label_map[month]
    
    for day in range(1, days_in_month + 1):
        date_str = f"{m_label}月{day}日"
        if date_str in existing_dates:
            continue
        
        dt = date(year, month, day)
        
        # 仅补齐过去日期（含今天）
        if dt > today:
            continue
        
        wd = weekdays_cn[dt.weekday()]
        iso_week = dt.isocalendar()[1]
        
        completed_list.append({
            "date": date_str,
            "weekday": wd,
            "total_kg": 0,
            "trips": 0,
            "week": iso_week,
            "pending": True,
            "pending_reason": "数据待上传"
        })
        pending_dates.append(date_str)
    
    # Re-sort by date
    def sort_key(item):
        try:
            parts = item["date"].replace("月", " ").replace("日", "").split()
            return (int(parts[0]), int(parts[1]))
        except:
            return (0, 0)
    
    completed_list.sort(key=sort_key)
    return completed_list, pending_dates


# ============================================================
# 金山文档直读数据源（kdocs-cli）
# ============================================================
KDOCS_CLI = os.path.expanduser("~/.local/bin/kdocs-cli")
KDOCS_DRIVE_ID = "3117977951"
KDOCS_FOLDER_ID = "Ayxnj63aJrMfJpW2MZ1jxxhP8wQUPXDda"


def _kdocs_exec(params_json, service_action="drive list-files"):
    """执行 kdocs-cli 命令，返回解析后的 data 字段。失败返回 None。
    
    service_action 格式: "drive list-files" 或 "drive read-file"。
    params_json 直接作为命令行参数传入（非 stdin）。
    
    kdocs-cli --silent 返回: {code: 0, data: {items: [...]}}
    """
    import subprocess, shutil
    
    if not os.path.exists(KDOCS_CLI) and not shutil.which("kdocs-cli"):
        print("[WARN] kdocs-cli 未安装，跳过金山文档直读")
        return None
    
    cli_path = KDOCS_CLI if os.path.exists(KDOCS_CLI) else "kdocs-cli"
    parts = service_action.split()
    cmd = [cli_path] + parts + [params_json, "--silent"]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "PATH": f"{os.path.expanduser('~/.local/bin')}:{os.environ.get('PATH', '')}"}
        )
        stderr = result.stderr.strip()
        if result.returncode != 0:
            print(f"[WARN] kdocs-cli {service_action} 返回非零 (rc={result.returncode}): {stderr[:200]}")
            return None
        
        output = result.stdout.strip()
        if not output:
            print(f"[WARN] kdocs-cli {service_action}: 空输出")
            return None
        
        # Parse JSON — handle possible trailing upgrade notices
        idx = output.find("{")
        if idx < 0:
            return None
        
        depth = 0
        start = idx
        while idx < len(output):
            if output[idx] == "{":
                depth += 1
            elif output[idx] == "}":
                depth -= 1
                if depth == 0:
                    inner = json.loads(output[start:idx + 1])
                    # kdocs-cli --silent 返回: {code: 0, data: {...}}
                    if isinstance(inner, dict):
                        inner_data = inner.get("data", inner)
                        if isinstance(inner_data, dict):
                            # list-files: data.items
                            if "items" in inner_data:
                                return inner_data["items"]
                            # read-file: data 内部包含 range_data
                            if "range_data" in inner_data:
                                return inner_data
                            # read-file 可能有 content 包装
                            if "content" in inner_data:
                                content = inner_data["content"]
                                if isinstance(content, dict) and "range_data" in content:
                                    return content
                                return inner_data
                            return inner_data
                        if isinstance(inner_data, list):
                            return inner_data
                        return inner_data
                    return inner
            idx += 1
        
        return None
    except FileNotFoundError:
        print("[WARN] kdocs-cli 不可用")
        return None
    except json.JSONDecodeError as e:
        print(f"[WARN] kdocs-cli {service_action} JSON解析失败: {e}")
        return None
    except Exception as e:
        print(f"[WARN] kdocs-cli {service_action} 异常: {e}")
        return None


def list_kdocs_daily_files(year, month):
    """列出目标月份的所有日数据文件。

    返回列表: [(date_str, file_id), ...] 例如 [("6月1日", "d3ne..."), ...]
    """
    params = json.dumps({
        "drive_id": KDOCS_DRIVE_ID,
        "parent_id": KDOCS_FOLDER_ID,
        "page_size": 50,
        "order": "asc",
        "order_by": "fname"
    }, ensure_ascii=False)
    
    items = _kdocs_exec(params, service_action="drive list-files")
    if not items:
        return []
    
    month_files = []
    m_label = {1:"1", 2:"2", 3:"3", 4:"4", 5:"5", 6:"6",
               7:"7", 8:"8", 9:"9", 10:"10", 11:"11", 12:"12"}[month]
    prefix = f"{m_label}月"
    
    for item in items:
        name = item.get("name", "")
        fid = item.get("id", "")
        # 匹配格式: "M月D日餐厨.xls"
        if name.startswith(prefix) and "日餐厨.xls" in name:
            try:
                day_part = name[len(prefix):name.index("日餐厨.xls")]
                day_str = f"{prefix}{day_part}日"
                month_files.append((day_str, fid))
            except ValueError:
                continue
    
    print(f"[INFO] 金山文档: 找到 {len(month_files)} 个日数据文件 ({m_label}月)")
    return month_files


def parse_kdocs_xls(cells):
    """从 kdocs read_file 返回的 rangeData 中提取日收运数据。

    表格格式（列）:
      0: 序号, 1: 区域, 2: 车牌号, 3: 毛重, 4: 皮重, 5: 净重, 6: 差值, 7: 时间, 8: 状态

    返回: {"total_kg": int, "trips": int, "regions": {"区域名": kg, ...},
           "region_trips": {"区域名": count, ...},
           "vehicles": {"车牌号": {"kg": int, "trips": int, "region_trips": {"区域": count}, "unit": "主要区域"}, ...}}
    """
    total_kg = 0
    trips = 0
    regions = {}
    
    # 找到合计行
    max_row = 0
    is_summary = {}  # row -> True
    for cell in cells:
        r = cell.get("rowFrom", 0)
        max_row = max(max_row, r)
    
    # 识别合计行
    for cell in cells:
        t = cell.get("cellText", "").strip()
        if t == "合计":
            is_summary[cell.get("rowFrom", 0)] = True
    
    for cell in cells:
        r = cell.get("rowFrom", 0)
        c = cell.get("colFrom", 0)
        t = cell.get("cellText", "").strip()
        vt = cell.get("understandableType", {})
        val = vt.get("value", None)
        
        # 合计行的净重（第5列）
        if r in is_summary:
            if c == 5 and isinstance(val, (int, float)):
                total_kg = int(val)
            continue
        
        # 跳过标题行和表头
        if r <= 1:
            continue
        
        # 区域（第1列）
        if c == 1 and t:
            # 记录 trip（每行一个车次）
            trips += 1
        
        # 净重（第5列）
        if c == 5 and isinstance(val, (int, float)) and val > 0:
            # 需要关联到对应行的区域名
            pass  # 先标记净重，等区域名读取后再配对
    
    # 第二次遍历：构建行数据（区域、车牌号、净重）
    rows = {}  # row -> {region, plate, net_weight}
    for cell in cells:
        r = cell.get("rowFrom", 0)
        c = cell.get("colFrom", 0)
        t = cell.get("cellText", "").strip()
        vt = cell.get("understandableType", {})
        val = vt.get("value", None)
        
        if r <= 1 or r in is_summary:
            continue
        
        if r not in rows:
            rows[r] = {"region": "", "plate": "", "net_weight": 0}
        
        if c == 1 and t:
            rows[r]["region"] = t
        if c == 2 and t:
            rows[r]["plate"] = t
        if c == 5 and isinstance(val, (int, float)) and val > 0:
            rows[r]["net_weight"] = int(val)
    
    # 按区域汇总
    trips_count = 0
    region_trips = {}  # v3.1: 每个区域的实际车次数
    vehicles = {}  # v3.2: 按车牌聚合
    for row_key, row_data in rows.items():
        region = row_data.get("region", "")
        plate = row_data.get("plate", "")
        net = row_data.get("net_weight", 0)
        if region and net > 0:
            clean_region = _normalize_region(region)
            regions[clean_region] = regions.get(clean_region, 0) + net
            region_trips[clean_region] = region_trips.get(clean_region, 0) + 1
            trips_count += 1
            
            # 车牌聚合（空车牌按未知处理，不计入车辆排名）
            if plate:
                if plate not in vehicles:
                    vehicles[plate] = {
                        "kg": 0,
                        "trips": 0,
                        "region_trips": {},
                        "unit": clean_region  # 初始默认区域
                    }
                v = vehicles[plate]
                v["kg"] += net
                v["trips"] += 1
                v["region_trips"][clean_region] = v["region_trips"].get(clean_region, 0) + 1
                # 更新主要区域
                v["unit"] = max(v["region_trips"], key=v["region_trips"].get)
    
    if trips_count == 0:
        trips_count = len(rows)
    
    return {
        "total_kg": total_kg,
        "trips": trips_count,
        "regions": regions,
        "region_trips": region_trips,  # v3.1: 每个区域的车次数
        "vehicles": vehicles  # v3.2: 每辆车当天数据
    }


def _normalize_region(raw_name):
    """标准化区域名称"""
    mapping = {
        "岳阳楼区餐厨": "岳阳楼区",
        "岳阳楼区": "岳阳楼区",
        "开发区餐厨": "开发区",
        "开发区": "开发区",
        "君山区餐厨": "君山区",
        "岳阳君山区餐厨": "君山区",
        "君山区": "君山区",
        "临港新区餐厨": "临港新区",
        "临港新区": "临港新区",
        "南湖新区餐厨": "南湖新区",
        "南湖新区": "南湖新区",
    }
    return mapping.get(raw_name, raw_name)


def read_daily_from_kdocs(year, month):
    """金山文档直读：列出并解析所有日数据文件。
    
    Returns:
        daily_list: 同 aggregate_daily_data() 格式
        region_totals: {"岳阳楼区": {"kg": ..., "trips": ...}, ...}
        vehicle_totals: {"车牌号": {"kg": ..., "trips": ..., "unit": ...}, ...}
    """
    month_files = list_kdocs_daily_files(year, month)
    if not month_files:
        print("[WARN] 金山文档: 未找到目标月份文件，回退到本地周数据")
        return [], {}
    
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    daily_list = []
    region_totals = {}
    vehicle_totals = {}  # v3.2: 月度车辆聚合
    
    for i, (date_str, file_id) in enumerate(month_files):
        try:
            params = json.dumps({
                "file_id": file_id,
                "format": "markdown"
            }, ensure_ascii=False)
            
            data = _kdocs_exec(params, service_action="drive read-file")
            if not data:
                print(f"  [SKIP] {date_str}: 读取失败")
                continue
            
            # data 可能是 range_data dict 或包含 content 的 dict
            cells = data.get("range_data", {}).get("detail", {}).get("rangeData", [])
            if not cells and "content" in data:
                content = data["content"]
                cells = content.get("range_data", {}).get("detail", {}).get("rangeData", [])
            
            if not cells:
                print(f"  [SKIP] {date_str}: 无单元格数据 (keys={list(data.keys())[:5]})")
                continue
            
            parsed = parse_kdocs_xls(cells)
            
            # 解析日期获取星期
            try:
                m_str, d_str = date_str.replace("月", " ").replace("日", "").split()
                m, d = int(m_str), int(d_str)
                full_date = date(year, m, d)
                weekday = weekday_names[full_date.weekday()]
                iso_week = full_date.isocalendar()[1]
            except (ValueError, IndexError):
                weekday = "?"
                iso_week = 0
            
            daily_list.append({
                "date": date_str,
                "weekday": weekday,
                "total_kg": parsed["total_kg"],
                "trips": parsed["trips"],
                "week": iso_week
            })
            
            # 区域汇总 (v3.1: 按实际车次计数，非文件数)
            parsed_region_trips = parsed.get("region_trips", {})
            for rname, kg in parsed.get("regions", {}).items():
                if rname not in region_totals:
                    region_totals[rname] = {"kg": 0, "trips": 0}
                region_totals[rname]["kg"] += kg
                # 使用 parse_kdocs_xls 返回的每个区域的实际车次数
                actual_trips = parsed_region_trips.get(rname, 0)
                if actual_trips > 0:
                    region_totals[rname]["trips"] += actual_trips
                else:
                    # 回退：至少计 1 次（该区域当天有收运）
                    region_totals[rname]["trips"] += 1
            
            # 车辆汇总 (v3.2: 从每日文件聚合车牌)
            for plate, vdata in parsed.get("vehicles", {}).items():
                if plate not in vehicle_totals:
                    vehicle_totals[plate] = {
                        "kg": 0,
                        "trips": 0,
                        "region_trips": {},
                        "unit": vdata.get("unit", "")
                    }
                vt = vehicle_totals[plate]
                vt["kg"] += vdata.get("kg", 0)
                vt["trips"] += vdata.get("trips", 0)
                for rname, rcnt in vdata.get("region_trips", {}).items():
                    vt["region_trips"][rname] = vt["region_trips"].get(rname, 0) + rcnt
                # 主要区域 = 车次最多的区域
                if vt["region_trips"]:
                    vt["unit"] = max(vt["region_trips"], key=vt["region_trips"].get)
            
            if (i + 1) % 5 == 0 or i == len(month_files) - 1:
                print(f"  [PROGRESS] 已读取 {i+1}/{len(month_files)} 个文件")
            
        except Exception as e:
            print(f"  [SKIP] {date_str}: 解析异常 {e}")
            continue
    
    print(f"[INFO] 金山文档: 成功读取 {len(daily_list)} / {len(month_files)} 个文件, 车辆 {len(vehicle_totals)} 台")
    return daily_list, region_totals, vehicle_totals


def aggregate_regions(weeks_data):
    """聚合所有周的 regions 数据"""
    region_totals = {}  # name -> {kg, trips, total_avg_sum}
    
    for week_num, wdata in weeks_data:
        for r in wdata.get("regions", []):
            name = r.get("name", "")
            if not name:
                continue
            if name not in region_totals:
                region_totals[name] = {"kg": 0, "trips": 0, "avg_sum": 0, "avg_count": 0}
            region_totals[name]["kg"] += r.get("kg", 0)
            region_totals[name]["trips"] += r.get("trips", 0)
            if r.get("avg_per_trip"):
                region_totals[name]["avg_sum"] += r.get("avg_per_trip", 0) * r.get("trips", 1)
                region_totals[name]["avg_count"] += r.get("trips", 1)
    
    total_kg = sum(v["kg"] for v in region_totals.values())
    result = []
    for name, rt in sorted(region_totals.items(), key=lambda x: -x[1]["kg"]):
        result.append({
            "name": name,
            "kg": rt["kg"],
            "pct": round(rt["kg"] / total_kg * 100, 1) if total_kg else 0,
            "trips": rt["trips"],
            "avg_per_trip": round(rt["avg_sum"] / rt["avg_count"]) if rt["avg_count"] else 0
        })
    
    return result


def aggregate_vehicles(weeks_data):
    """聚合所有周的车辆数据"""
    vehicle_totals = {}  # plate -> {kg, trips, days_active_set, unit, mo_changes}
    
    for week_num, wdata in weeks_data:
        all_vehicles = (wdata.get("vehicles_top10", []) + 
                       wdata.get("vehicles_bottom10", []))
        for v in all_vehicles:
            plate = v.get("plate", "")
            if not plate:
                continue
            if plate not in vehicle_totals:
                vehicle_totals[plate] = {
                    "plate": plate,
                    "unit": v.get("unit", ""),
                    "kg": 0,
                    "trips": 0,
                    "avg_sum": 0,
                    "avg_count": 0,
                    "days_active": set()
                }
            vt = vehicle_totals[plate]
            vt["kg"] += v.get("total_kg", v.get("kg", 0))
            vt["trips"] += v.get("total_trips", v.get("trips", 0))
            vt["avg_sum"] += v.get("avg_per_trip", 0) * (v.get("total_trips", v.get("trips", 1)))
            vt["avg_count"] += v.get("total_trips", v.get("trips", 1))
            # Track active days from attendance string
            att = v.get("attendance", v.get("days_active", ""))
            if isinstance(att, str) and "/" in att:
                vt["days_active"] = att.split("/")[0]
            elif isinstance(att, (int, float)):
                vt["days_active"] = str(int(att))
    
    # Sort by kg descending
    sorted_vehicles = sorted(vehicle_totals.values(), 
                            key=lambda x: x["kg"], reverse=True)
    
    for v in sorted_vehicles:
        v["avg_per_trip"] = round(v["avg_sum"] / v["avg_count"]) if v["avg_count"] else 0
    
    top10 = sorted_vehicles[:10] if len(sorted_vehicles) >= 10 else sorted_vehicles
    bottom10 = sorted(sorted_vehicles[-10:], key=lambda x: x["kg"]) if len(sorted_vehicles) >= 10 else []
    
    return top10, bottom10, len(sorted_vehicles)


# ============================================================
# 数据校验框架 (v3.1)
# ============================================================
class DataValidator:
    """月度分析数据完整性校验器
    
    在生成报告后运行，自动检测以下问题：
    1. 时间连续性 - 检测日期缺失、重复
    2. 数值合理性 - 0值、负值、异常大值
    3. 字段完整性 - 必要字段是否存在
    4. 计算正确性 - pending天是否被正确排除在均值之外
    5. 数据质量评分 - 综合评分0-100
    """
    
    def __init__(self, report, year, month):
        self.report = report
        self.year = year
        self.month = month
        self.warnings = []
        self.errors = []
        self.quality_score = 100  # start perfect, deduct for issues
    
    def validate_all(self):
        """执行所有校验，返回校验报告"""
        self._check_schema()
        self._check_date_continuity()
        self._check_value_ranges()
        self._check_pending_exclusion()
        self._check_region_trips()
        self._check_weekly_fields()
        
        return {
            "is_valid": len(self.errors) == 0,
            "quality_score": max(0, self.quality_score),
            "severity": "ERROR" if self.errors else ("WARNING" if self.warnings else "OK"),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": self._build_summary(),
        }
    
    def _add_error(self, field, message):
        self.errors.append({"field": field, "message": message})
        self.quality_score -= 20
    
    def _add_warning(self, field, message):
        self.warnings.append({"field": field, "message": message})
        self.quality_score -= 5
    
    def _check_schema(self):
        """校验必填字段和结构完整性"""
        required = [
            "month", "year", "month_num", "label", "date_range",
            "total_kg", "total_ton", "total_trips",
            "daily", "weekly_breakdown", "regions",
            "weekday_pattern", "peak", "valley"
        ]
        for field in required:
            if field not in self.report or self.report[field] is None:
                self._add_error(f"schema.{field}", f"缺少必填字段: {field}")
        
        # daily 数组非空
        daily = self.report.get("daily", [])
        if not daily:
            self._add_error("schema.daily", "日数据数组为空")
        
        # weekly_breakdown 非空
        wb = self.report.get("weekly_breakdown", [])
        if not wb:
            self._add_warning("schema.weekly_breakdown", "周度分解数据为空")
        
        # vehicle_count 检查
        vc = self.report.get("vehicle_count", 0)
        if vc == -1:
            self._add_warning("vehicles", "车辆排名数据不可用（kdocs 模式暂不支持）")
    
    def _check_date_continuity(self):
        """校验日期连续性和缺失"""
        from calendar import monthrange
        
        daily = self.report.get("daily", [])
        _, days_in_month = monthrange(self.year, self.month)
        
        # Build date index (v3.1: 存储为实例属性供其他校验方法使用)
        self._date_map = {}
        duplicates = []
        for d in daily:
            dt = d.get("date", "")
            if dt in self._date_map:
                duplicates.append(dt)
            self._date_map[dt] = d
        
        if duplicates:
            self._add_error("daily.duplicate", f"重复日期: {', '.join(duplicates)}")
        
        # Check for gaps
        missing_dates = []
        pending_dates = []
        month_label_map = {
            1:"1",2:"2",3:"3",4:"4",5:"5",6:"6",
            7:"7",8:"8",9:"9",10:"10",11:"11",12:"12"
        }
        m_label = month_label_map[self.month]
        today = date.today()
        
        for day in range(1, days_in_month + 1):
            date_str = f"{m_label}月{day}日"
            if date_str not in self._date_map:
                dt = date(self.year, self.month, day)
                if dt > today:
                    # 未来日期不算缺失
                    continue
                missing_dates.append(date_str)
            elif self._date_map[date_str].get("pending"):
                pending_dates.append(date_str)
        
        if missing_dates:
            self._add_error("daily.missing", f"缺失日期 ({len(missing_dates)}天): {', '.join(missing_dates)}")
        
        # pending 日期是警告而非错误（等待上传是正常状态）
        if pending_dates:
            self._add_warning("daily.pending", f"待上传日期 ({len(pending_dates)}天): {', '.join(pending_dates)}")
        
        # 与报告声明的 pending_dates 一致性
        reported_pending = set(self.report.get("pending_dates", []))
        actual_pending = set(pending_dates)
        if reported_pending != actual_pending:
            self._add_warning("metadata.pending_mismatch",
                f"pending_dates 元数据不一致: 报告={reported_pending}, 实际={actual_pending}")
    
    def _check_value_ranges(self):
        """校验数值合理性"""
        daily = [d for d in self.report.get("daily", []) if not d.get("pending")]
        
        if not daily:
            self._add_warning("daily.no_valid_data", "无有效日数据（全部为 pending）")
            return
        
        # 收运量范围检查
        kgs = [d.get("total_kg", 0) for d in daily]
        trips_list = [d.get("trips", 0) for d in daily]
        
        # 零值检测（pending 已排除，出现0值异常）
        zero_kg = [d for d in daily if d.get("total_kg", 0) == 0]
        if zero_kg:
            self._add_warning("daily.zero_kg", f"{len(zero_kg)}天收运量为零: {', '.join(d['date'] for d in zero_kg)}")
        
        # 负值检测
        neg_kg = [d for d in daily if d.get("total_kg", 0) < 0]
        if neg_kg:
            self._add_error("daily.negative_kg", f"收运量出现负值: {', '.join(d['date'] + '=' + str(d['total_kg']) for d in neg_kg)}")
        
        # 异常大值检测（3倍标准差）
        if len(kgs) >= 3:
            avg_kg = sum(kgs) / len(kgs)
            variance = sum((k - avg_kg) ** 2 for k in kgs) / len(kgs)
            stddev = variance ** 0.5
            threshold = avg_kg + 3 * stddev
            outliers = [d for d in daily if d.get("total_kg", 0) > threshold]
            if outliers:
                self._add_warning("daily.outliers",
                    f"异常高值 (>{threshold:.0f}kg): {', '.join(d['date'] + '=' + str(d['total_kg']) + 'kg' for d in outliers)}")
        
        # trips 范围检查
        if trips_list:
            zero_trips = [d for d in daily if d.get("trips", 0) == 0 and d.get("total_kg", 0) > 0]
            if zero_trips:
                self._add_warning("daily.zero_trips", f"有收运量但车次为零: {', '.join(d['date'] for d in zero_trips)}")
        
        # 峰值谷值一致性
        peak_date = self.report.get("peak", {}).get("date", "")
        if peak_date and peak_date in self._date_map:
            peak_data = self._date_map[peak_date]
            if peak_data.get("total_kg", 0) != self.report.get("peak", {}).get("kg", 0):
                self._add_warning("peak.mismatch", f"峰值数据不一致: {peak_date}")
        
        # regions: kg 和 pct 校验
        regions = self.report.get("regions", [])
        if regions:
            total_kg = self.report.get("total_kg", 0)
            region_sum = sum(r.get("kg", 0) for r in regions)
            if region_sum > 0:
                pct_diff = abs(region_sum - total_kg) / total_kg * 100
                if pct_diff > 5:
                    self._add_warning("regions.sum_mismatch",
                        f"区域合计({region_sum}kg)与总量({total_kg}kg)偏差 {pct_diff:.1f}%")
        
        # weekday_pattern 合理性
        wp = self.report.get("weekday_pattern", {})
        workday = wp.get("workday_avg_kg", 0)
        weekend = wp.get("weekend_avg_kg", 0)
        if workday > 0 and weekend > workday:
            self._add_warning("weekday_pattern.inverted", "周末均值高于工作日均值（可能为异常）")
    
    def _check_pending_exclusion(self):
        """确保 pending 天未参与有效数据计算"""
        daily = self.report.get("daily", [])
        non_pending = [d for d in daily if not d.get("pending")]
        pending_count = len([d for d in daily if d.get("pending")])
        
        if not non_pending:
            return
        
        # 日均计算应仅基于有效天数
        actual_total_kg = sum(d.get("total_kg", 0) for d in non_pending)
        actual_trips = sum(d.get("trips", 0) for d in non_pending)
        actual_days = len(non_pending)
        
        # 检查报告的 avg_daily 是否排除了 pending（关键校验）
        reported_avg = self.report.get("avg_daily_kg", 0)
        expected_avg_no_pending = round(actual_total_kg / actual_days) if actual_days else 0
        reported_all_avg = round(self.report.get("total_kg", 0) / self.report.get("data_days", 1))
        
        if reported_avg == reported_all_avg and pending_count > 0:
            self._add_error("calc.avg_daily_kg",
                f"日均计算错误: pending天({pending_count}天)被错误纳入分母。"
                f"当前={reported_avg}kg(含pending), 应为={expected_avg_no_pending}kg(排除pending)")
        
        # 检查 weekday_pattern 的 weekday 均值
        wp = self.report.get("weekday_pattern", {})
        for wd in ["周一","周二","周三","周四","周五","周六","周日"]:
            if wd not in wp:
                continue
            # 根据 weekday 筛选 non_pending
            wd_pending = [d for d in daily if d.get("pending") and d.get("weekday") == wd]
            if not wd_pending:
                continue
            
            wp_count = wp[wd].get("count", 0)
            non_pending_count = len([d for d in non_pending if d.get("weekday") == wd])
            if wp_count > non_pending_count:
                self._add_warning(f"weekday_pattern.{wd}.count",
                    f"{wd}统计天数({wp_count})包含{len(wd_pending)}个pending天，"
                    f"导致{wd}均值偏低")
    
    def _check_region_trips(self):
        """校验区域 trips 计数"""
        daily = self.report.get("daily", [])
        non_pending = [d for d in daily if not d.get("pending")]
        regions = self.report.get("regions", [])
        
        if not regions:
            return
        
        # 区域 trips 总数应与日总 trips 之和相同量级
        total_daily_trips = sum(d.get("trips", 0) for d in non_pending)
        region_trips_sum = sum(r.get("trips", 0) for r in regions)
        
        # 每个 region 的 trips 应该等于有该区域数据的文件数（约为有效天数）
        # 如果所有区域 trips 都等于有效天数，说明是按文件数计而非实际车次数
        if total_daily_trips > 0 and region_trips_sum > 0:
            if region_trips_sum <= len(non_pending) * 5:  # 5个区域 × 天数
                # 检查各区域 trips 是否都接近同一个值
                region_trip_values = [r.get("trips", 0) for r in regions]
                if len(set(region_trip_values)) <= 1:
                    self._add_warning("regions.trips_count",
                        f"区域车次均为 {region_trip_values[0] if region_trip_values else 0}，"
                        f"疑似按文件数计数而非实际车次数。应考虑按实际车次聚合。")
    
    def _check_weekly_fields(self):
        """校验周度字段完整性"""
        wb = self.report.get("weekly_breakdown", [])
        if not wb:
            return
        
        empty_date_ranges = [w["week"] for w in wb if not w.get("date_range")]
        if empty_date_ranges:
            self._add_warning("weekly.date_range",
                f"以下周的 date_range 为空: W{', W'.join(str(w) for w in empty_date_ranges)}")
        
        # v3.1: 第一周 trend_label 为空是正常的（无前一周对比），不报警告
        empty_trend = [w["week"] for w in wb if not w.get("trend_label")]
        if len(empty_trend) > 1:  # 超过1个才报警告
            self._add_warning("weekly.trend_label",
                f"以下周的 trend_label 为空: W{', W'.join(str(w) for w in empty_trend)}")
        elif len(empty_trend) == 1:
            first_trend_week = empty_trend[0]
            if first_trend_week != wb[0]["week"]:
                self._add_warning("weekly.trend_label",
                    f"第W{first_trend_week}周 trend_label 为空（非首周）")
    
    def _build_summary(self):
        """生成可读的校验摘要"""
        parts = []
        
        daily = self.report.get("daily", [])
        non_pending = [d for d in daily if not d.get("pending")]
        pending = [d for d in daily if d.get("pending")]
        
        parts.append(f"数据覆盖: {len(non_pending)}/{self.report.get('days_in_month', '?')}天有效")
        if pending:
            parts.append(f"待上传: {len(pending)}天({', '.join(d['date'] for d in pending)})")
        
        if self.errors:
            parts.append(f"严重问题: {len(self.errors)}项")
        if self.warnings:
            parts.append(f"警告: {len(self.warnings)}项")
        
        parts.append(f"质量评分: {self.quality_score}/100")
        
        return " | ".join(parts)


def compute_weekday_pattern(daily_list):
    """计算工作日/周末收运模式
    
    v3.1: 排除 pending 天，避免 0 值拉低均值
    """
    pattern = defaultdict(lambda: {"total_kg": 0, "count": 0})
    for d in daily_list:
        if d.get("pending"):
            continue  # 跳过待上传天数
        wd = d.get("weekday", "")
        if wd:
            pattern[wd]["total_kg"] += d.get("total_kg", 0)
            pattern[wd]["count"] += 1
    
    result = {}
    for wd in ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]:
        p = pattern.get(wd)
        if p and p["count"] > 0:
            result[wd] = {
                "avg_kg": round(p["total_kg"] / p["count"]),
                "avg_ton": round(p["total_kg"] / p["count"] / 1000, 1),
                "count": p["count"]
            }
    
    # Separate workday vs weekend
    workday_total = sum(pattern[wd]["total_kg"] for wd in ["周一", "周二", "周三", "周四", "周五"] if wd in pattern)
    workday_count = sum(pattern[wd]["count"] for wd in ["周一", "周二", "周三", "周四", "周五"] if wd in pattern)
    weekend_total = sum(pattern[wd]["total_kg"] for wd in ["周六", "周日"] if wd in pattern)
    weekend_count = sum(pattern[wd]["count"] for wd in ["周六", "周日"] if wd in pattern)
    
    result["workday_avg_kg"] = round(workday_total / workday_count) if workday_count else 0
    result["workday_avg_ton"] = round(workday_total / workday_count / 1000, 1) if workday_count else 0
    result["weekend_avg_kg"] = round(weekend_total / weekend_count) if weekend_count else 0
    result["weekend_avg_ton"] = round(weekend_total / weekend_count / 1000, 1) if weekend_count else 0
    result["weekend_drop_pct"] = round(
        (1 - result["weekend_avg_kg"] / result["workday_avg_kg"]) * 100, 1
    ) if result["workday_avg_kg"] > 0 and result["weekend_avg_kg"] > 0 else 0
    
    return result


def get_mom_comparison(weekly_dir, year, month):
    """获取环比变化（与上月对比）
    
    v3.1: 修复自比Bug——不再读取 monthly-analysis/data.json (会读到当前月数据)
    改为优先读取月度归档文件 archive/{prev_year}-{prev_month:02d}.json
    """
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    
    prev_total = 0
    
    # v3.1: 优先从归档文件读取上月数据
    archive_path = os.path.join(
        os.path.dirname(weekly_dir), "monthly-analysis", "archive",
        f"{prev_year}-{prev_month:02d}.json"
    )
    if os.path.isfile(archive_path):
        try:
            with open(archive_path, "r", encoding="utf-8") as f:
                prev_data = json.load(f)
                prev_total = prev_data.get("total_ton", 0)
                if prev_total > 0:
                    return prev_total
        except Exception:
            pass
    
    # 回退：从周数据中估算上月总量
    if prev_total == 0:
        prev_files = find_weekly_files(weekly_dir, prev_year, prev_month)
        prev_total = sum(w[1].get("total_ton", 0) for w in prev_files) if prev_files else 0
    
    return prev_total


def build_monthly_report(weekly_dir, year, month, source="local"):
    """构建月度分析数据
    
    Args:
        weekly_dir: 本地周数据目录（local 模式）
        year, month: 目标年月
        source: "local" (读取本地周数据JSON) 或 "kdocs" (金山文档直读)
    """
    from calendar import monthrange
    
    _, days_in_month = monthrange(year, month)
    month_label_map = {
        1: "1月", 2: "2月", 3: "3月", 4: "4月",
        5: "5月", 6: "6月", 7: "7月", 8: "8月",
        9: "9月", 10: "10月", 11: "11月", 12: "12月"
    }
    
    # 数据源：本地周数据 或 金山文档直读
    if source == "kdocs":
        print(f"[INFO] 数据源: 金山文档直读")
        daily_list, region_map, vehicle_map = read_daily_from_kdocs(year, month)
        if not daily_list:
            print("[WARN] 金山文档读取失败或无数据，回退到本地周数据")
            source = "local"
    
    weeks_data = []
    region_list = []
    top10_vehicles = []
    bottom10_vehicles = []
    vehicle_count = 0
    
    if source == "local":
        weekly_files = find_weekly_files(weekly_dir, year, month)
        if not weekly_files:
            print(f"[WARN] 未找到 {year}年{month}月 的周数据文件")
            return None
        
        weeks_data = [(d[1].get("week", 0), d[1]) for d in weekly_files]
        weeks_data.sort(key=lambda x: x[0])
        
        daily_list = aggregate_daily_data(weeks_data, year, month)
        # 补齐月末缺失天数（例如 29、30 日属于下一周，周数据文件尚未生成）
        daily_list, pending_dates = fill_missing_days(daily_list, year, month)
        region_list = aggregate_regions(weeks_data)
        top10_vehicles, bottom10_vehicles, vehicle_count = aggregate_vehicles(weeks_data)
        
    else:  # kdocs
        # 补齐缺失天数（6月30日尚未上传到金山文档）
        daily_list, pending_dates = fill_missing_days(daily_list, year, month)
        
        # 从 region_map 构造 region_list
        sorted_regions = sorted(region_map.items(), key=lambda x: x[1]["kg"], reverse=True)
        for rname, rdata in sorted_regions:
            avg_per_day = round(rdata["kg"] / len([d for d in daily_list if d["total_kg"] > 0])) if daily_list else 0
            region_list.append({
                "name": rname,
                "kg": rdata["kg"],
                "trips": rdata["trips"],
                "avg_per_day_kg": avg_per_day
            })
        
        # 从 vehicle_map 构造车辆排名 (v3.2)
        if vehicle_map:
            sorted_vehicles = sorted(
                [{"plate": plate, **vdata} for plate, vdata in vehicle_map.items()],
                key=lambda x: x["kg"], reverse=True
            )
            for v in sorted_vehicles:
                v["avg_per_trip"] = round(v["kg"] / v["trips"]) if v["trips"] else 0
                v.pop("region_trips", None)  # 前端不需要
            top10_vehicles = sorted_vehicles[:10] if len(sorted_vehicles) >= 10 else sorted_vehicles
            bottom10_vehicles = sorted(sorted_vehicles[-10:], key=lambda x: x["kg"]) if len(sorted_vehicles) >= 10 else []
            vehicle_count = len(sorted_vehicles)
        else:
            # 无车牌数据时降级显示
            top10_vehicles = []
            bottom10_vehicles = []
            vehicle_count = -1
        
    # 计算周度分解（kdocs 模式从 daily_list 自行分组）
    if source == "kdocs" and daily_list:
        week_groups = defaultdict(lambda: {"start": None, "end": None, "days": 0, "valid_days": 0, "total_kg": 0, "total_trips": 0})
        for d in daily_list:
            wk = d.get("week", 0)
            if wk == 0:
                continue
            wg = week_groups[wk]
            wg["total_kg"] += d.get("total_kg", 0)
            wg["total_trips"] += d.get("trips", 0)
            wg["days"] += 1
            if not d.get("pending"):
                wg["valid_days"] += 1
            # 推算该周的起止日期
            date_str = d.get("date", "")
            try:
                m_s, d_s = date_str.replace("月", " ").replace("日", "").split()
                day_num = int(d_s)
            except (ValueError, IndexError):
                continue
            if wg["start"] is None or day_num < wg["start"]:
                wg["start"] = day_num
            if wg["end"] is None or day_num > wg["end"]:
                wg["end"] = day_num
        
        m_label = {1:"1月",2:"2月",3:"3月",4:"4月",5:"5月",6:"6月",
                   7:"7月",8:"8月",9:"9月",10:"10月",11:"11月",12:"12月"}[month]
        weeks_data = []
        for wk in sorted(week_groups.keys()):
            wg = week_groups[wk]
            start_label = f"{m_label}{wg['start']}日" if wg["start"] is not None else f"W{wk}"
            end_label = f"{m_label}{wg['end']}日" if wg["end"] is not None else f"W{wk}"
            weeks_data.append((
                wk,
                {
                    "week": wk,
                    "date_start": f"{year}-{month:02d}-{wg['start']:02d}" if wg["start"] else "",
                    "date_end": f"{year}-{month:02d}-{wg['end']:02d}" if wg["end"] else "",
                    "start_label": start_label,
                    "end_label": end_label,
                    "days": wg["days"],
                    "valid_days": wg["valid_days"],
                    "total_kg": wg["total_kg"],
                    "total_ton": round(wg["total_kg"] / 1000, 1),
                    "total_trips": wg["total_trips"],
                    "avg_daily_ton": round(wg["total_kg"] / wg["valid_days"] / 1000, 1) if wg["valid_days"] else 0
                }
            ))
        weeks_data.sort(key=lambda x: x[0])
    
    weekday_pattern = compute_weekday_pattern(daily_list)
    
    # 计算月度总计 (v3.1: 有效天/总天数分开统计)
    total_kg = sum(d["total_kg"] for d in daily_list)
    total_trips = sum(d["trips"] for d in daily_list)
    actual_days = len(daily_list)
    
    # 有效天数（排除 pending）
    valid_days = [d for d in daily_list if not d.get("pending")]
    valid_day_count = len(valid_days)
    valid_kg = sum(d["total_kg"] for d in valid_days)
    valid_trips = sum(d["trips"] for d in valid_days)
    
    # avg_daily 仅基于有效天数计算
    avg_daily_kg = round(valid_kg / valid_day_count) if valid_day_count else 0
    
    # 峰值/谷值（仅统计已有数据的天数）
    valid_days = [d for d in daily_list if not d.get("pending")]
    peak_entry = max(valid_days, key=lambda d: d["total_kg"]) if valid_days else {}
    valley_entry = min(valid_days, key=lambda d: d["total_kg"]) if valid_days else {}
    
    # 环比
    prev_month_total = get_mom_comparison(weekly_dir, year, month)
    mom_change = round(total_kg / 1000 - prev_month_total, 1) if prev_month_total else 0
    mom_pct = round((total_kg / 1000 / prev_month_total - 1) * 100, 1) if prev_month_total else None
    
    # 趋势判断
    trend = "up" if mom_change > 0 else ("down" if mom_change < 0 else "flat")
    trend_label = "环比增长" if mom_change > 0 else ("环比下降" if mom_change < 0 else "环比持平")
    
    # 周分解
    weekly_breakdown = []
    prev_ton = None
    for week_num, wdata in weeks_data:
        # v3.1: 构建 date_range（优先 kdocs 的 start_label/end_label，回退到固定格式）
        if wdata.get("start_label") and wdata.get("end_label"):
            date_range_str = f"{wdata['start_label']} - {wdata['end_label']}"
        else:
            date_range_str = wdata.get("date_range", "")
        
        # v3.1: 计算周间趋势
        cur_ton = wdata.get("total_ton", 0)
        if prev_ton and prev_ton > 0:
            change_pct = round((cur_ton - prev_ton) / prev_ton * 100, 1)
            trend = "up" if change_pct > 0 else ("down" if change_pct < 0 else "flat")
            trend_label = f"{'+' if change_pct >= 0 else ''}{change_pct}%"
            if trend == "up":
                trend_color = "#16a34a"
            elif trend == "down":
                trend_color = "#e15759"
            else:
                trend_color = "#64748b"
        else:
            trend_label = ""
            trend_color = "#4C72B0"
        prev_ton = cur_ton
        
        # v3.1: avg_daily 排除 pending 天（仅有效天参与分母计算）
        w_valid_days = wdata.get("valid_days", wdata.get("days", 0))
        avg_daily_ton = round(cur_ton / w_valid_days, 1) if w_valid_days else 0
        
        weekly_breakdown.append({
            "week": week_num,
            "total_ton": cur_ton,
            "avg_daily": avg_daily_ton,
            "total_trips": wdata.get("total_trips", 0),
            "date_range": date_range_str,
            "trend_label": trend_label,
            "trend_color": trend_color
        })
    
    # 组装报告
    report = {
        "schema_version": 2,  # v3.1: 数据校验框架 + pending天排除
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "month": f"{year:04d}-{month:02d}",
        "year": year,
        "month_num": month,
        "label": f"{year}年{month_label_map[month]}",
        "date_range": f"{month}月1日 - {month}月{days_in_month}日",
        "days_in_month": days_in_month,
        "data_days": actual_days,
        "pending_dates": pending_dates,
        "pending_count": len(pending_dates),
        "has_pending": len(pending_dates) > 0,
        "weeks_covered": [wb["week"] for wb in weekly_breakdown],
        
        # 月度 KPI
        "total_kg": total_kg,
        "total_ton": round(total_kg / 1000, 1),
        "total_trips": total_trips,
        "avg_daily_kg": avg_daily_kg,
        "avg_daily_ton": round(avg_daily_kg / 1000, 1),
        "avg_daily_trips": round(valid_trips / valid_day_count, 1) if valid_day_count else 0,
        
        # 峰值谷值
        "peak": {
            "date": peak_entry.get("date", ""),
            "weekday": peak_entry.get("weekday", ""),
            "kg": peak_entry.get("total_kg", 0),
            "ton": round(peak_entry.get("total_kg", 0) / 1000, 1),
            "trips": peak_entry.get("trips", 0)
        } if peak_entry else {},
        "valley": {
            "date": valley_entry.get("date", ""),
            "weekday": valley_entry.get("weekday", ""),
            "kg": valley_entry.get("total_kg", 0),
            "ton": round(valley_entry.get("total_kg", 0) / 1000, 1),
            "trips": valley_entry.get("trips", 0)
        } if valley_entry else {},
        
        # 环比
        "prev_month_total_ton": prev_month_total,
        "mom_change_ton": mom_change,
        "mom_change_pct": mom_pct,
        "trend": trend,
        "trend_label": trend_label,
        
        # 日数据
        "daily": daily_list,
        
        # 周分解
        "weekly_breakdown": weekly_breakdown,
        
        # 区域
        "regions": region_list,
        
        # 车辆
        "vehicles_top10": top10_vehicles,
        "vehicles_bottom10": bottom10_vehicles,
        "vehicle_count": vehicle_count,
        
        # 工作日模式
        "weekday_pattern": weekday_pattern,
        
        # v3.1: 数据质量校验报告
        "data_quality": {},  # 将在校验后填充
    }
    
    # v3.1: 运行数据校验
    validator = DataValidator(report, year, month)
    quality_report = validator.validate_all()
    report["data_quality"] = quality_report
    
    # 输出校验摘要
    if quality_report["severity"] == "ERROR":
        print(f"\n[VALIDATION] 发现 {quality_report['error_count']} 个严重问题, "
              f"{quality_report['warning_count']} 个警告")
        for err in quality_report["errors"]:
            print(f"  [ERROR] [{err['field']}] {err['message']}")
        for warn in quality_report["warnings"]:
            print(f"  [WARN]  [{warn['field']}] {warn['message']}")
    elif quality_report["severity"] == "WARNING":
        print(f"\n[VALIDATION] 数据质量评分: {quality_report['quality_score']}/100, "
              f"{quality_report['warning_count']} 个警告")
        for warn in quality_report["warnings"]:
            print(f"  [WARN]  [{warn['field']}] {warn['message']}")
    else:
        print(f"\n[VALIDATION] 数据质量评分: {quality_report['quality_score']}/100, 校验通过")
    
    return report


def generate_html(report):
    """生成月度分析 HTML 页面"""
    report_json = json.dumps(report, ensure_ascii=False, indent=2)
    
    # 准备区域饼图颜色
    region_colors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1']
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>厨余垃圾收运量月度数据分析 · {report["label"]}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg: #f0f2f5;
  --card-bg: #ffffff;
  --header-bg: #1a1a2e;
  --header-bg2: #16213e;
  --text: #1e293b;
  --text-secondary: #64748b;
  --text-light: #e2e8f0;
  --border: #e2e8f0;
  --border-light: #f1f5f9;
  --radius: 14px;
  --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
  --shadow-hover: 0 4px 12px rgba(0,0,0,0.1), 0 8px 32px rgba(0,0,0,0.08);
  --accent-blue: #4C72B0;
  --accent-green: #16a34a;
  --accent-orange: #DD8452;
  --accent-red: #e15759;
  --accent-cyan: #0891b2;
  --accent-purple: #7c3aed;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.6;
}}

/* Breadcrumb */
.breadcrumb-bar {{
  background: var(--card-bg);
  border-bottom: 1px solid var(--border);
  padding: 10px 24px;
  font-size: 13px;
  color: var(--text-secondary);
}}
.breadcrumb-bar a {{ color: var(--accent-blue); text-decoration: none; font-weight: 500; }}
.breadcrumb-bar a:hover {{ text-decoration: underline; }}
.breadcrumb-bar .sep {{ color: #94a3b8; margin: 0 8px; }}

/* Header */
.site-header {{
  background: linear-gradient(135deg, var(--header-bg), var(--header-bg2));
  color: var(--text-light);
  padding: 32px 40px;
  position: relative;
  overflow: hidden;
}}
.site-header::after {{
  content: '';
  position: absolute;
  top: -30%; right: -5%;
  width: 360px; height: 360px;
  background: radial-gradient(circle, rgba(255,255,255,0.04) 0%, transparent 70%);
  border-radius: 50%;
}}
.header-content {{
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}}
.header-content h1 {{ font-size: 26px; font-weight: 700; letter-spacing: 1px; margin-bottom: 4px; }}
.header-content .subtitle {{ font-size: 13px; color: rgba(255,255,255,0.55); }}
.header-meta {{
  display: flex; gap: 20px; margin-top: 12px; flex-wrap: wrap;
  font-size: 12px; color: rgba(255,255,255,0.6);
}}

/* Main */
.main-container {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 28px 24px 48px;
}}

/* Section */
.section-title {{
  font-size: 18px; font-weight: 700; color: var(--text);
  margin-bottom: 16px; padding-bottom: 10px;
  border-bottom: 2px solid var(--border);
  display: flex; align-items: center; gap: 10px;
}}
.section-subtitle {{
  font-size: 15px; font-weight: 600; color: var(--text);
  margin: 20px 0 12px;
}}

/* KPI Row */
.kpi-row {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}}
.kpi-card {{
  background: var(--card-bg);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
  text-align: center;
  border-top: 3px solid transparent;
}}
.kpi-card:nth-child(1) {{ border-top-color: var(--accent-blue); }}
.kpi-card:nth-child(2) {{ border-top-color: var(--accent-green); }}
.kpi-card:nth-child(3) {{ border-top-color: var(--accent-orange); }}
.kpi-card:nth-child(4) {{ border-top-color: var(--accent-purple); }}
.kpi-card .label {{ font-size: 12px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }}
.kpi-card .value {{ font-size: 30px; font-weight: 700; color: var(--text); line-height: 1.2; }}
.kpi-card .unit {{ font-size: 14px; color: var(--text-secondary); margin-left: 2px; font-weight: 400; }}
.kpi-card .sub {{ font-size: 12px; color: var(--text-secondary); margin-top: 4px; }}
.kpi-card .sub.up {{ color: var(--accent-green); font-weight: 600; }}
.kpi-card .sub.down {{ color: var(--accent-red); font-weight: 600; }}

/* Chart Grid */
.chart-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 28px;
}}
.chart-grid .full {{ grid-column: 1 / -1; }}
.chart-card {{
  background: var(--card-bg);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
}}
.chart-card h3 {{
  font-size: 14px; font-weight: 600;
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text);
}}
.chart-card canvas {{ max-height: 320px; }}

/* Tables */
.detail-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-top: 8px;
}}
.detail-table th {{
  background: #f8fafc;
  text-align: left;
  padding: 10px 14px;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid var(--border);
}}
.detail-table td {{
  padding: 9px 14px;
  border-bottom: 1px solid var(--border-light);
}}
.detail-table tr:last-child td {{ border-bottom: none; }}
.detail-table tr:hover td {{ background: #f8fafc; }}

/* Table Card */
.table-card {{
  background: var(--card-bg);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
  margin-bottom: 20px;
}}
.table-card h3 {{
  font-size: 14px; font-weight: 600;
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text);
}}

/* Dual Table Row */
.dual-table {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 28px;
}}

/* Footer */
.site-footer {{
  text-align: center;
  padding: 32px 24px;
  color: var(--text-secondary);
  font-size: 12px;
  border-top: 1px solid var(--border);
  margin-top: 48px;
}}

/* Responsive */
@media (max-width: 768px) {{
  .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
  .chart-grid {{ grid-template-columns: 1fr; }}
  .dual-table {{ grid-template-columns: 1fr; }}
  .site-header {{ padding: 24px 20px; }}
  .header-content h1 {{ font-size: 22px; }}
  .main-container {{ padding: 20px 16px 32px; }}
}}

.peak-cell {{ color: var(--accent-red); font-weight: 600; }}
.valley-cell {{ color: var(--accent-green); font-weight: 600; }}

/* Pending Alert */
.pending-alert {{
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  border: 1px solid #fbbf24;
  border-radius: var(--radius);
  padding: 14px 20px;
  margin-bottom: 20px;
  font-size: 13px;
  color: #92400e;
  display: flex;
  align-items: center;
  gap: 10px;
}}
.pending-alert .icon {{ font-size: 20px; }}
.pending-date {{
  display: inline-block;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 4px;
  padding: 1px 8px;
  margin: 0 3px;
  font-weight: 600;
  color: #b45309;
}}
@media (max-width: 768px) {{
  .pending-alert {{ flex-direction: column; align-items: flex-start; }}
}}
</style>
</head>
<body>

<div class="breadcrumb-bar">
  <a href="../">🏠 看板中心</a><span class="sep">/</span>
  <a href="./">📊 月度数据分析</a>
</div>

<header class="site-header">
  <div class="header-content">
    <h1>📊 厨余垃圾收运量 · 月度数据分析</h1>
    <div class="subtitle">{report["label"]} · 花果畈餐厨垃圾处理项目</div>
    <div class="header-meta">
      <span>📅 报告月: {report["date_range"]}</span>
      <span>🔢 已加载 {report["data_days"]} 天数据（覆盖 {len(report["weeks_covered"])} 周）{', <em style=\\"color:#fbbf24;\\">' + str(report['pending_count']) + ' 天待上传</em>' if report['has_pending'] else ''}</span>
      <span>🔍 数据质量: {report.get("data_quality", {}).get("quality_score", "--")}/100</span>
      <span>🔄 生成于 {report["generated_at"]}</span>
    </div>
  </div>
</header>

<div class="main-container">

  <!-- v3.1: 数据质量警报 -->
  <div id="quality-alert" style="display:none;"></div>

  <!-- KPI Cards -->
  <div class="kpi-row" id="kpi-row"></div>

  <!-- 环比趋势 KPI -->
  <div class="kpi-row" id="kpi-trend-row"></div>

  <!-- Pending Data Alert -->
  <div id="pending-alert" style="display:none;"></div>

  <!-- Charts: Weekly Breakdown + Daily Trend -->
  <div class="chart-grid">
    <div class="chart-card">
      <h3>📅 周度收运量分解</h3>
      <canvas id="chart-weekly-breakdown"></canvas>
    </div>
    <div class="chart-card">
      <h3>📈 日收运量趋势</h3>
      <canvas id="chart-daily-trend"></canvas>
    </div>
    <div class="chart-card">
      <h3>🏘️ 区域收运分布</h3>
      <canvas id="chart-region-pie"></canvas>
    </div>
    <div class="chart-card">
      <h3>📅 工作日 vs 周末收运模式</h3>
      <canvas id="chart-weekday-pattern"></canvas>
    </div>
  </div>

  <!-- 周度明细表 -->
  <div class="table-card">
    <h3>📋 周度收运明细</h3>
    <table class="detail-table">
      <thead><tr><th>周次</th><th>日期范围</th><th>周总量 (吨)</th><th>日均 (吨)</th><th>车次</th><th>趋势</th></tr></thead>
      <tbody id="weekly-detail-body"></tbody>
    </table>
  </div>

  <!-- 区域 + 工作日模式 双栏 -->
  <div class="dual-table">
    <div class="table-card">
      <h3>🏘️ 各区域收运量占比</h3>
      <table class="detail-table">
        <thead><tr><th>区域</th><th>月总量 (吨)</th><th>占比</th><th>车次</th><th>车均 (kg)</th></tr></thead>
        <tbody id="region-table-body"></tbody>
      </table>
    </div>
    <div class="table-card">
      <h3>📅 工作日/周末收运模式</h3>
      <table class="detail-table">
        <thead><tr><th>类别</th><th>日均收运量 (吨)</th><th>统计天数</th></tr></thead>
        <tbody id="weekday-pattern-body"></tbody>
      </table>
    </div>
  </div>

  <!-- 车辆排名 -->
  <div class="dual-table">
    <div class="table-card">
      <h3>🏆 运力TOP10 · 高效车辆</h3>
      <table class="detail-table">
        <thead><tr><th>#</th><th>车牌号</th><th>月总量 (kg)</th><th>车次</th><th>车均 (kg)</th><th>区域</th></tr></thead>
        <tbody id="top10-body"></tbody>
      </table>
    </div>
    <div class="table-card">
      <h3>⚠️ 运力后10名 · 需关注车辆</h3>
      <table class="detail-table">
        <thead><tr><th>#</th><th>车牌号</th><th>月总量 (kg)</th><th>车次</th><th>车均 (kg)</th><th>区域</th></tr></thead>
        <tbody id="bottom10-body"></tbody>
      </table>
    </div>
  </div>

</div>

<footer class="site-footer">
  <p>&copy; 2026 湖南伏泰环境科技有限责任公司 · 数据自动同步 · 每月1日自动刷新</p>
</footer>

<script>
// ============================================================
// Data (embedded from Python)
// ============================================================
const MONTHLY_DATA = {report_json};

// ============================================================
// Utilities
// ============================================================
function fmtNum(n, d) {{
  if (n === null || n === undefined) return '-';
  d = d || 0;
  return Number(n).toLocaleString('zh-CN', {{ maximumFractionDigits: d }});
}}
function fmtTon(kg, d) {{ return (kg / 1000).toFixed(d || 1); }}
function fmtPct(n) {{ return (n !== null && n !== undefined) ? n.toFixed(1) + '%' : '-'; }}

const CHART_COLORS = {region_colors};
const CHART_BG = CHART_COLORS.map(c => c.replace(')', ',0.7)').replace('rgb', 'rgba'));

// ============================================================
// KPI Rendering
// ============================================================
function renderKPIs() {{
  const d = MONTHLY_DATA;
  const momClass = d.mom_change_pct !== null && d.mom_change_pct > 0 ? 'up' : 'down';
  const momSign = d.mom_change_pct !== null && d.mom_change_pct >= 0 ? '+' : '';

  document.getElementById('kpi-row').innerHTML =
    '<div class="kpi-card">' +
      '<div class="label">月度总收运量</div>' +
      '<div class="value">' + fmtNum(d.total_ton, 1) + '<span class="unit">吨</span></div>' +
      '<div class="sub">' + d.total_trips + ' 车次 · 已覆盖 ' + d.data_days + '/' + d.days_in_month + ' 天</div>' +
    '</div>' +
    '<div class="kpi-card">' +
      '<div class="label">日均收运量</div>' +
      '<div class="value">' + fmtNum(d.avg_daily_ton, 1) + '<span class="unit">吨/日</span></div>' +
      '<div class="sub">日均 ' + d.avg_daily_trips + ' 车次</div>' +
    '</div>' +
    '<div class="kpi-card">' +
      '<div class="label">月内单日峰值</div>' +
      '<div class="value">' + d.peak.ton + '<span class="unit">吨</span></div>' +
      '<div class="sub">' + d.peak.date + ' ' + d.peak.weekday + ' · ' + d.peak.trips + '车次</div>' +
    '</div>' +
    '<div class="kpi-card">' +
      '<div class="label">月内单日谷值</div>' +
      '<div class="value">' + d.valley.ton + '<span class="unit">吨</span></div>' +
      '<div class="sub">' + d.valley.date + ' ' + d.valley.weekday + ' · ' + d.valley.trips + '车次</div>' +
    '</div>';
  
  document.getElementById('kpi-trend-row').innerHTML =
    '<div class="kpi-card">' +
      '<div class="label">上月总量</div>' +
      '<div class="value">' + (d.prev_month_total_ton > 0 ? fmtNum(d.prev_month_total_ton, 1) : '-') + '<span class="unit">吨</span></div>' +
      '<div class="sub">' + (d.prev_month_total_ton > 0 ? '作为环比基准' : '暂无上月数据') + '</div>' +
    '</div>' +
    '<div class="kpi-card">' +
      '<div class="label">环比变化</div>' +
      '<div class="value" style="color:' + (d.mom_change_ton > 0 ? 'var(--accent-green)' : 'var(--accent-red))') + '">' +
        (d.mom_change_ton > 0 ? '+' : '') + d.mom_change_ton + '<span class="unit">吨</span></div>' +
      '<div class="sub ' + momClass + '">' + momSign + (d.mom_change_pct !== null ? d.mom_change_pct : '--') + '%</div>' +
    '</div>' +
    '<div class="kpi-card">' +
      '<div class="label">周均收运量</div>' +
      '<div class="value">' + (d.weekly_breakdown.length > 0 ? (d.total_ton / d.weekly_breakdown.length).toFixed(1) : '-') + '<span class="unit">吨/周</span></div>' +
      '<div class="sub">覆盖 ' + d.weekly_breakdown.length + ' 周</div>' +
    '</div>' +
    '<div class="kpi-card">' +
      '<div class="label">趋势判断</div>' +
      '<div class="value" style="font-size:22px;">&#x2009;' + d.trend_label + '</div>' +
      '<div class="sub">覆盖 ' + (d.vehicle_count >= 0 ? d.vehicle_count : 'N/A') + ' 台车辆</div>' +
    '</div>';
  
  // Pending alert
  if (d.has_pending) {{
    var pendingBadges = d.pending_dates.map(function(dt) {{
      return '<span class="pending-date">' + dt + '</span>';
    }}).join('');
    document.getElementById('pending-alert').style.display = 'flex';
    document.getElementById('pending-alert').className = 'pending-alert';
    document.getElementById('pending-alert').innerHTML =
      '<span class="icon">&#x26A0;</span>' +
      '<div>' +
        '<strong>部分日期数据待上传</strong><br>' +
        '以下 ' + d.pending_count + ' 天数据尚未上传：' + pendingBadges +
        '。数据上传后将自动纳入统计。' +
      '</div>';
  }}
  
  // v3.1: 数据质量警报
  var dq = d.data_quality || {{}};
  if (dq.severity === 'ERROR' || dq.severity === 'WARNING') {{
    var qa = document.getElementById('quality-alert');
    qa.style.display = 'block';
    var severityBg = dq.severity === 'ERROR' ? 'linear-gradient(135deg, #fee2e2, #fecaca)' : 'linear-gradient(135deg, #fef3c7, #fde68a)';
    var severityBorder = dq.severity === 'ERROR' ? '#f87171' : '#fbbf24';
    var severityColor = dq.severity === 'ERROR' ? '#991b1b' : '#92400e';
    var severityIcon = dq.severity === 'ERROR' ? '&#x274C;' : '&#x26A0;';
    
    var qualityHtml = '<div style="background:' + severityBg + ';border:1px solid ' + severityBorder + ';border-radius:14px;padding:14px 20px;margin-bottom:20px;font-size:13px;color:' + severityColor + ';">' +
      '<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">' +
        '<span style="font-size:20px;">' + severityIcon + '</span>' +
        '<strong>数据质量评分: ' + dq.quality_score + '/100</strong>' +
        '<span style="font-size:12px;opacity:0.7;">(' + dq.summary + ')</span>' +
      '</div>';
    
    if (dq.errors && dq.errors.length > 0) {{
      qualityHtml += '<div style="margin-top:8px;padding-left:30px;">';
      dq.errors.forEach(function(e) {{
        qualityHtml += '<div style="margin:4px 0;color:#991b1b;">&#x1F534; [' + e.field + '] ' + e.message + '</div>';
      }});
      qualityHtml += '</div>';
    }}
    if (dq.warnings && dq.warnings.length > 0) {{
      qualityHtml += '<div style="margin-top:8px;padding-left:30px;">';
      dq.warnings.forEach(function(w) {{
        qualityHtml += '<div style="margin:4px 0;color:#92400e;">&#x26A0; [' + w.field + '] ' + w.message + '</div>';
      }});
      qualityHtml += '</div>';
    }}
    qualityHtml += '</div>';
    qa.innerHTML = qualityHtml;
  }}
}}

// ============================================================
// Charts
// ============================================================
function renderCharts() {{
  const d = MONTHLY_DATA;
  
  // 1. Weekly Breakdown Bar Chart
  (function() {{
    const ctx = document.getElementById('chart-weekly-breakdown');
    if (!ctx) return;
    const wb = d.weekly_breakdown;
    new Chart(ctx, {{
      type: 'bar',
      data: {{
        labels: wb.map(w => '第' + w.week + '周'),
        datasets: [{{
          label: '周收运量 (吨)',
          data: wb.map(w => w.total_ton),
          backgroundColor: wb.map(w => w.trend_color || '#4C72B0'),
          borderRadius: 8
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{
            callbacks: {{
              label: function(ctx) {{
                const w = wb[ctx.dataIndex];
                return '总量: ' + w.total_ton + '吨 · 日均: ' + w.avg_daily + '吨 · ' + w.total_trips + '车次';
              }}
            }}
          }}
        }},
        scales: {{
          y: {{ beginAtZero: false, title: {{ display: true, text: '吨' }} }}
        }}
      }}
    }});
  }})();

  // 2. Daily Trend Line Chart
  (function() {{
    const ctx = document.getElementById('chart-daily-trend');
    if (!ctx) return;
    const daily = d.daily;
    const peakIdx = daily.findIndex(x => x.total_kg === d.peak.kg && !x.pending);
    const valleyIdx = daily.findIndex(x => x.total_kg === d.valley.kg && !x.pending);
    
    const defaultRadius = daily.map(function(x) {{ return x.pending ? 2 : 3; }});
    const pointColors = daily.map(function(x, i) {{
      if (x.pending) return '#cbd5e1';
      if (i === peakIdx) return '#e15759';
      if (i === valleyIdx) return '#59a14f';
      return '#4C72B0';
    }});
    const pointRadii = daily.map(function(x, i) {{
      if (x.pending) return 2;
      if (i === peakIdx || i === valleyIdx) return 6;
      return 3;
    }});

    new Chart(ctx, {{
      type: 'line',
      data: {{
        labels: daily.map(x => x.date),
        datasets: [{{
          label: '收运量 (吨)',
          data: daily.map(x => x.total_kg / 1000),
          borderColor: '#4C72B0',
          backgroundColor: 'rgba(76,114,176,0.1)',
          fill: true,
          tension: 0.3,
          pointRadius: pointRadii,
          pointBackgroundColor: pointColors,
          pointBorderColor: pointColors,
          segment: {{
            borderDash: function(ctx) {{
              var idx = ctx.p0DataIndex;
              return daily[idx].pending ? [5, 5] : undefined;
            }}
          }}
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{
          tooltip: {{
            callbacks: {{
              label: function(ctx) {{
                const x = daily[ctx.dataIndex];
                if (x.pending) return x.date + ' · ' + x.weekday + ' · 数据待上传';
                return fmtTon(x.total_kg, 1) + '吨 · ' + x.trips + '车次 · ' + x.weekday;
              }}
            }}
          }}
        }},
        scales: {{
          y: {{ beginAtZero: false, title: {{ display: true, text: '吨' }} }},
          x: {{ ticks: {{ maxRotation: 45 }} }}
        }}
      }}
    }});
  }})();

  // 3. Region Pie Chart
  (function() {{
    const ctx = document.getElementById('chart-region-pie');
    if (!ctx || d.regions.length === 0) return;
    new Chart(ctx, {{
      type: 'doughnut',
      data: {{
        labels: d.regions.map(r => r.name),
        datasets: [{{
          data: d.regions.map(r => r.kg),
          backgroundColor: CHART_COLORS.slice(0, d.regions.length),
          borderWidth: 2,
          borderColor: '#fff'
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{
          legend: {{ position: 'bottom' }},
          tooltip: {{
            callbacks: {{
              label: function(ctx) {{
                const r = d.regions[ctx.dataIndex];
                return r.name + ': ' + fmtTon(r.kg, 1) + '吨 (' + r.pct + '%)';
              }}
            }}
          }}
        }}
      }}
    }});
  }})();

  // 4. Weekday Pattern Bar Chart
  (function() {{
    const ctx = document.getElementById('chart-weekday-pattern');
    if (!ctx) return;
    const wp = d.weekday_pattern;
    const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    const values = days.map(wd => wp[wd] ? wp[wd].avg_ton : 0);
    const colors = days.map(wd => 
      wd === '周六' || wd === '周日' ? '#e15759' : '#4C72B0'
    );
    
    new Chart(ctx, {{
      type: 'bar',
      data: {{
        labels: days,
        datasets: [{{
          label: '日均收运量 (吨)',
          data: values,
          backgroundColor: colors,
          borderRadius: 6
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{
            callbacks: {{
              label: function(ctx) {{
                const wd = days[ctx.dataIndex];
                const p = wp[wd];
                return p ? p.avg_ton + '吨/日 · ' + p.count + '天' : '0吨';
              }}
            }}
          }}
        }},
        scales: {{
          y: {{ beginAtZero: false, title: {{ display: true, text: '吨/日' }} }}
        }}
      }}
    }});
  }})();
}}

// ============================================================
// Tables
// ============================================================
function renderTables() {{
  const d = MONTHLY_DATA;
  
  // Weekly Detail
  document.getElementById('weekly-detail-body').innerHTML = d.weekly_breakdown.map(function(w) {{
    return '<tr>' +
      '<td><strong>第' + w.week + '周</strong></td>' +
      '<td>' + w.date_range + '</td>' +
      '<td><strong>' + fmtNum(w.total_ton, 1) + '</strong></td>' +
      '<td>' + w.avg_daily + '</td>' +
      '<td>' + w.total_trips + '</td>' +
      '<td style="color:' + w.trend_color + '">' + w.trend_label + '</td>' +
    '</tr>';
  }}).join('');

  // Regions
  document.getElementById('region-table-body').innerHTML = d.regions.map(function(r, i) {{
    const color = CHART_COLORS[i % CHART_COLORS.length];
    return '<tr>' +
      '<td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:' + color + ';margin-right:8px;"></span>' + r.name + '</td>' +
      '<td><strong>' + fmtTon(r.kg, 1) + '</strong></td>' +
      '<td>' + r.pct + '%</td>' +
      '<td>' + r.trips + '</td>' +
      '<td>' + fmtNum(r.avg_per_trip) + '</td>' +
    '</tr>';
  }}).join('');

  // Weekday Pattern
  const wp = d.weekday_pattern;
  document.getElementById('weekday-pattern-body').innerHTML = [
    ['工作日 (周一~周五)', wp.workday_avg_ton || '-', wp.workday_avg_ton ? '~' + (wp.workday_avg_ton > 0 ? Math.round(d.data_days * 5/7) : 0) + ' 天' : '-'],
    ['周末 (周六~周日)', wp.weekend_avg_ton || '-', wp.weekend_avg_ton ? '~' + (wp.weekend_avg_ton > 0 ? Math.round(d.data_days * 2/7) : 0) + ' 天' : '-'],
    ['周末较工作日下降', wp.weekend_drop_pct > 0 ? wp.weekend_drop_pct + '%' : '-', '']
  ].map(function(row) {{
    return '<tr>' +
      '<td><strong>' + row[0] + '</strong></td>' +
      '<td><strong>' + row[1] + ' 吨/日</strong></td>' +
      '<td style="color:var(--text-secondary);">' + row[2] + '</td>' +
    '</tr>';
  }}).join('');

  // Top 10 Vehicles
  document.getElementById('top10-body').innerHTML = d.vehicles_top10.map(function(v, i) {{
    return '<tr>' +
      '<td><strong>' + (i + 1) + '</strong></td>' +
      '<td><strong>' + v.plate + '</strong></td>' +
      '<td>' + fmtNum(v.kg) + '</td>' +
      '<td>' + v.trips + '</td>' +
      '<td>' + fmtNum(v.avg_per_trip) + '</td>' +
      '<td style="font-size:12px;color:var(--text-secondary);">' + (v.unit || '') + '</td>' +
    '</tr>';
  }}).join('');

  // Bottom 10 Vehicles
  document.getElementById('bottom10-body').innerHTML = d.vehicles_bottom10.map(function(v, i) {{
    return '<tr>' +
      '<td style="color:#991b1b;font-weight:700;">' + (d.vehicles_bottom10.length - i) + '</td>' +
      '<td><strong>' + v.plate + '</strong></td>' +
      '<td>' + fmtNum(v.kg) + '</td>' +
      '<td>' + v.trips + '</td>' +
      '<td>' + fmtNum(v.avg_per_trip) + '</td>' +
      '<td style="font-size:12px;color:var(--text-secondary);">' + (v.unit || '') + '</td>' +
    '</tr>';
  }}).join('');

  // Add peak/valley highlight to daily trend data
  var peakDay = null, valleyDay = null;
  for (var i = 0; i < d.daily.length; i++) {{
    if (d.daily[i].total_kg === d.peak.kg) peakDay = d.daily[i];
    if (d.daily[i].total_kg === d.valley.kg) valleyDay = d.daily[i];
  }}
}}

// ============================================================
// Init
// ============================================================
document.addEventListener('DOMContentLoaded', function() {{
  renderKPIs();
  renderCharts();
  renderTables();
}});
</script>
</body>
</html>'''
    
    return html


def main():
    parser = argparse.ArgumentParser(description="花果畈厨余垃圾收运量月度数据分析构建器")
    parser.add_argument("--month", type=str, help="目标月份 YYYY-MM（默认上月）")
    parser.add_argument("--weekly-dir", type=str, help="周数据目录路径")
    parser.add_argument("--output-dir", type=str, help="输出目录路径")
    parser.add_argument("--source", type=str, default="kdocs", choices=["local", "kdocs"], help="数据源: local/kdocs（默认kdocs）")
    parser.add_argument("--json-only", action="store_true", help="仅生成 JSON，不生成 HTML")
    parser.add_argument("--deploy", action="store_true", help="生成后自动部署到 GitHub Pages")
    args = parser.parse_args()
    
    year, month = get_target_month(args)
    weekly_dir = args.weekly_dir or DEFAULT_WEEKLY_DIR
    output_dir = args.output_dir or DEFAULT_OUTPUT_DIR
    
    print(f"[INFO] 目标月份: {year}年{month}月")
    print(f"[INFO] 数据源: {args.source}")
    if args.source == "local":
        print(f"[INFO] 周数据目录: {weekly_dir}")
    print(f"[INFO] 输出目录: {output_dir}")
    
    # 构建报告
    report = build_monthly_report(weekly_dir, year, month, source=args.source)
    if not report:
        print("[ERROR] 无法生成月度分析报告")
        sys.exit(1)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 写入 JSON
    json_path = os.path.join(output_dir, "data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON 已保存: {json_path} ({os.path.getsize(json_path)} bytes)")
    
    # v3.1: 同时保存月度归档（用于后续月环比计算）
    archive_dir = os.path.join(output_dir, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    archive_path = os.path.join(archive_dir, f"{year}-{month:02d}.json")
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[OK] 归档已保存: {archive_path}")
    
    if not args.json_only:
        # 生成 HTML
        html_content = generate_html(report)
        html_path = os.path.join(output_dir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[OK] HTML 已保存: {html_path} ({os.path.getsize(html_path)} bytes)")
    
    # 部署
    if args.deploy:
        deploy_script = os.path.join(weekly_dir, "..", ".scripts", "deploy.sh")
        if os.path.isfile(deploy_script):
            os.system(f'bash "{deploy_script}" --message "monthly: {year}年{month}月 月度分析刷新"')
        else:
            print("[WARN] 未找到部署脚本，跳过自动部署")
    
    # 打印摘要
    print()
    print("=" * 50)
    print(f"  {year}年{month}月 月度分析摘要 (v3.2)")
    print(f"  数据源:     {args.source.upper()}")
    print(f"  数据质量:   {report.get('data_quality', {}).get('quality_score', '--')}/100"
          f" ({report.get('data_quality', {}).get('severity', 'N/A')})")
    print("=" * 50)
    print(f"  月总收运量: {report['total_ton']} 吨")
    print(f"  日均收运量: {report['avg_daily_ton']} 吨/日 (有效天)")
    print(f"  总车次:     {report['total_trips']}")
    print(f"  数据天数:   {report['data_days']} / {report['days_in_month']} 天", end="")
    if report.get("has_pending"):
        print(f"（{report['pending_count']} 天待上传）")
    else:
        print()
    print(f"  有效天数:   {len([d for d in report['daily'] if not d.get('pending')])} 天 (排除pending)")
    print(f"  覆盖周数:   {len(report['weekly_breakdown'])}")
    print(f"  区域数:     {len(report['regions'])}")
    vc = report.get('vehicle_count', 0)
    print(f"  车辆数:     {'N/A（无车辆排名数据）' if vc < 0 else vc}")
    if report['mom_change_pct'] is not None:
        print(f"  环比变化:   {'+' if report['mom_change_ton'] >= 0 else ''}{report['mom_change_ton']}吨 ({report['mom_change_pct']}%)")
    if report.get("has_pending"):
        print(f"  待上传:     {', '.join(report['pending_dates'])}")
    print("=" * 50)
    
    external_url = f"https://2810300-bot.github.io/hnft/monthly-analysis/"
    print(f"  外部地址:   {external_url}")
    
    return report


if __name__ == "__main__":
    main()
