# 工作任务跟踪系统 · 钉钉群通知子系统

> 在钉钉工作群中，当工作任务状态发生变化（分配、临近截止、逾期、完成等）时，自动向指定人员发送带 @ 提醒的结构化通知。
> 本子系统基于现有 `task-tracker` 静态站点与 `task_data.json` 数据管线构建，纯 Python 标准库实现，无需额外依赖。

---

## 一、总体架构

```
                         ┌─────────────────────────────────────────┐
                         │   现有同步流程（IMA → task_data.json）    │
                         └───────────────────┬─────────────────────┘
                                             │ 每次同步产出新的 task_data.json
                                             ▼
                         ┌─────────────────────────────────────────┐
                         │        task_watchdog.py  （变更检测）     │
                         │  ① 读取 task_data.baseline.json（上一版） │
                         │  ② 与最新 task_data.json 逐任务 diff      │
                         │  ③ 识别事件：新增/状态变更/临近/逾期/完成  │
                         └───────────────────┬─────────────────────┘
                                             │ 事件 + 任务对象
                                             ▼
                         ┌─────────────────────────────────────────┐
                         │     notification_config.json（权限引擎）  │
                         │  · 触发规则（哪些事件要通知）              │
                         │  · 角色权限（责任人/主管/总经理 各收什么） │
                         │  · 人员映射（姓名 → 钉钉手机号，用于 @）   │
                         └───────────────────┬─────────────────────┘
                                             │ 解析出「接收人 + 是否@」
                                             ▼
                         ┌─────────────────────────────────────────┐
                         │       dingtalk_notifier.py（推送通道）    │
                         │  群机器人 Webhook（加签）+ 可选 OpenAPI    │
                         │  消息类型：markdown(@) / actionCard(链接)  │
                         └───────────────────┬─────────────────────┘
                                             │ HTTPS POST
                                             ▼
                         ┌─────────────────────────────────────────┐
                         │        钉钉工作群（@责任人 + 群内知会）    │
                         └─────────────────────────────────────────┘
                                             │
                                  baseline 更新为最新版（防重复通知）
```

---

## 二、需求逐条映射

### 1. 通知触发条件
`task_watchdog.py` 在每次数据同步后运行，逐任务对比 `baseline` 与最新数据，识别以下 **5 类事件**：

| 事件 | 触发判定 | 默认开启 |
|------|----------|----------|
| `assigned` 任务分配/新增 | 任务 id 在 baseline 中不存在（新下发） | ✅ |
| `status_change` 状态变更 | 任务 `status` 字段发生非完成/非逾期的变化 | ✅ |
| `deadline_approaching` 截止临近 | 距 `deadline` ≤ `deadline_warning_days`(默认3天) 且未逾期未完成 | ✅ |
| `overdue` 逾期 | `deadline` 已过且 `status≠completed`，且 baseline 中尚未逾期 | ✅ |
| `completed` 任务完成 | `status` 由非完成变为 `completed` | ✅ |

> 临近提醒使用「相对今天」动态计算，因此即便 baseline 未变化，只要日期推进到阈值内即可触发，避免漏报。

### 2. 通知目标（群 + @精准提醒）
- 目标群通过 **群机器人 Webhook** 配置（`DINGTALK_WEBHOOK` 环境变量），所有通知发到该工作群。
- **@精准提醒**：markdown 消息通过 `at.atMobiles` 字段传入责任人手机号，实现群内真实 @（手机端强提醒）。
- 手机号来自 `notification_config.json` 的 `people` 映射表（姓名 → mobile），仅对 `notify=true` 的人员 @。
- 主管/总经理等角色在群内「知会」但不强制 @，避免刷屏（见权限模型）。

### 3. 通知内容
每条消息均为结构化卡片，包含：
- **任务标题**（`content`）
- **任务详情**（`category` 类别、`notes` 备注、责任人列表）
- **当前状态**（中文状态徽标：待启动/进行中/已逾期/已完成）
- **截止时间**（`deadline` 格式化 + 剩余天数）
- **相关链接**（actionCard 单按钮，跳转到 `task_tracker_url` 处理页）

消息模板示例（markdown）：
```
📋 **【任务逾期】安环台账印刷成册**
> 类别：临时重点工作
> 责任人：施洪彬、苏铮铮
> 截止：6月10日（已逾期 30 天）
> 状态：🔴 已逾期
> 备注：xxx
[点击在跟踪系统查看并处理](https://2810300-bot.github.io/hnft/task-tracker/)
```

### 4. 集成方式
**主通道 — 钉钉自定义群机器人（推荐起步）**
- 在目标工作群「智能群助手 → 添加机器人 → 自定义」创建，获得 Webhook URL。
- 开启「加签」获得 `secret`，消息通过 HMAC-SHA256 签名防伪造。
- 实现见 `dingtalk_notifier.py`，纯标准库（`urllib`/`hmac`/`hashlib`），零依赖。

**增强通道 — 钉钉 OpenAPI 工作通知（保证必达）**
- 群机器人仅群内可见，若成员离线可能漏看。对「逾期/完成」等强提醒场景，可用 `topapi/message/corpconversation/asyncsend_v2` 走「工作通知」，消息直接推送到个人钉钉会话（强提醒）。
- `dingtalk_notifier.py` 预留 `openapi` 通道接口，切换 `channel: openapi_worknotice` 即可启用（需 `app_key/app_secret/agent_id`）。
- 两种通道可并存：群内 @ 用于透明协作，工作通知用于个人兜底。

### 5. 权限管理（角色化，避免冗余/遗漏）
`notification_config.json` 中定义 **角色 → 事件** 的接收矩阵：

| 角色 | 接收事件 | 是否 @ |
|------|----------|--------|
| 责任人 `responsible` | 分配、截止临近、逾期 | ✅ @ |
| 主管 `supervisor` | 状态变更、逾期、完成 | ❌ 群内知会 |
| 总经理 `gm` | 逾期、完成 | ❌ 群内知会 |

- 每个人在 `people` 表中标注 `role` 与 `notify`（可单独关闭某人通知，如请假）。
- 通过角色矩阵而非「全员广播」，既保证责任人被精准 @，又避免主管/总经理被无关消息淹没。
- 新增人员只需在 `people` 表加一行（姓名+手机号+角色），无需改代码。

---

## 三、可靠性保障
- **防重复通知**：每次运行后把最新 `task_data.json` 落地为 `task_data.baseline.json`；仅 diff 出「本周期新变化」才通知。
- **失败重试**：`dingtalk_notifier` 内置 1 次退避重试；返回 `errcode≠0` 时写入 `notification_log.json` 并退出非零，便于定时任务捕获告警。
- **限流保护**：钉钉群机器人默认 20 条/分钟，watchdog 对单次运行通知数设上限（默认 20），超额写入待发队列日志，下次补发。
- **降级**：Webhook 不可达时不影响主同步流程（通知失败仅记日志，不阻断业务数据更新）。

---

## 四、安全
- **密钥不入仓**：Webhook 与加签 `secret` 通过环境变量 `DINGTALK_WEBHOOK` / `DINGTALK_SECRET` 注入；配置文件中仅保留占位符。
- **加签校验**：启用 `secret` 后，所有请求带 `timestamp+sign`，防止 Webhook 地址泄露后被滥发。
- **手机号最小化**：`people` 表仅用于 @，建议该配置文件仅限内部仓库或本地保存。

---

## 五、接入现有同步自动化流程（推荐：控制器收尾模式）

> 需求要点：「通知**仅在自动化流程执行完毕后**触发」，且要用 **ActionCard** 格式、含跳转按钮，失败要有兜底。
> 为此新增 `sync_notify_controller.py`：**先跑同步、再发通知**，单命令完成，天然满足「同步结束后才通知」。

### 运行链路
```
自动化（每周二 08:00）
   └─ sync_notify_controller.py
        ① 顺序执行 task_tracker_sync.py（IMA → task_data.json，含 git push）
        ② 对比本次运行前后的 task_data.json，识别变更
        ③ 同步成功 → 向「湖南伏泰工作通知群」发整体 ActionCard（含跳转按钮）
           同步失败 → 发失败兜底 ActionCard（含失败阶段 / 错误摘要 / 排查建议）
```

### 接入步骤
1. **准备密钥文件**（不入库，放本地 `~/.workbuddy/config/`）：
   ```bash
   # ~/.workbuddy/config/dingtalk_notify.env
   export DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=xxxx"
   export DINGTALK_SECRET="SECxxxx"
   ```
2. **把自动化原本直接调 `task_tracker_sync.py` 改为调控制器**（控制器内部会调同步脚本）：
   ```bash
   if [ -f ~/.workbuddy/config/dingtalk_notify.env ]; then
     source ~/.workbuddy/config/dingtalk_notify.env
   fi
   /Users/mac/.workbuddy/binaries/python/envs/default/bin/python \
     /Users/mac/.workbuddy/hnft-site/task-tracker/notifications/sync_notify_controller.py
   ```
3. **首次接入先 `--dry-run` 预览卡片**（不发送、不更新基线）：
   ```bash
   /Users/mac/.workbuddy/binaries/python/envs/default/bin/python \
     /Users/mac/.workbuddy/hnft-site/task-tracker/notifications/sync_notify_controller.py --dry-run
   ```

### ActionCard 格式（符合钉钉群机器人规范）
- `msgtype: actionCard`，单按钮 `singleTitle: "📊 查看任务跟踪看板"` → `singleURL` 直达看板。
- 卡片含：任务标题、类别/责任人/备注、当前状态、截止时间及剩余天数、跳转按钮。
- 成功卡片按紧急度排序（逾期 > 完成 > 状态 > 截止 > 内容 > 新增），超 10 项折叠提示。
- 失败卡片含失败阶段、错误摘要（末 8 行）、排查建议；同步失败控制器退出码非 0，便于自动化记录失败。

### 兜底与可靠性
- **通知不阻断同步**：同步成功但通知失败 → 写 `notifications/notify_failed.json` 兜底 + 记 `notification_log.json`，同步仍视为成功。
- **缺密钥不崩溃**：未设置 `DINGTALK_WEBHOOK` 时，控制器跳过通知、写运行日志并正常退出（同步照常完成）。
- **防重复**：每次成功运行后把 `task_data.json` 落地为 `task_data.baseline.json`，下次仅 diff 新变化。

---

## 六、已知数据问题与注意
1. **源数据存在重复 id**：实测 `task_data.json` 中有两个任务共用 `t23`（一个已完成、一个进行中）。
   若直接用 id 建索引会让错误配对、发出虚假通知。watchdog 已内置**按 id 去重（保留首次出现）+ 告警**，
   但建议上游同步脚本修正该重复 id，以免跟踪看板本身也出现展示错乱。
2. **人员手机号必须补全**：`people` 表中每位成员需填真实钉钉手机号（`mobile`）才能被 @。
   可用 `gen_people_template.py` 从 `task_data.json` 一键生成全部责任人的骨架，再补全 `mobile` 与 `role`。
3. **密钥不入仓**：`dingtalk.group_webhook` / `secret` 建议留占位符，运行时通过环境变量
   `DINGTALK_WEBHOOK` / `DINGTALK_SECRET` 注入，避免群机器人地址泄露后被滥发。
4. **首次运行先 `--dry-run`**：确认通知内容、@ 对象、知会对象无误后再正式推送。

## 七、文件清单
| 文件 | 作用 |
|------|------|
| `notifications/README.md` | 本设计文档 |
| `notifications/dingtalk_notifier.py` | 钉钉推送通道（群机器人/OpenAPI） |
| `notifications/task_watchdog.py` | 变更检测 + 权限分发 + 防重 + 去重 |
| `notifications/sync_notify_controller.py` | **同步后 ActionCard 通知控制器（接自动化收尾）** |
| `notifications/notification_config.json` | 触发规则 / 角色权限 / 人员映射（已含全部责任人骨架） |
| `notifications/gen_people_template.py` | 从 task_data.json 生成 people 配置骨架 |
| `notifications/notification_log.json` | 运行日志（自动生成，可忽略） |
| `notifications/notify_failed.json` | 通知发送失败时的兜底卡片（自动生成） |
