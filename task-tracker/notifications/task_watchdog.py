#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务变更检测与通知分发器
================================
在每次 task_data.json 同步后运行，逐任务对比 baseline，识别任务状态变化，
按 notification_config.json 的角色权限矩阵解析接收人，调用钉钉推送通道发送通知。

特性：
  · 五大触发事件：分配 / 状态变更 / 截止临近 / 逾期 / 完成
  · 角色权限矩阵：责任人(@) / 主管 / 总经理，避免冗余与遗漏
  · 防重复：baseline 比对 + 临近提醒去重状态；仅通知「本周期新变化」
  · 安全降级：通知失败仅记日志，不阻断主同步
  · 支持 --dry-run 预览、--init 仅初始化基线

用法：
  python3 task_watchdog.py \
      --current task-tracker/task_data.json \
      --baseline task-tracker/task_data.baseline.json \
      --config task-tracker/notifications/notification_config.json

  python3 task_watchdog.py --current ... --baseline ... --config ... --dry-run
"""
import os
import sys
import json
import argparse
import datetime

# 允许直接运行（同目录导入 notifier）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dingtalk_notifier import DingTalkNotifier  # noqa: E402

# ---------------------------------------------------------------------- #
# 时间解析（与前端保持一致）
# ---------------------------------------------------------------------- #
def parse_deadline(d):
    if not d:
        return None
    import re
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", d)
    if m:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", d)
    if m:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def fmt_date(d):
    dt = parse_deadline(d)
    return f"{dt.month}月{dt.day}日" if dt else (d or "长期")


def status_label(status):
    return {
        "completed": "已完成",
        "in_progress": "进行中",
        "pending": "待启动",
        "overdue": "已逾期",
    }.get(status, status)


def is_overdue(task):
    if task.get("status") == "completed":
        return False
    dt = parse_deadline(task.get("deadline"))
    if not dt:
        return False
    return dt < datetime.date.today()


def days_info(task):
    dt = parse_deadline(task.get("deadline"))
    if not dt:
        return ""
    diff = (dt - datetime.date.today()).days
    if diff < 0:
        return f"已逾期 {abs(diff)} 天"
    if diff == 0:
        return "今天截止"
    if diff == 1:
        return "明天截止"
    return f"剩余 {diff} 天"


# ---------------------------------------------------------------------- #
# 配置加载
# ---------------------------------------------------------------------- #
def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dedupe_tasks(tasks):
    """按 id 去重，保留首次出现。返回 (去重后列表, 重复 id 列表)。

    源数据偶发重复 id（如两个任务共用 t23），若直接用 dict 建索引会
    把不同任务混为一谈，导致错误配对并发送虚假通知。去重可保证 1:1 比对。
    """
    seen = set()
    out = []
    dups = []
    for t in tasks:
        tid = t.get("id")
        if tid in seen:
            dups.append(tid)
            continue
        seen.add(tid)
        out.append(t)
    return out, dups


# ---------------------------------------------------------------------- #
# 事件检测
# ---------------------------------------------------------------------- #
EVENT_PRIORITY = {
    "overdue": 0, "completed": 1, "assigned": 2,
    "deadline_approaching": 3, "status_change": 4,
}
EVENT_TITLE = {
    "assigned": "🆕 新任务分配",
    "status_change": "🔄 任务状态变更",
    "deadline_approaching": "⏰ 任务临近截止",
    "overdue": "🔴 任务已逾期",
    "completed": "✅ 任务已完成",
}


def detect_events(current_tasks, baseline_map, cfg, warn_state):
    """返回 {task_id: set(events)}，并更新 warn_state。"""
    rules = cfg.get("rules", {})
    notify_on = rules.get("notify_on", {})
    warn_days = int(rules.get("deadline_warning_days", 3))
    today = datetime.date.today()

    result = {}
    for t in current_tasks:
        tid = t["id"]
        btask = baseline_map.get(tid)
        events = set()

        # 1) 新任务 / 分配
        if btask is None:
            if notify_on.get("assigned"):
                events.add("assigned")
        else:
            # 2) 状态变更
            if btask.get("status") != t.get("status"):
                ns = t.get("status")
                if ns == "completed" and notify_on.get("completed"):
                    events.add("completed")
                elif ns == "overdue" and notify_on.get("overdue"):
                    events.add("overdue")
                elif notify_on.get("status_change"):
                    events.add("status_change")
            # 3) 逾期（兜底：status 可能未标 overdue 但日期已过的任务）
            if (is_overdue(t) and not is_overdue(btask)
                    and t.get("status") != "completed" and notify_on.get("overdue")):
                events.add("overdue")

        # 4) 截止临近（去重：已提醒过则不再重复）
        if (notify_on.get("deadline_approaching")
                and not is_overdue(t)
                and t.get("status") != "completed"):
            dt = parse_deadline(t.get("deadline"))
            if dt and 0 <= (dt - today).days <= warn_days:
                st = warn_state.get(tid, {})
                if not st.get("approaching"):
                    events.add("deadline_approaching")
                    st["approaching"] = True
                    warn_state[tid] = st
                # 已提醒过：保持标记，不重复通知

        # 完成 / 逾期后清除临近标记，便于将来重新打开时再次提醒
        if "completed" in events or "overdue" in events:
            if tid in warn_state:
                warn_state[tid].pop("approaching", None)

        if events:
            result[tid] = events
    return result


# ---------------------------------------------------------------------- #
# 接收人解析（角色权限矩阵 + @）
# ---------------------------------------------------------------------- #
def resolve_recipients(task, events, cfg):
    """返回 (at_mobiles, informed)。

    · at_mobiles：仅 @ 任务「实际责任人」中配置了手机号且开启通知者，确保精准。
    · informed  ：主管/总经理等角色按矩阵在群内知会（不 @），
                  并通过 supervisor_of 精确追加任务责任人的直属主管。
    """
    roles = cfg.get("roles", {})
    people = cfg.get("people", {})
    sup_map = cfg.get("supervisor_of", {})
    ev_set = set(events)

    at_mobiles = []
    informed = {}  # name -> role_label
    resp_names = task.get("responsible", [])

    # 1) 责任人 @：仅 @ 任务实际责任人（在其接收事件范围内且开启 @）
    resp_role_cfg = roles.get("responsible", {})
    if ev_set & set(resp_role_cfg.get("receive", [])) and resp_role_cfg.get("at_mention"):
        for name in resp_names:
            p = people.get(name)
            if p and p.get("notify", True) and p.get("mobile"):
                at_mobiles.append(p["mobile"])

    # 2) 主管 / 总经理：群内知会（不 @），按角色矩阵收集
    for role_name, role_cfg in roles.items():
        if role_name == "responsible":
            continue
        if not (ev_set & set(role_cfg.get("receive", []))):
            continue
        for name, p in people.items():
            if p.get("role") == role_name and p.get("notify", True):
                informed[name] = role_cfg.get("label", role_name)

    # 3) supervisor_of 精确知会：任务责任人的直属主管（无论主管角色是否全局接收该事件）
    for name in resp_names:
        sup = sup_map.get(name)
        if sup and people.get(sup, {}).get("notify", True):
            sup_role = people[sup].get("role")
            sup_label = roles.get(sup_role, {}).get("label", sup_role)
            informed[sup] = sup_label

    at_mobiles = list(dict.fromkeys(at_mobiles))
    return at_mobiles, informed


# ---------------------------------------------------------------------- #
# 消息构建
# ---------------------------------------------------------------------- #
def build_message(task, events, cfg):
    url = cfg.get("task_tracker_url", "")
    # 主标题取优先级最高的事件
    top = min(events, key=lambda e: EVENT_PRIORITY[e])
    title = EVENT_TITLE[top]

    reasons = "、".join(EVENT_TITLE[e].replace("🆕 ", "").replace("🔄 ", "")
                        .replace("⏰ ", "").replace("🔴 ", "").replace("✅ ", "")
                        for e in sorted(events, key=lambda e: EVENT_PRIORITY[e]))

    lines = [
        f"### {title}",
        f"> **任务**：{task.get('content', '')}",
        f"> **类别**：{task.get('category', '-')}",
        f"> **责任人**：{'、'.join(task.get('responsible', [])) or '-'}",
        f"> **截止**：{fmt_date(task.get('deadline'))}（{days_info(task) or '-'}）",
        f"> **状态**：{status_label(task.get('status'))}",
    ]
    if task.get("notes"):
        lines.append(f"> **备注**：{task['notes']}")
    if task.get("completed_date"):
        lines.append(f"> **完成日期**：{task['completed_date']}")
    lines.append(f"> **触发**：{reasons}")
    if url:
        lines.append(f"\n[点击在任务跟踪系统查看并处理]({url})")
    return title, "\n".join(lines)


# ---------------------------------------------------------------------- #
# 主流程
# ---------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="任务变更钉钉通知分发器")
    ap.add_argument("--current", required=True, help="最新 task_data.json 路径")
    ap.add_argument("--baseline", required=True, help="baseline 快照路径")
    ap.add_argument("--config", required=True, help="notification_config.json 路径")
    ap.add_argument("--dry-run", action="store_true", help="仅预览，不发送、不更新 baseline")
    ap.add_argument("--init", action="store_true", help="仅初始化 baseline 后退出")
    args = ap.parse_args()

    cfg = load_config(args.config)
    with open(args.current, "r", encoding="utf-8") as f:
        current = json.load(f)
    current_tasks_raw = current.get("tasks", [])
    current_tasks, cur_dups = dedupe_tasks(current_tasks_raw)
    if cur_dups:
        print(f"[数据警告] 当前数据存在重复 id（已去重，保留首次出现）：{sorted(set(cur_dups))}",
              file=sys.stderr)
    current_map = {t["id"]: t for t in current_tasks}

    # 载入或初始化 baseline
    if not os.path.exists(args.baseline):
        baseline = current.copy()
        baseline["tasks"] = current_tasks
        baseline["_warn_state"] = {}
        if not args.dry_run:
            with open(args.baseline, "w", encoding="utf-8") as f:
                json.dump(baseline, f, ensure_ascii=False, indent=2)
        print(f"[初始化] 已创建 baseline（{len(current_tasks)} 个任务），本次不发送通知。")
        return

    with open(args.baseline, "r", encoding="utf-8") as f:
        baseline = json.load(f)
    base_tasks, base_dups = dedupe_tasks(baseline.get("tasks", []))
    if base_dups:
        print(f"[数据警告] baseline 存在重复 id（已去重）：{sorted(set(base_dups))}",
              file=sys.stderr)
    baseline_map = {t["id"]: t for t in base_tasks}
    warn_state = baseline.get("_warn_state", {})

    if args.init:
        baseline = current.copy()
        baseline["tasks"] = current_tasks
        baseline["_warn_state"] = warn_state
        if not args.dry_run:
            with open(args.baseline, "w", encoding="utf-8") as f:
                json.dump(baseline, f, ensure_ascii=False, indent=2)
        print("[init] baseline 已更新为最新。")
        return

    # 检测事件
    events_map = detect_events(current_tasks, baseline_map, cfg, warn_state)

    if not events_map:
        print("[无变化] 本周期无任务状态变化，无需通知。")
        # 仍更新 warn_state（临近标记可能变化）
        baseline = current.copy()
        baseline["tasks"] = current_tasks
        baseline["_warn_state"] = warn_state
        if not args.dry_run:
            with open(args.baseline, "w", encoding="utf-8") as f:
                json.dump(baseline, f, ensure_ascii=False, indent=2)
        return

    # 限额保护
    max_n = int(cfg.get("rules", {}).get("max_notify_per_run", 20))
    items = list(events_map.items())
    overflow = max(0, len(items) - max_n)
    items = items[:max_n]

    notifier = DingTalkNotifier(cfg) if not args.dry_run else None
    log = []
    sent = 0
    for tid, events in items:
        task = current_map[tid]
        at_mobiles, informed = resolve_recipients(task, events, cfg)
        title, text = build_message(task, events, cfg)

        informed_line = ""
        if informed:
            informed_line = "\n\n👀 **知会**：" + "、".join(
                f"{n}（{r}）" for n, r in informed.items()
            )
        full_text = text + informed_line

        log_entry = {
            "time": datetime.datetime.now().isoformat(timespec="seconds"),
            "task_id": tid,
            "events": sorted(events, key=lambda e: EVENT_PRIORITY[e]),
            "at": at_mobiles,
            "informed": list(informed.keys()),
        }

        if args.dry_run:
            print("─" * 60)
            print(f"[DRY-RUN] 任务 {tid} 事件={log_entry['events']}")
            print(full_text)
            print(f"  @手机号: {at_mobiles}")
            sent += 1
            log.append({**log_entry, "result": "dry-run"})
            continue

        res = notifier.send_markdown(title, full_text, at_mobiles)
        ok = res.get("errcode") == 0
        log_entry["result"] = res if not ok else "ok"
        log.append(log_entry)
        if ok:
            sent += 1
            print(f"[发送成功] {tid} 事件={log_entry['events']} @={at_mobiles}")
        else:
            print(f"[发送失败] {tid}: {res}", file=sys.stderr)

    # 写日志
    log_path = os.path.join(os.path.dirname(os.path.abspath(args.config)),
                            "notification_log.json")
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        history = []
    history.extend(log)
    history = history[-500:]  # 仅保留最近 500 条
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    # 更新 baseline（写入最新数据 + warn_state）
    baseline = current.copy()
    baseline["tasks"] = current_tasks
    baseline["_warn_state"] = warn_state
    if not args.dry_run:
        with open(args.baseline, "w", encoding="utf-8") as f:
            json.dump(baseline, f, ensure_ascii=False, indent=2)

    print(f"\n[完成] 本次发送 {sent}/{len(items)} 条通知"
          + (f"，超额 {overflow} 条已留待下次（见日志）" if overflow else ""))


if __name__ == "__main__":
    main()
