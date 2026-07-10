#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步后钉钉 ActionCard 通知控制器
================================
作为「工作任务跟踪系统 — IMA知识库同步至数据看板」自动化流程的收尾步骤：

  1. 顺序执行 task_tracker_sync.py（完成 IMA→看板 同步）；
  2. 同步成功：对比运行前后的 task_data.json，识别本次变更，向钉钉群
     「湖南伏泰工作通知群」发送一张**整体跳转 ActionCard**：
       · 标题、任务详情（类别/备注/责任人）
       · 当前执行状态、截止时间及剩余天数
       · 跳转按钮直达任务跟踪看板
  3. 同步失败：发送一张**失败 ActionCard** 兜底通知（含失败阶段/错误摘要/排查建议）。

设计要点：
  · 通知「仅在同步流程执行完毕后」触发（先 sync 后 notify，顺序执行）；
  · 密钥经环境变量 DINGTALK_WEBHOOK / DINGTALK_SECRET 注入，不入库；
  · 通知失败不阻断主流程，仅写本地兜底文件 + 日志；
  · 复用 task_watchdog 的格式化与去重逻辑，保证与看板口径一致；
  · 支持 --dry-run 预览卡片（不发送、不更新基线）。

用法：
  # 正式接入自动化（同步 + 通知）
  python3 sync_notify_controller.py

  # 预览本次将发送的卡片（不发送、不更新基线）
  python3 sync_notify_controller.py --dry-run

  # 自定义路径
  python3 sync_notify_controller.py \
      --sync-script /path/task_tracker_sync.py \
      --data /path/task_data.json \
      --baseline /path/task_data.baseline.json \
      --config /path/notification_config.json
"""
import argparse
import json
import os
import sys
import subprocess
import datetime

# 同目录导入 notifier / watchdog 工具
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from dingtalk_notifier import DingTalkNotifier  # noqa: E402
from task_watchdog import (  # noqa: E402
    parse_deadline, fmt_date, status_label, days_info, dedupe_tasks,
)

# ---------------------------------------------------------------------- #
# 默认路径
# ---------------------------------------------------------------------- #
SCRIPTS_DIR = os.path.expanduser("~/.workbuddy/scripts")
DEFAULT_SYNC = os.path.join(SCRIPTS_DIR, "task_tracker_sync.py")
DEFAULT_PY = "/Users/mac/.workbuddy/binaries/python/envs/default/bin/python"
HNFT_DIR = os.path.expanduser("~/.workbuddy/hnft-site")
DEFAULT_DATA = os.path.join(HNFT_DIR, "task-tracker", "task_data.json")
DEFAULT_BASELINE = os.path.join(HNFT_DIR, "task-tracker", "task_data.baseline.json")
DEFAULT_CONFIG = os.path.join(HERE, "notification_config.json")
ERROR_LOG = os.path.expanduser("~/.workbuddy/logs/task_sync_errors.log")

# 卡片渲染约束（钉钉 actionCard text 上限约 5000 字符，留余量）
MAX_TASKS = 10
TEXT_LIMIT = 4000

STATUS_EMOJI = {
    "completed": "✅",
    "in_progress": "🔄",
    "pending": "⏳",
    "overdue": "⚠️",
}


# ---------------------------------------------------------------------- #
# 基础工具
# ---------------------------------------------------------------------- #
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------- #
# 执行同步脚本
# ---------------------------------------------------------------------- #
def run_sync(py, sync_script, dry_run):
    """运行同步脚本，返回 (returncode, stdout, stderr)。"""
    cmd = [py, sync_script]
    if dry_run:
        cmd.append("--dry-run")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "同步脚本执行超时（>600s）"
    except Exception as e:  # noqa: BLE001
        return 1, "", f"无法启动同步脚本: {e}"


def detect_stage(text):
    """从同步输出推断失败阶段，用于失败卡片展示。"""
    if "凭证" in text:
        return "IMA 凭证加载"
    if "IMA 文件" in text or "get_knowledge_list" in text:
        return "获取 IMA 文件列表"
    if "Excel 解析" in text or "下载 Excel" in text:
        return "Excel 下载/解析"
    if "差异报告" in text:
        return "差异报告生成"
    if "GitHub" in text or "git" in text.lower():
        return "GitHub Pages 部署"
    return "未知阶段"


# ---------------------------------------------------------------------- #
# 变更计算（运行前 / 运行后 对比）
# ---------------------------------------------------------------------- #
def compute_changes(old_tasks, new_tasks):
    """返回变更列表：[{'task':..., 'diffs':set}]，及移除数量。"""
    old_dedup, _ = dedupe_tasks(old_tasks)
    new_dedup, _ = dedupe_tasks(new_tasks)
    old_index = {t["id"]: t for t in old_dedup}

    changes = []
    for t in new_dedup:
        o = old_index.get(t.get("id"))
        if o is None:
            changes.append({"task": t, "diffs": {"new"}})
            continue
        diffs = set()
        if o.get("status") != t.get("status"):
            diffs.add("status")
        if o.get("deadline") != t.get("deadline"):
            diffs.add("deadline")
        if o.get("content", "").strip() != t.get("content", "").strip():
            diffs.add("content")
        if diffs:
            changes.append({"task": t, "diffs": diffs})

    # 移除数量（排除常态化工作，与同步脚本口径一致）
    new_ids = {t.get("id") for t in new_dedup}
    new_keys = {t.get("content", "")[:30].strip() for t in new_dedup}
    removed = 0
    for o in old_dedup:
        if o.get("category") == "常态化工作":
            continue
        if o.get("id") not in new_ids and o.get("content", "")[:30].strip() not in new_keys:
            removed += 1

    return changes, removed


def change_label(ch):
    diffs = ch["diffs"]
    status = ch["task"].get("status")
    if "new" in diffs:
        return "🆕 新任务"
    if "status" in diffs:
        if status == "completed":
            return "✅ 已完成"
        if status == "overdue":
            return "⚠️ 已逾期"
        return "🔄 状态变更"
    if "deadline" in diffs:
        return "📅 截止变更"
    if "content" in diffs:
        return "✏️ 内容变更"
    return "🔔 变更"


# ---------------------------------------------------------------------- #
# 卡片构建
# ---------------------------------------------------------------------- #
def build_success_card(changes, new_data, removed, cfg):
    url = cfg.get("task_tracker_url", "")
    now = now_str()
    source = new_data.get("source_file", "")
    stats = new_data.get("stats", {})
    total = len(new_data.get("tasks", []))
    n = len(changes)

    if n == 0:
        title = "✅ 任务跟踪同步完成（无变更）"
        text = (
            f"# {title}\n"
            f"> **同步时间**：{now}\n"
            f"> **数据源**：IMA 待办事项跟踪 / {source}\n"
            f"> **看板**：已刷新\n\n"
            f"**📊 任务概览**\n"
            f"> 总任务：{total} 项 ｜ 已完成：{stats.get('completed', 0)} ｜ "
            f"进行中：{stats.get('in_progress', 0)} ｜ 逾期：{stats.get('overdue', 0)}\n\n"
            "本次同步未检测到任务变更，数据与看板保持一致。"
        )
        return title, text, url

    title = f"✅ 任务跟踪同步完成（{n} 项变更）"
    lines = [
        f"# {title}",
        f"> **同步时间**：{now}",
        f"> **数据源**：IMA 待办事项跟踪 / {source}",
        f"> **看板**：已刷新",
        "",
        "**📊 任务概览**",
        f"> 总任务：{total} ｜ 已完成：{stats.get('completed', 0)} ｜ "
        f"进行中：{stats.get('in_progress', 0)} ｜ 逾期：{stats.get('overdue', 0)}"
        + (f" ｜ 移除：{removed}" if removed else ""),
        "",
        f"**🔔 本次变更（{n} 项）**",
    ]

    # 按紧急度排序：逾期 > 完成 > 状态 > 截止 > 内容 > 新增
    prio = {"overdue": 0, "completed": 1, "status": 2, "deadline": 3,
            "content": 4, "new": 5}
    changes.sort(key=lambda c: min(prio.get(d, 9) for d in c["diffs"]))

    overflow = max(0, n - MAX_TASKS)
    for i, ch in enumerate(changes[:MAX_TASKS], 1):
        t = ch["task"]
        label = change_label(ch)
        block = [
            f"**{i}. {label} · {t.get('content', '')[:60]}**",
            f"> 类别：{t.get('category', '-')} ｜ 责任人：{'、'.join(t.get('responsible', [])) or '-'}",
            f"> 截止：{fmt_date(t.get('deadline'))}（{days_info(t) or '-'}）｜ "
            f"状态：{STATUS_EMOJI.get(t.get('status'), '')} {status_label(t.get('status'))}",
        ]
        if t.get("notes"):
            block.append(f"> 备注：{t['notes']}")
        snippet = "\n".join(block)
        # 长度保护：超出上限则停止追加并提示
        if len("\n".join(lines)) + len(snippet) + 60 > TEXT_LIMIT:
            overflow += (n - i + 1)
            break
        lines.append(snippet)
        lines.append("")

    if overflow:
        lines.append(f"… 还有 {overflow} 项变更，请在看板查看完整列表。")
    return title, "\n".join(lines), url


def build_failure_card(stage, err_text, cfg):
    url = cfg.get("task_tracker_url", "")
    now = now_str()
    excerpt_lines = (err_text or "未知错误").strip().splitlines()[-8:]
    excerpt_q = "\n".join(f"> {ln}" for ln in excerpt_lines) if excerpt_lines else "> （无详细输出）"
    title = "❌ 任务跟踪同步失败"
    text = (
        f"# {title}\n"
        f"> **失败时间**：{now}\n"
        f"> **失败阶段**：{stage}\n"
        f"> **错误摘要**：\n{excerpt_q}\n\n"
        "**🔧 排查建议**\n"
        "> 1. 检查 IMA 凭证是否过期（~/.config/ima）\n"
        "> 2. 检查网络与 IMA / 钉钉服务可用性\n"
        "> 3. 查看错误日志：~/.workbuddy/logs/task_sync_errors.log\n\n"
        "失败后看板未更新，仍展示上次正常数据。"
    )
    return title, text, url


# ---------------------------------------------------------------------- #
# 发送 + 兜底
# ---------------------------------------------------------------------- #
def send_card(notifier, title, text, url, log_path):
    """发送 actionCard；失败写本地兜底文件。返回 (ok, detail)。"""
    try:
        res = notifier.send_action_card(title, text, url, single_title="📊 查看任务跟踪看板")
    except Exception as e:  # noqa: BLE001
        res = {"errcode": -2, "errmsg": f"发送异常: {e}"}
    ok = res.get("errcode") == 0
    if not ok:
        # 兜底：保存未发送卡片，避免消息丢失
        try:
            fb = {
                "time": datetime.datetime.now().isoformat(timespec="seconds"),
                "title": title,
                "text": text,
                "url": url,
                "error": res,
            }
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(fb, f, ensure_ascii=False, indent=2)
            print(f"[兜底] 通知发送失败，已写入 {log_path}：{res}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"[兜底] 无法写入兜底文件: {e}", file=sys.stderr)
    return ok, res


def write_run_log(log_path, entry):
    try:
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
        history.append(entry)
        history = history[-200:]
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:  # noqa: BLE001
        print(f"[日志] 写入运行日志失败: {e}", file=sys.stderr)


# ---------------------------------------------------------------------- #
# 主流程
# ---------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="同步后钉钉 ActionCard 通知控制器")
    ap.add_argument("--sync-script", default=DEFAULT_SYNC, help="同步脚本路径")
    ap.add_argument("--python", default=DEFAULT_PY, help="Python 解释器路径")
    ap.add_argument("--data", default=DEFAULT_DATA, help="task_data.json 路径")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE, help="基线快照路径")
    ap.add_argument("--config", default=DEFAULT_CONFIG, help="notification_config.json")
    ap.add_argument("--dry-run", action="store_true", help="预览卡片，不发送、不更新基线")
    args = ap.parse_args()

    cfg = load_config(args.config)
    log_path = os.path.join(HERE, "notify_failed.json")
    run_log = os.path.join(HERE, "notification_log.json")

    # —— 载入运行前基线（用于对比本次变更）——
    old_tasks = []
    if os.path.exists(args.baseline):
        with open(args.baseline, "r", encoding="utf-8") as f:
            old_tasks = json.load(f).get("tasks", [])
    elif os.path.exists(args.data):
        with open(args.data, "r", encoding="utf-8") as f:
            old_tasks = json.load(f).get("tasks", [])

    if args.dry_run:
        # 预览：对比基线 vs 当前文件（不运行同步、不更新基线）
        new_data = load_json(args.data) if os.path.exists(args.data) else {"tasks": []}
        changes, removed = compute_changes(old_tasks, new_data.get("tasks", []))
        title, text, url = build_success_card(changes, new_data, removed, cfg)
        print("=" * 60)
        print("[DRY-RUN] 将发送的 ActionCard 预览：")
        print("=" * 60)
        print(f"标题: {title}\n")
        print(text)
        print("=" * 60)
        print(f"跳转链接: {url}")
        print("（dry-run 未发送、未更新基线）")
        return

    # —— 1) 执行同步（通知仅在同步完成后触发）——
    print(f"▶ 开始执行同步脚本：{args.sync_script}")
    rc, out, err = run_sync(args.python, args.sync_script, dry_run=False)
    combined = out + "\n" + err
    print(combined)

    # —— 2) 载入运行后数据 ——
    new_data = load_json(args.data) if os.path.exists(args.data) else {"tasks": []}
    changes, removed = compute_changes(old_tasks, new_data.get("tasks", []))

    # —— 3) 初始化通知器（密钥来自环境变量）——
    try:
        notifier = DingTalkNotifier(cfg)
    except ValueError as e:
        print(f"[配置缺失] {e}", file=sys.stderr)
        # 同步成功但无法通知：写兜底，记日志，仍视为同步成功
        write_run_log(run_log, {
            "time": datetime.datetime.now().isoformat(timespec="seconds"),
            "result": "notify_skipped_no_webhook",
            "sync_rc": rc,
            "changes": len(changes),
        })
        return

    # —— 4) 成功 / 失败 分支 ——
    if rc != 0:
        stage = detect_stage(combined)
        title, text, url = build_failure_card(stage, combined, cfg)
        ok, res = send_card(notifier, title, text, url, log_path)
        write_run_log(run_log, {
            "time": datetime.datetime.now().isoformat(timespec="seconds"),
            "result": "sync_failed",
            "stage": stage,
            "notify_ok": ok,
            "notify_res": res if not ok else "ok",
        })
        print(f"\n[失败通知] 已发送失败 ActionCard：ok={ok}")
        # 同步失败：退出非 0，便于自动化记录失败
        sys.exit(1)

    # 同步成功 → 发送运行结果 ActionCard
    title, text, url = build_success_card(changes, new_data, removed, cfg)
    ok, res = send_card(notifier, title, text, url, log_path)
    # 更新基线（供下次对比）
    try:
        import shutil
        shutil.copyfile(args.data, args.baseline)
    except Exception as e:  # noqa: BLE001
        print(f"[警告] 基线更新失败: {e}", file=sys.stderr)
    write_run_log(run_log, {
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
        "result": "ok",
        "changes": len(changes),
        "removed": removed,
        "notify_ok": ok,
        "notify_res": res if not ok else "ok",
    })
    print(f"\n[完成] 同步成功，变更 {len(changes)} 项，ActionCard 发送 ok={ok}")


if __name__ == "__main__":
    main()
