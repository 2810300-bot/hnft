#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
钉钉群通知推送通道
================================
支持两种通道：
  1. group_robot        —— 自定义群机器人 Webhook（加签），群内发送 + @提醒
  2. openapi_worknotice —— 钉钉 OpenAPI 工作通知（个人强提醒，保证必达）

纯标准库实现（urllib / hmac / hashlib / json），无需 pip 安装。

安全：Webhook 与加签 secret 优先从环境变量读取
      DINGTALK_WEBHOOK / DINGTALK_SECRET，避免密钥入库。
"""
import os
import sys
import time
import json
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
import urllib.error


class DingTalkNotifier:
    """钉钉消息推送器。"""

    def __init__(self, config: dict = None, timeout: int = 10):
        config = config or {}
        dt = config.get("dingtalk", {}) or {}
        self.channel = dt.get("channel", "group_robot")
        self.timeout = timeout

        # —— 群机器人通道参数 ——
        # 环境变量优先，其次配置文件
        self.webhook = os.environ.get("DINGTALK_WEBHOOK") or dt.get("group_webhook", "")
        self.secret = os.environ.get("DINGTALK_SECRET") or dt.get("secret", "")
        if not self.webhook:
            raise ValueError("缺少钉钉 Webhook：请设置环境变量 DINGTALK_WEBHOOK 或在配置中填写 dingtalk.group_webhook")

        # —— OpenAPI 工作通知通道参数 ——
        self.openapi = dt.get("openapi", {}) or {}
        self._app_token = None  # 缓存 access_token

    # ------------------------------------------------------------------ #
    # 群机器人：加签
    # ------------------------------------------------------------------ #
    def _signed_url(self) -> str:
        if not self.secret:
            return self.webhook
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            self.secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        sep = "&" if "?" in self.webhook else "?"
        return f"{self.webhook}{sep}timestamp={timestamp}&sign={sign}"

    # ------------------------------------------------------------------ #
    # 底层 POST
    # ------------------------------------------------------------------ #
    def _post(self, payload: dict) -> dict:
        url = self._signed_url()
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json; charset=utf-8"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as e:
            return {"errcode": e.code, "errmsg": f"HTTP {e.code}: {e.reason}"}
        except urllib.error.URLError as e:
            return {"errcode": -1, "errmsg": f"网络错误: {e.reason}"}
        except Exception as e:  # noqa: BLE001
            return {"errcode": -2, "errmsg": f"未知错误: {e}"}

    # ------------------------------------------------------------------ #
    # 群机器人：markdown 消息（支持 @）
    # ------------------------------------------------------------------ #
    def send_markdown(self, title: str, text: str, at_mobiles: list = None) -> dict:
        """发送 markdown 消息，at_mobiles 为被 @ 的手机号列表。"""
        at_mobiles = at_mobiles or []
        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text},
            "at": {"atMobiles": at_mobiles, "isAtAll": False},
        }
        return self._post(payload)

    # ------------------------------------------------------------------ #
    # 群机器人：actionCard 消息（带跳转按钮/链接）
    # ------------------------------------------------------------------ #
    def send_action_card(self, title: str, text: str, single_url: str,
                         single_title: str = "查看并处理") -> dict:
        """发送整体跳转 actionCard，单按钮跳转任务处理页。"""
        payload = {
            "msgtype": "actionCard",
            "actionCard": {
                "title": title,
                "text": text,
                "singleTitle": single_title,
                "singleURL": single_url,
            },
        }
        return self._post(payload)

    # ------------------------------------------------------------------ #
    # OpenAPI 工作通知（个人强提醒，保证必达）
    # ------------------------------------------------------------------ #
    def _get_app_token(self) -> str:
        if self._app_token:
            return self._app_token
        ck = self.openapi.get("app_key")
        cs = self.openapi.get("app_secret")
        if not ck or not cs:
            raise ValueError("OpenAPI 通道需要配置 dingtalk.openapi.app_key/app_secret")
        url = (f"https://oapi.dingtalk.com/gettoken?appkey={ck}&appsecret={cs}")
        try:
            with urllib.request.urlopen(urllib.request.Request(url), timeout=self.timeout) as r:
                d = json.loads(r.read().decode("utf-8"))
            if d.get("errcode") == 0:
                self._app_token = d["access_token"]
                return self._app_token
            raise RuntimeError(f"获取 token 失败: {d}")
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"获取 token 异常: {e}")

    def send_work_notice(self, userid_list: list, title: str, text: str,
                         url: str = None) -> dict:
        """通过工作通知推送给指定 userId 列表（强提醒，直达个人会话）。"""
        token = self._get_app_token()
        agent_id = self.openapi.get("agent_id")
        md = text
        if url:
            md += f"\n\n[点击查看]({url})"
        payload = {
            "agent_id": agent_id,
            "userid_list": ",".join(userid_list),
            "msg": {"msgtype": "markdown", "markdown": {"title": title, "text": md}},
        }
        api = f"https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2?access_token={token}"
        req = urllib.request.Request(
            api, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            return {"errcode": -1, "errmsg": f"工作通知发送失败: {e}"}


# ---------------------------------------------------------------------- #
# 便捷函数：供 watchdog 直接调用
# ---------------------------------------------------------------------- #
def build_notifier(config: dict) -> DingTalkNotifier:
    return DingTalkNotifier(config)


if __name__ == "__main__":
    # 自测：发送一条测试消息（需先设置环境变量）
    cfg = {"dingtalk": {"channel": "group_robot"}}
    try:
        n = DingTalkNotifier(cfg)
    except ValueError as e:
        print(f"[配置缺失] {e}\n请先设置 DINGTALK_WEBHOOK（与可选 DINGTALK_SECRET）")
        sys.exit(2)
    test_text = (
        "## 🔔 通知通道自测\n"
        "> 这是一条来自「工作任务跟踪系统」的测试消息，说明钉钉推送通道已打通。\n"
        "> 若你能看到本条消息，说明 Webhook 与加签配置正确。"
    )
    res = n.send_markdown("通知通道自测", test_text)
    print("发送结果:", res)
