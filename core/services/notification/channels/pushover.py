# -*- coding: utf-8 -*-
"""
Pushover通知渠道
"""

import logging
import re
import time
from datetime import datetime
from typing import Optional

import requests

from .base import BaseNotificationChannel, NotificationChannel

logger = logging.getLogger(__name__)


class PushoverChannel(BaseNotificationChannel):
    """Pushover通知渠道"""

    def __init__(self, config: dict):
        """
        初始化Pushover渠道

        Args:
            config: 配置字典，包含：
                - user_key: Pushover 用户 Key
                - api_token: Pushover API Token
        """
        super().__init__(config)
        self.user_key = config.get("user_key")
        self.api_token = config.get("api_token")
        self.api_url = "https://api.pushover.net/1/messages.json"
        self.max_length = 1024  # Pushover 消息限制 1024 字符

    @property
    def name(self) -> str:
        """返回渠道名称"""
        return "Pushover"

    def is_configured(self) -> bool:
        """检查Pushover配置是否完整"""
        return bool(self.user_key and self.api_token)

    def send(self, content: str, title: Optional[str] = None, **kwargs) -> bool:
        """
        推送消息到 Pushover

        Pushover API 格式：
        POST https://api.pushover.net/1/messages.json
        {
            "token": "应用 API Token",
            "user": "用户 Key",
            "message": "消息内容",
            "title": "标题（可选）"
        }

        Pushover 特点：
        - 支持 iOS/Android/桌面多平台推送
        - 消息限制 1024 字符
        - 支持优先级设置
        - 支持 HTML 格式

        Args:
            content: 消息内容（Markdown 格式，会转为纯文本）
            title: 消息标题（可选，默认为"股票分析报告"）

        Returns:
            是否发送成功
        """
        if not self.is_configured():
            logger.warning("Pushover 配置不完整，跳过推送")
            return False

        # 处理消息标题
        if title is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            title = f"📈 股票分析报告 - {date_str}"

        # 转换 Markdown 为纯文本（Pushover 支持 HTML，但纯文本更通用）
        plain_content = self._markdown_to_plain_text(content)

        if len(plain_content) <= self.max_length:
            # 单条消息发送
            return self._send_message(plain_content, title)
        else:
            # 分段发送长消息
            return self._send_chunked(plain_content, title)

    def _markdown_to_plain_text(self, markdown_text: str) -> str:
        """
        将 Markdown 转换为纯文本

        移除 Markdown 格式标记，保留可读性
        """
        text = markdown_text

        # 移除标题标记 # ## ###
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

        # 移除加粗 **text** -> text
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)

        # 移除斜体 *text* -> text
        text = re.sub(r"\*(.+?)\*", r"\1", text)

        # 移除引用 > text -> text
        text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)

        # 移除列表标记 - item -> item
        text = re.sub(r"^[-*]\s+", "• ", text, flags=re.MULTILINE)

        # 移除分隔线 ---
        text = re.sub(r"^---+$", "────────", text, flags=re.MULTILINE)

        # 移除表格语法 |---|---|
        text = re.sub(r"\|[-:]+\|[-:|\s]+\|", "", text)
        text = re.sub(r"^\|(.+)\|$", r"\1", text, flags=re.MULTILINE)

        # 清理多余空行
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _send_message(self, message: str, title: str, priority: int = 0) -> bool:
        """
        发送单条 Pushover 消息

        Args:
            message: 消息内容
            title: 消息标题
            priority: 优先级 (-2 ~ 2，默认 0)
        """
        try:
            payload = {
                "token": self.api_token,
                "user": self.user_key,
                "message": message,
                "title": title,
                "priority": priority,
            }

            response = requests.post(self.api_url, data=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == 1:
                    logger.info("Pushover 消息发送成功")
                    return True
                else:
                    errors = result.get("errors", ["未知错误"])
                    logger.error(f"Pushover 返回错误: {errors}")
                    return False
            else:
                logger.error(f"Pushover 请求失败: HTTP {response.status_code}")
                logger.debug(f"响应内容: {response.text}")
                return False

        except Exception as e:
            logger.error(f"发送 Pushover 消息失败: {e}")
            return False

    def _send_chunked(self, content: str, title: str) -> bool:
        """
        分段发送长 Pushover 消息

        按段落分割，确保每段不超过最大长度
        """
        # 按段落（分隔线或双换行）分割
        if "────────" in content:
            sections = content.split("────────")
            separator = "────────"
        else:
            sections = content.split("\n\n")
            separator = "\n\n"

        chunks = []
        current_chunk = []
        current_length = 0

        for section in sections:
            # 计算添加这个 section 后的实际长度
            if current_chunk:
                # 已有元素，添加新元素需要：当前长度 + 分隔符 + 新 section
                new_length = current_length + len(separator) + len(section)
            else:
                # 第一个元素，不需要分隔符
                new_length = len(section)

            if new_length > self.max_length:
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                current_chunk = [section]
                current_length = len(section)
            else:
                current_chunk.append(section)
                current_length = new_length

        if current_chunk:
            chunks.append(separator.join(current_chunk))

        total_chunks = len(chunks)
        success_count = 0

        logger.info(f"Pushover 分批发送：共 {total_chunks} 批")

        for i, chunk in enumerate(chunks):
            # 添加分页标记到标题
            chunk_title = f"{title} ({i+1}/{total_chunks})" if total_chunks > 1 else title

            if self._send_message(chunk, chunk_title):
                success_count += 1
                logger.info(f"Pushover 第 {i+1}/{total_chunks} 批发送成功")
            else:
                logger.error(f"Pushover 第 {i+1}/{total_chunks} 批发送失败")

            # 批次间隔，避免触发频率限制
            if i < total_chunks - 1:
                time.sleep(1)

        return success_count == total_chunks
