#!/usr/bin/env python3
"""
湖南伏泰合同管理系统 - 自动化引擎 v1.0
核心功能：
1. IMA知识库变更检测（新增/修改/删除条目对比）
2. 合同数据自动同步（更新data.js）
3. 到期预警扫描（7天/30天/90天三级）
4. 钉钉消息推送（关键事项提醒）
5. 执行日志记录与状态监控
"""

import json
import os
import sys
import hashlib
import datetime
import subprocess
import re
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ============================================================
# 配置
# ============================================================
PROJECT_DIR = Path(__file__).parent.parent
SYSTEM_DIR = PROJECT_DIR / "contract-system"
DATA_JS_PATH = SYSTEM_DIR / "data.js"
SNAPSHOT_DIR = SYSTEM_DIR / ".automation"
SNAPSHOT_FILE = SNAPSHOT_DIR / "last_snapshot.json"
LOG_FILE = SNAPSHOT_DIR / "execution_log.json"
STATUS_FILE = SNAPSHOT_DIR / "task_status.json"

IMA_BASE_URL = "https://ima.qq.com/openapi/wiki/v1"
IMA_KB_ID = "rpjY-P_h9OTpvV05usKihwJFx1ini69GhCxY-83pEvo="
IMA_KB_NAME = "岳阳餐厨垃圾项目"
IMA_CONTRACT_FOLDER_ID = "folder_7474652100181775"

# 预警阈值（天数）
WARNING_LEVELS = {"urgent": 7, "caution": 30, "notice": 90}

# 钉钉推送配置
DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "")
DINGTALK_KEYWORD = "合同管理"

# ============================================================
# IMA API 工具
# ============================================================
def _get_ima_credentials():
    """读取IMA凭证，处理UTF-8 BOM"""
    client_id_path = Path("~/.config/ima/client_id").expanduser()
    api_key_path = Path("~/.config/ima/api_key").expanduser()
    
    client_id = client_id_path.read_text("utf-8-sig").strip()
    api_key = api_key_path.read_text("utf-8-sig").strip()
    return client_id, api_key

def _ima_api_request(endpoint, data):
    """通用IMA API请求（通过ima_api.cjs调用，更可靠）"""
    client_id, api_key = _get_ima_credentials()
    ima_api_path = Path("/Users/mac/.workbuddy/skills/ima-skill/ima_api.cjs")
    
    if not ima_api_path.exists():
        return {"error": "ima_api.cjs 不存在"}
    
    # 确保 endpoint 为完整 apiPath
    if not endpoint.startswith("openapi/"):
        api_path = f"openapi/wiki/v1/{endpoint}"
    else:
        api_path = endpoint
    
    opts = json.dumps({"clientId": client_id, "apiKey": api_key}, ensure_ascii=False)
    body = json.dumps(data, ensure_ascii=False)
    
    try:
        result = subprocess.run(
            ["/Users/mac/.workbuddy/binaries/node/versions/22.22.2/bin/node", str(ima_api_path), api_path, body, opts],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode != 0:
            err_text = result.stderr.strip() or result.stdout.strip()
            try:
                err_json = json.loads(err_text)
                return {"error": err_json.get("msg", err_text)}
            except json.JSONDecodeError:
                return {"error": err_text or "ima_api 调用失败"}
        
        resp = json.loads(result.stdout)
        if resp.get("code") != 0:
            return {"error": resp.get("msg", "未知错误")}
        return resp.get("data", {})
    except subprocess.TimeoutExpired:
        return {"error": "IMA API 请求超时"}
    except Exception as e:
        return {"error": str(e)}

def scan_knowledge_base(folder_id=None, limit=50):
    """扫描IMA知识库指定文件夹，获取所有条目列表"""
    all_items = []
    cursor = ""
    
    while True:
        data = {
            "knowledge_base_id": IMA_KB_ID,
            "cursor": cursor,
            "limit": limit
        }
        if folder_id:
            data["folder_id"] = folder_id
        
        result = _ima_api_request("get_knowledge_list", data)
        if "error" in result:
            return {"error": result["error"], "items": all_items}
        
        items = result.get("knowledge_list", [])
        folders = result.get("folder_infos", result.get("folders", []))
        
        for item in items:
            all_items.append({
                "media_id": item.get("media_id", ""),
                "title": item.get("title", ""),
                "parent_folder_id": item.get("parent_folder_id", ""),
                "type": "file"
            })
        
        for folder in folders:
            all_items.append({
                "folder_id": folder.get("folder_id", ""),
                "name": folder.get("name", ""),
                "file_number": folder.get("file_number", 0),
                "parent_folder_id": folder.get("parent_folder_id", ""),
                "type": "folder"
            })
        
        if result.get("is_end", True):
            break
        cursor = result.get("next_cursor", "")
        if not cursor:
            break
    
    return {"items": all_items}

def search_contract_content(query="合同", limit=50):
    """在知识库中搜索合同相关内容"""
    all_results = []
    cursor = ""
    
    while True:
        data = {
            "knowledge_base_id": IMA_KB_ID,
            "query": query,
            "cursor": cursor
        }
        result = _ima_api_request("search_knowledge", data)
        if "error" in result:
            return {"error": result["error"], "results": all_results}
        
        for item in result.get("info_list", []):
            all_results.append({
                "media_id": item.get("media_id", ""),
                "title": item.get("title", ""),
                "parent_folder_id": item.get("parent_folder_id", ""),
                "highlight_content": item.get("highlight_content", "")
            })
        
        if result.get("is_end", True):
            break
        cursor = result.get("next_cursor", "")
        if not cursor:
            break
    
    return {"results": all_results}

# ============================================================
# 变更检测模块
# ============================================================
def compute_hash(item):
    """计算条目指纹，用于变更检测"""
    key_fields = [item.get("title", ""), item.get("media_id", ""), 
                  item.get("parent_folder_id", ""), item.get("name", ""),
                  str(item.get("file_number", ""))]
    return hashlib.md5("|".join(key_fields).encode()).hexdigest()

def detect_changes(current_items, previous_items):
    """对比前后两次扫描结果，识别新增/修改/删除"""
    current_hashes = {}
    for item in current_items:
        h = compute_hash(item)
        current_hashes[h] = item
    
    previous_hashes = {}
    for item in previous_items:
        h = compute_hash(item)
        previous_hashes[h] = item
    
    # 新增：当前存在但之前不存在
    added = [current_hashes[h] for h in current_hashes if h not in previous_hashes]
    
    # 删除：之前存在但当前不存在
    deleted = [previous_hashes[h] for h in previous_hashes if h not in current_hashes]
    
    # 修改：哈希相同但某些字段变化（通过title/media_id匹配）
    modified = []
    current_by_id = {item.get("media_id", item.get("folder_id", "")): item for item in current_items}
    previous_by_id = {item.get("media_id", item.get("folder_id", "")): item for item in previous_items}
    
    for id_key in current_by_id:
        if id_key in previous_by_id and compute_hash(current_by_id[id_key]) != compute_hash(previous_by_id[id_key]):
            modified.append({
                "current": current_by_id[id_key],
                "previous": previous_by_id[id_key]
            })
    
    return {
        "added": added,
        "deleted": deleted,
        "modified": modified,
        "total_current": len(current_items),
        "total_previous": len(previous_items)
    }

# ============================================================
# 到期预警扫描
# ============================================================
def scan_expiry_warnings(contracts_data):
    """扫描合同到期情况，生成分级预警"""
    now = datetime.datetime.now()
    warnings = []
    
    for c in contracts_data:
        status = c.get("status", "")
        end_date_str = c.get("endDate", "")
        
        # 排除已完成/已归档的合同
        if status in ["已归档", "履行完毕"]:
            continue
        if "后续已续签" in status:
            continue
        if not end_date_str or any(k in end_date_str for k in ["待", "长期", "贰年", "约", "收到", "款到", "货期", "付", "天", "左右"]):
            continue
        
        try:
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            continue
        
        days_left = (end_date - now).days
        # 保留90天内到期或已过期（但不超过90天前）的合同
        if days_left > 90 or days_left < -90:
            continue
        
        # 已过期/待续签 强制标记为紧急
        if days_left < 0 or status in ["待续签", "已到期"]:
            level = "urgent"
            action = "已过期，需立即续签" if days_left < 0 else "需续签"
        elif days_left <= 7:
            level = "urgent"
            action = "紧急处理"
        elif days_left <= 30:
            level = "caution"
            action = "需续签"
        else:
            level = "notice"
            action = "关注"
        
        warnings.append({
            "id": c.get("id", ""),
            "name": c.get("name", ""),
            "party": c.get("party", ""),
            "endDate": end_date_str,
            "daysLeft": days_left,
            "level": level,
            "action": action,
            "amount": c.get("amount", 0),
            "status": status
        })
    
    warnings.sort(key=lambda x: x["daysLeft"])
    return warnings

# ============================================================
# 数据同步模块
# ============================================================
def update_data_js(contracts_data, changes, warnings, scan_time):
    """将检测结果写入data.js，更新前端展示数据"""
    
    # 读取现有data.js
    existing_content = DATA_JS_PATH.read_text("utf-8") if DATA_JS_PATH.exists() else ""
    
    # 生成自动化运行信息
    automation_info = {
        "lastScanTime": scan_time,
        "scanResult": {
            "addedCount": len(changes["added"]),
            "deletedCount": len(changes["deleted"]),
            "modifiedCount": len(changes["modified"]),
            "totalItems": changes["total_current"]
        },
        "warningSummary": {
            "urgent": len([w for w in warnings if w["level"] == "urgent"]),
            "caution": len([w for w in warnings if w["level"] == "caution"]),
            "notice": len([w for w in warnings if w["level"] == "notice"]),
            "totalWarnings": len(warnings)
        }
    }
    
    # 在data.js中追加自动化运行信息
    auto_info_js = f"""
// ========== 自动化运行信息（由引擎自动更新）==========
const automationRunInfo = {json.dumps(automation_info, ensure_ascii=False, indent=2)};
const lastScanWarnings = {json.dumps(warnings[:20], ensure_ascii=False, indent=2)}; // 最多保留20条预警
const knowledgeBaseChanges = {json.dumps(changes, ensure_ascii=False, indent=2)};
"""
    
    # 查找是否已有自动化信息区块，如果有则替换
    # 使用更宽泛的正则匹配，兼容 "// ========== " 和 "/* ===== " 两种注释格式
    # 同时匹配所有旧版本区块（可能有多个重复），统一替换为单个新区块
    pattern = r"(// ========== 自动化运行信息.*?const knowledgeBaseChanges\s*=\s*\{.*?\};)"
    
    if re.search(pattern, existing_content, re.DOTALL):
        # 替换最后一个匹配（最新的），删除之前所有重复区块
        # 先删除所有匹配区块，再在末尾追加新区块
        new_content = re.sub(pattern, "", existing_content, flags=re.DOTALL).rstrip()
        new_content = new_content + "\n" + auto_info_js
    else:
        # 在文件末尾追加
        new_content = existing_content.rstrip() + "\n" + auto_info_js
    
    DATA_JS_PATH.write_text(new_content, "utf-8")
    return True

# ============================================================
# 钉钉推送模块
# ============================================================
def push_dingtalk_message(title, content, is_markdown=True):
    """通过钉钉Webhook推送消息"""
    if not DINGTALK_WEBHOOK:
        return {"status": "skipped", "reason": "未配置钉钉Webhook"}
    
    msg_type = "markdown" if is_markdown else "text"
    data = {
        "msgtype": msg_type,
        msg_type: {
            "title": title,
            "text": content if is_markdown else content
        }
    }
    
    if is_markdown:
        data["markdown"]["text"] = content
    
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    
    req = Request(DINGTALK_WEBHOOK, data=body, headers=headers, method="POST")
    
    try:
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return {"status": "success" if result.get("errcode") == 0 else "failed", 
                    "response": result}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def generate_dingtalk_report(changes, warnings, scan_time):
    """生成钉钉推送的Markdown格式报告"""
    lines = [
        f"# 📋 伏泰合同管理自动化报告",
        f"",
        f"**扫描时间**: {scan_time}",
        f"**知识库**: {IMA_KB_NAME}",
        f"",
        f"## 🔍 知识库变更检测",
        f"",
        f"- **新增条目**: {len(changes['added'])}个",
        f"- **删除条目**: {len(changes['deleted'])}个",
        f"- **修改条目**: {len(changes['modified'])}个",
        f"- **当前总条目**: {changes['total_current']}个",
    ]
    
    # 列出新增条目
    if changes["added"]:
        lines.append("")
        lines.append("**新增内容**:")
        for item in changes["added"][:10]:
            title = item.get("title", item.get("name", "未知"))
            lines.append(f"  - {title}")
    
    # 列出删除条目
    if changes["deleted"]:
        lines.append("")
        lines.append("**删除内容**:")
        for item in changes["deleted"][:10]:
            title = item.get("title", item.get("name", "未知"))
            lines.append(f"  - {title}")
    
    # 到期预警
    lines.append("")
    lines.append("## ⚠️ 合同到期预警")
    lines.append("")
    
    urgent = [w for w in warnings if w["level"] == "urgent"]
    caution = [w for w in warnings if w["level"] == "caution"]
    
    if urgent:
        lines.append(f"**🔴 7天内到期 ({len(urgent)}份)**:")
        for w in urgent:
            lines.append(f"  - {w['name']} | 到期: {w['endDate']} | {w['daysLeft']}天 | 操作: {w['action']}")
    
    if caution:
        lines.append(f"**🟡 30天内到期 ({len(caution)}份)**:")
        for w in caution[:5]:
            lines.append(f"  - {w['name']} | 到期: {w['endDate']} | {w['daysLeft']}天")
    
    notice_count = len([w for w in warnings if w["level"] == "notice"])
    if notice_count:
        lines.append(f"**🟢 90天内到期 ({notice_count}份)** — 详情请查看合同管理系统")
    
    if not warnings:
        lines.append("当前无到期预警 ✅")
    
    lines.append("")
    lines.append("---")
    lines.append("> 本报告由伏泰合同管理自动化引擎自动生成")
    
    return "\n".join(lines)

# ============================================================
# 日志与状态管理
# ============================================================
def ensure_dirs():
    """确保自动化目录存在"""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

def save_snapshot(items):
    """保存当前扫描快照"""
    ensure_dirs()
    data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "items": items
    }
    SNAPSHOT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

def load_snapshot():
    """加载上次扫描快照"""
    ensure_dirs()
    if not SNAPSHOT_FILE.exists():
        return []
    data = json.loads(SNAPSHOT_FILE.read_text("utf-8"))
    return data.get("items", [])

def append_execution_log(entry):
    """追加执行日志"""
    ensure_dirs()
    logs = []
    if LOG_FILE.exists():
        try:
            logs = json.loads(LOG_FILE.read_text("utf-8"))
        except json.JSONDecodeError:
            logs = []
    
    logs.append(entry)
    # 保留最近50条日志
    if len(logs) > 50:
        logs = logs[-50:]
    
    LOG_FILE.write_text(json.dumps(logs, ensure_ascii=False, indent=2), "utf-8")

def update_task_status(status_data):
    """更新任务状态"""
    ensure_dirs()
    STATUS_FILE.write_text(json.dumps(status_data, ensure_ascii=False, indent=2), "utf-8")

# ============================================================
# 主执行流程
# ============================================================
def load_current_contracts():
    """从data.js加载当前合同数据"""
    if not DATA_JS_PATH.exists():
        return []
    
    content = DATA_JS_PATH.read_text("utf-8")
    # 提取contracts数组
    match = re.search(r"const contracts = \[(.*?)\];", content, re.DOTALL)
    if not match:
        return []
    
    # 简化提取：将JS对象字符串转为可解析的JSON
    js_array_str = match.group(1)
    
    # 使用Node.js解析JS对象（比纯Python更可靠）
    node_path = "/Users/mac/.workbuddy/binaries/node/versions/22.22.2/bin/node"
    script = f"""
const data = [{js_array_str}];
console.log(JSON.stringify(data));
"""
    
    try:
        result = subprocess.run(
            [node_path, "-e", script],
            capture_output=True, text=True, timeout=10,
            cwd=str(SYSTEM_DIR)
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    
    return []

def run_automation_engine():
    """执行完整的自动化流程"""
    start_time = datetime.datetime.now()
    scan_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"[{scan_time}] 伏泰合同管理自动化引擎启动")
    
    # ===== Step 1: IMA知识库扫描 =====
    print("Step 1: 扫描IMA知识库...")
    
    # 扫描合同管理根目录
    scan_result = scan_knowledge_base(IMA_CONTRACT_FOLDER_ID, 50)
    
    # 扫描各子文件夹
    subfolder_ids = [
        "folder_7474665815554652",  # 设备采购合同
        "folder_7474665815552733",  # 药剂物料采购合同
        "folder_7474665819758743",  # 服务维保合同
        "folder_7474665819759241",  # 工程技改合同
        "folder_7474665828136489",  # 租赁合同
        "folder_7474665828150377",  # 信息系统平台合同
        "folder_7474665823953259",  # 处置运输协议
        "folder_7474665832342135",  # 补充协议
    ]
    
    all_current_items = []
    if "error" not in scan_result:
        all_current_items.extend(scan_result["items"])
    
    for fid in subfolder_ids:
        sub_result = scan_knowledge_base(fid, 50)
        if "error" not in sub_result:
            all_current_items.extend(sub_result["items"])
    
    # 搜索合同关键词获取更多条目
    search_result = search_contract_content("合同", 50)
    if "error" not in search_result:
        for item in search_result["results"]:
            if not any(i.get("media_id") == item.get("media_id") for i in all_current_items):
                all_current_items.append(item)
    
    scan_error = None
    if "error" in scan_result:
        scan_error = scan_result["error"]
    
    print(f"  扫描完成: {len(all_current_items)}个条目")
    
    # ===== Step 2: 变更检测 =====
    print("Step 2: 变更检测...")
    previous_items = load_snapshot()
    changes = detect_changes(all_current_items, previous_items)
    
    print(f"  新增: {len(changes['added'])} | 修改: {len(changes['modified'])} | 删除: {len(changes['deleted'])}")
    
    # 保存当前快照
    save_snapshot(all_current_items)
    
    # ===== Step 3: 加载合同数据 & 到期预警 =====
    print("Step 3: 到期预警扫描...")
    contracts_data = load_current_contracts()
    warnings = scan_expiry_warnings(contracts_data)
    
    urgent_count = len([w for w in warnings if w["level"] == "urgent"])
    caution_count = len([w for w in warnings if w["level"] == "caution"])
    notice_count = len([w for w in warnings if w["level"] == "notice"])
    
    print(f"  预警: 紧急{urgent_count} | 注意{caution_count} | 关注{notice_count}")
    
    # ===== Step 4: 数据同步更新 =====
    print("Step 4: 更新data.js...")
    sync_success = False
    try:
        sync_success = update_data_js(contracts_data, changes, warnings, scan_time)
        print(f"  数据同步: {'成功' if sync_success else '失败'}")
    except Exception as e:
        print(f"  数据同步失败: {e}")
    
    # ===== Step 5: 钉钉推送 =====
    print("Step 5: 钉钉消息推送...")
    
    # 仅在有紧急预警或显著变更时推送
    should_push = urgent_count > 0 or len(changes["added"]) > 0 or len(changes["deleted"]) > 0
    
    push_result = {"status": "skipped"}
    if should_push:
        report = generate_dingtalk_report(changes, warnings, scan_time)
        push_result = push_dingtalk_message(
            "伏泰合同管理自动化报告",
            report
        )
        print(f"  推送结果: {push_result['status']}")
    else:
        print("  无紧急事项，跳过推送")
    
    # ===== Step 6: 记录日志 =====
    print("Step 6: 记录执行日志...")
    
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    log_entry = {
        "runId": start_time.strftime("%Y%m%d%H%M%S"),
        "startTime": start_time.isoformat(),
        "endTime": end_time.isoformat(),
        "durationSeconds": round(duration, 2),
        "status": "success" if not scan_error and sync_success else "partial",
        "scanItemsCount": len(all_current_items),
        "changes": {
            "added": len(changes["added"]),
            "deleted": len(changes["deleted"]),
            "modified": len(changes["modified"])
        },
        "warnings": {
            "urgent": urgent_count,
            "caution": caution_count,
            "notice": notice_count
        },
        "syncResult": "success" if sync_success else "failed",
        "pushResult": push_result["status"],
        "errors": [scan_error] if scan_error else []
    }
    
    append_execution_log(log_entry)
    
    # 更新任务状态
    task_status = {
        "lastRunTime": start_time.isoformat(),
        "nextRunTime": (start_time + datetime.timedelta(weeks=1)).isoformat(),
        "status": "active",
        "totalRuns": len(json.loads(LOG_FILE.read_text("utf-8"))) if LOG_FILE.exists() else 1,
        "lastRunStatus": log_entry["status"],
        "consecutiveSuccesses": 0,  # 计算连续成功次数
        "imaConnection": "connected" if not scan_error else "error"
    }
    
    # 计算连续成功次数
    if LOG_FILE.exists():
        all_logs = json.loads(LOG_FILE.read_text("utf-8"))
        consecutive = 0
        for lg in reversed(all_logs):
            if lg.get("status") == "success":
                consecutive += 1
            else:
                break
        task_status["consecutiveSuccesses"] = consecutive
    
    update_task_status(task_status)
    
    # ===== 输出摘要 =====
    print("\n" + "=" * 50)
    print("伏泰合同管理自动化引擎 — 执行摘要")
    print("=" * 50)
    print(f"扫描时间: {scan_time}")
    print(f"执行耗时: {duration:.2f}秒")
    print(f"知识库条目: {len(all_current_items)}")
    print(f"变更检测: 新增{len(changes['added'])} / 修改{len(changes['modified'])} / 删除{len(changes['deleted'])}")
    print(f"到期预警: 紧急{urgent_count} / 注意{caution_count} / 关注{notice_count}")
    print(f"数据同步: {'成功' if sync_success else '失败'}")
    print(f"消息推送: {push_result['status']}")
    print(f"执行状态: {log_entry['status']}")
    
    # 生成Markdown格式报告并保存
    report_md = generate_automation_report_md(log_entry, changes, warnings, scan_time)
    report_path = SNAPSHOT_DIR / f"report_{start_time.strftime('%Y%m%d')}.md"
    report_path.write_text(report_md, "utf-8")
    print(f"详细报告: {report_path}")
    
    return log_entry

def generate_automation_report_md(log_entry, changes, warnings, scan_time):
    """生成Markdown格式的执行报告"""
    lines = [
        f"# 伏泰合同管理自动化执行报告",
        f"",
        f"| 项目 | 值 |",
        f"|------|------|",
        f"| 执行时间 | {scan_time} |",
        f"| 执行耗时 | {log_entry['durationSeconds']}秒 |",
        f"| 执行状态 | {log_entry['status']} |",
        f"| 知识库条目 | {log_entry['scanItemsCount']} |",
        f"| 数据同步 | {log_entry['syncResult']} |",
        f"| 消息推送 | {log_entry['pushResult']} |",
        f"",
        f"## 变更检测",
        f"",
        f"| 类型 | 数量 |",
        f"|------|------|",
        f"| 新增 | {log_entry['changes']['added']} |",
        f"| 修改 | {log_entry['changes']['modified']} |",
        f"| 删除 | {log_entry['changes']['deleted']} |",
    ]
    
    if changes["added"]:
        lines.append("")
        lines.append("### 新增条目")
        for item in changes["added"][:10]:
            lines.append(f"- {item.get('title', item.get('name', '未知'))}")
    
    if changes["deleted"]:
        lines.append("")
        lines.append("### 删除条目")
        for item in changes["deleted"][:10]:
            lines.append(f"- {item.get('title', item.get('name', '未知'))}")
    
    lines.append("")
    lines.append("## 到期预警")
    lines.append("")
    lines.append(f"| 级别 | 数量 |")
    lines.append(f"|------|------|")
    lines.append(f"| 🔴 紧急(7天内) | {log_entry['warnings']['urgent']} |")
    lines.append(f"| 🟡 注意(30天内) | {log_entry['warnings']['caution']} |")
    lines.append(f"| 🟢 关注(90天内) | {log_entry['warnings']['notice']} |")
    
    if warnings:
        lines.append("")
        lines.append("### 预警详情")
        for w in warnings[:15]:
            icon = "🔴" if w["level"] == "urgent" else "🟡" if w["level"] == "caution" else "🟢"
            lines.append(f"- {icon} **{w['name']}** | {w['party']} | {w['daysLeft']}天 | {w['endDate']} | 操作: {w['action']}")
    
    if log_entry.get("errors"):
        lines.append("")
        lines.append("## 错误信息")
        for err in log_entry["errors"]:
            lines.append(f"- {err}")
    
    return "\n".join(lines)

# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    try:
        result = run_automation_engine()
        sys.exit(0 if result["status"] == "success" else 1)
    except Exception as e:
        print(f"自动化引擎异常: {e}")
        
        # 记录异常日志
        ensure_dirs()
        error_entry = {
            "runId": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            "startTime": datetime.datetime.now().isoformat(),
            "status": "error",
            "errors": [str(e)]
        }
        append_execution_log(error_entry)
        sys.exit(2)
