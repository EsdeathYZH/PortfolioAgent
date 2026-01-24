# -*- coding: utf-8 -*-
"""
Telegram通知渠道
"""

import logging
import re
from typing import Optional

import requests

from .base import BaseNotificationChannel, NotificationChannel

logger = logging.getLogger(__name__)


class TelegramChannel(BaseNotificationChannel):
    """Telegram通知渠道"""

    def __init__(self, config: dict):
        """
        初始化Telegram渠道

        Args:
            config: 配置字典，包含：
                - bot_token: Telegram Bot Token
                - chat_id: Telegram Chat ID
        """
        super().__init__(config)
        self.bot_token = config.get("bot_token")
        self.chat_id = config.get("chat_id")
        self.max_length = 4096  # Telegram 消息最大长度

    @property
    def name(self) -> str:
        """返回渠道名称"""
        return "Telegram"

    def is_configured(self) -> bool:
        """检查Telegram配置是否完整"""
        return bool(self.bot_token and self.chat_id)

    def send(self, content: str, **kwargs) -> bool:
        """
        推送消息到 Telegram 机器人

        Telegram Bot API 格式：
        POST https://api.telegram.org/bot<token>/sendMessage
        {
            "chat_id": "xxx",
            "text": "消息内容",
            "parse_mode": "Markdown"
        }

        Args:
            content: 消息内容（Markdown 格式）

        Returns:
            是否发送成功
        """
        if not self.is_configured():
            logger.warning("Telegram 配置不完整，跳过推送")
            return False

        try:
            # Telegram API 端点
            api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

            if len(content) <= self.max_length:
                # 单条消息发送
                return self._send_message(api_url, content)
            else:
                # 分段发送长消息
                return self._send_chunked(api_url, content)

        except Exception as e:
            logger.error(f"发送 Telegram 消息失败: {e}")
            import traceback

            logger.debug(traceback.format_exc())
            return False

    def _send_message(self, api_url: str, text: str) -> bool:
        """发送单条 Telegram 消息"""
        # 转换 Markdown 为 Telegram 支持的格式
        telegram_text = self._convert_to_telegram_markdown(text)

        payload = {
            "chat_id": self.chat_id,
            "text": telegram_text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        response = requests.post(api_url, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                logger.info("Telegram 消息发送成功")
                return True
            else:
                error_desc = result.get("description", "未知错误")
                logger.error(f"Telegram 返回错误: {error_desc}")

                # 如果 Markdown 解析失败，尝试纯文本发送
                if "parse" in error_desc.lower() or "markdown" in error_desc.lower():
                    logger.info("尝试使用纯文本格式重新发送...")
                    payload_no_markdown = {
                        "chat_id": self.chat_id,
                        "text": text,  # 使用原始文本
                        "disable_web_page_preview": True,
                    }

                    response = requests.post(api_url, json=payload_no_markdown, timeout=10)
                    if response.status_code == 200 and response.json().get("ok"):
                        logger.info("Telegram 消息发送成功（纯文本）")
                        return True

                return False
        else:
            logger.error(f"Telegram 请求失败: HTTP {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return False

    def _send_chunked(self, api_url: str, content: str) -> bool:
        """分段发送长 Telegram 消息"""
        # 按段落分割
        sections = content.split("\n---\n")

        current_chunk = []
        current_length = 0
        all_success = True
        chunk_index = 1

        for section in sections:
            section_length = len(section) + 5  # +5 for "\n---\n"

            if current_length + section_length > self.max_length:
                # 发送当前块
                if current_chunk:
                    chunk_content = "\n---\n".join(current_chunk)
                    logger.info(f"发送 Telegram 消息块 {chunk_index}...")
                    if not self._send_message(api_url, chunk_content):
                        all_success = False
                    chunk_index += 1

                # 重置
                current_chunk = [section]
                current_length = section_length
            else:
                current_chunk.append(section)
                current_length += section_length

        # 发送最后一块
        if current_chunk:
            chunk_content = "\n---\n".join(current_chunk)
            logger.info(f"发送 Telegram 消息块 {chunk_index}（最后）...")
            if not self._send_message(api_url, chunk_content):
                all_success = False

        return all_success

    def _convert_to_telegram_markdown(self, text: str) -> str:
        """
        将标准 Markdown 转换为 Telegram 支持的格式

        Telegram Markdown 限制：
        - 不支持 # 标题
        - 使用 *bold* 而非 **bold**
        - 使用 _italic_
        """
        result = text

        # 移除 # 标题标记（Telegram 不支持）
        result = re.sub(r"^#{1,6}\s+", "", result, flags=re.MULTILINE)

        # 转换 **bold** 为 *bold*
        result = re.sub(r"\*\*(.+?)\*\*", r"*\1*", result)

        # 转义特殊字符（Telegram Markdown 需要）
        # 注意：不转义已经用于格式的 * _ `
        for char in ["[", "]", "(", ")"]:
            result = result.replace(char, f"\\{char}")

        return result
