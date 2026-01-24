# -*- coding: utf-8 -*-
"""
自定义Webhook通知渠道
"""

import json
import logging
import time
from typing import List, Optional

import requests

from .base import BaseNotificationChannel, NotificationChannel

logger = logging.getLogger(__name__)


class CustomChannel(BaseNotificationChannel):
    """自定义Webhook通知渠道"""

    def __init__(self, config: dict):
        """
        初始化自定义Webhook渠道

        Args:
            config: 配置字典，包含：
                - webhook_urls: Webhook URL列表
                - bearer_token: Bearer Token（可选）
        """
        super().__init__(config)
        self.webhook_urls = config.get("webhook_urls", [])
        if isinstance(self.webhook_urls, str):
            self.webhook_urls = [self.webhook_urls]
        self.bearer_token = config.get("bearer_token")
        self.dingtalk_max_bytes = 20000  # 钉钉机器人 body 字节上限

    @property
    def name(self) -> str:
        """返回渠道名称"""
        return "自定义Webhook"

    def is_configured(self) -> bool:
        """检查自定义Webhook配置是否完整"""
        return bool(self.webhook_urls)

    def send(self, content: str, **kwargs) -> bool:
        """
        推送消息到自定义 Webhook

        支持任意接受 POST JSON 的 Webhook 端点
        默认发送格式：{"text": "消息内容", "content": "消息内容"}

        适用于：
        - 钉钉机器人
        - Discord Webhook
        - Slack Incoming Webhook
        - 自建通知服务
        - 其他支持 POST JSON 的服务

        Args:
            content: 消息内容（Markdown 格式）

        Returns:
            是否至少有一个 Webhook 发送成功
        """
        if not self.is_configured():
            logger.warning("未配置自定义 Webhook，跳过推送")
            return False

        success_count = 0

        for i, url in enumerate(self.webhook_urls):
            try:
                # 钉钉机器人对 body 有字节上限（约 20000 bytes），超长需要分批发送
                if self._is_dingtalk_webhook(url):
                    if self._send_dingtalk_chunked(url, content):
                        logger.info(f"自定义 Webhook {i+1}（钉钉）推送成功")
                        success_count += 1
                    else:
                        logger.error(f"自定义 Webhook {i+1}（钉钉）推送失败")
                    continue

                # 其他 Webhook：单次发送
                payload = self._build_payload(url, content)
                if self._post_webhook(url, payload, timeout=30):
                    logger.info(f"自定义 Webhook {i+1} 推送成功")
                    success_count += 1
                else:
                    logger.error(f"自定义 Webhook {i+1} 推送失败")

            except Exception as e:
                logger.error(f"自定义 Webhook {i+1} 推送异常: {e}")

        logger.info(f"自定义 Webhook 推送完成：成功 {success_count}/{len(self.webhook_urls)}")
        return success_count > 0

    @staticmethod
    def _is_dingtalk_webhook(url: str) -> bool:
        """判断是否为钉钉Webhook"""
        url_lower = (url or "").lower()
        return "dingtalk" in url_lower or "oapi.dingtalk.com" in url_lower

    def _post_webhook(self, url: str, payload: dict, timeout: int = 30) -> bool:
        """发送Webhook请求"""
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "StockAnalysis/1.0",
        }
        # 支持 Bearer Token 认证
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        response = requests.post(url, data=body, headers=headers, timeout=timeout)
        if response.status_code == 200:
            return True
        logger.error(f"自定义 Webhook 推送失败: HTTP {response.status_code}")
        logger.debug(f"响应内容: {response.text[:200]}")
        return False

    def _chunk_markdown_by_bytes(self, content: str, max_bytes: int) -> List[str]:
        """按字节数分割Markdown内容"""

        def get_bytes(s: str) -> int:
            return len(s.encode("utf-8"))

        def split_by_bytes(text: str, limit: int) -> List[str]:
            parts: List[str] = []
            remaining = text
            while remaining:
                part = self._truncate_to_bytes(remaining, limit)
                if not part:
                    break
                parts.append(part)
                remaining = remaining[len(part) :]
            return parts

        # 优先按分隔线/标题分割，保证分页自然
        if "\n---\n" in content:
            sections = content.split("\n---\n")
            separator = "\n---\n"
        elif "\n### " in content:
            parts = content.split("\n### ")
            sections = [parts[0]] + [f"### {p}" for p in parts[1:]]
            separator = "\n"
        else:
            # fallback：按行拼接
            sections = content.split("\n")
            separator = "\n"

        chunks: List[str] = []
        current_chunk: List[str] = []
        current_bytes = 0
        sep_bytes = get_bytes(separator)

        for section in sections:
            section_bytes = get_bytes(section)
            extra = sep_bytes if current_chunk else 0

            # 单段超长：截断
            if section_bytes + extra > max_bytes:
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_bytes = 0

                # 无法按结构拆分时，按字节强制拆分
                for part in split_by_bytes(section, max(200, max_bytes - 200)):
                    chunks.append(part)
                continue

            if current_bytes + section_bytes + extra > max_bytes:
                chunks.append(separator.join(current_chunk))
                current_chunk = [section]
                current_bytes = section_bytes
            else:
                if current_chunk:
                    current_bytes += sep_bytes
                current_chunk.append(section)
                current_bytes += section_bytes

        if current_chunk:
            chunks.append(separator.join(current_chunk))

        # 移除空块
        return [c for c in (c.strip() for c in chunks) if c]

    def _send_dingtalk_chunked(self, url: str, content: str) -> bool:
        """分批发送钉钉消息"""
        # 为 payload 开销预留空间，避免 body 超限
        budget = max(1000, self.dingtalk_max_bytes - 1500)
        chunks = self._chunk_markdown_by_bytes(content, budget)
        if not chunks:
            return False

        total = len(chunks)
        ok = 0

        for idx, chunk in enumerate(chunks):
            marker = f"\n\n📄 *({idx+1}/{total})*" if total > 1 else ""
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "股票分析报告",
                    "text": chunk + marker,
                },
            }

            # 如果仍超限（极端情况下），再按字节硬截断一次
            body_bytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
            if body_bytes > self.dingtalk_max_bytes:
                hard_budget = max(200, budget - (body_bytes - self.dingtalk_max_bytes) - 200)
                payload["markdown"]["text"] = self._truncate_to_bytes(payload["markdown"]["text"], hard_budget)

            if self._post_webhook(url, payload, timeout=30):
                ok += 1
            else:
                logger.error(f"钉钉分批发送失败: 第 {idx+1}/{total} 批")

            if idx < total - 1:
                time.sleep(1)

        return ok == total

    def _build_payload(self, url: str, content: str) -> dict:
        """
        根据 URL 构建对应的 Webhook payload

        自动识别常见服务并使用对应格式
        """
        url_lower = url.lower()

        # 钉钉机器人
        if "dingtalk" in url_lower or "oapi.dingtalk.com" in url_lower:
            return {"msgtype": "markdown", "markdown": {"title": "股票分析报告", "text": content}}

        # Discord Webhook
        if "discord.com" in url_lower or "discordapp.com" in url_lower:
            return {"content": content}

        # Slack Incoming Webhook
        if "slack.com" in url_lower or "hooks.slack.com" in url_lower:
            return {"text": content}

        # 默认格式（兼容大多数Webhook）
        return {"text": content, "content": content}

    def _truncate_to_bytes(self, text: str, max_bytes: int) -> str:
        """
        按字节数截断文本，确保不会在多字节字符中间截断
        """
        encoded = text.encode("utf-8")
        if len(encoded) <= max_bytes:
            return text

        truncated = encoded[:max_bytes]
        while True:
            try:
                return truncated.decode("utf-8")
            except UnicodeDecodeError:
                truncated = truncated[:-1]
                if not truncated:
                    return ""
