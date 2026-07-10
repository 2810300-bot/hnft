#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 task_data.json 生成 notification_config.json 的 people 骨架
================================
避免手工逐个录入责任人手机号。运行后把输出的 people 段贴入
notification_config.json，并补全每位成员的 mobile（钉钉手机号）与 role。

用法：
  python3 gen_people_template.py --current task-tracker/task_data.json
  python3 gen_people_template.py --current task_data.json --output people.json
"""
import sys
import json
import argparse


def main():
    ap = argparse.ArgumentParser(description="生成 people 配置骨架")
    ap.add_argument("--current", required=True, help="task_data.json 路径")
    ap.add_argument("--output", default=None, help="输出文件路径（默认打印到终端）")
    args = ap.parse_args()

    with open(args.current, "r", encoding="utf-8") as f:
        data = json.load(f)

    names = []
    for t in data.get("tasks", []):
        for p in t.get("responsible", []):
            if p not in names:
                names.append(p)
    # 若数据自带 persons 字段，一并购入
    for p in data.get("persons", []):
        if isinstance(p, str) and p not in names:
            names.append(p)

    people = {}
    for n in names:
        people[n] = {"mobile": "13xxxxxxxxx", "role": "responsible", "notify": True}

    out = {
        "_comment": "将本段替换 notification_config.json 的 people 字段，"
                    "并补全 mobile 与 role（responsible/supervisor/gm）",
        "people": people,
    }

    text = json.dumps(out, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已写出 {len(people)} 位成员到 {args.output}")
    else:
        print(text)
        print(f"\n[提示] 共识别 {len(people)} 位责任人，请补全 mobile 与 role 后写入配置。")


if __name__ == "__main__":
    main()
