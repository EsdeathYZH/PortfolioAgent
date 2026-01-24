# -*- coding: utf-8 -*-
"""
企业微信通知渠道
"""

import logging
import time
from typing import Optional

import requests

from .base import BaseNotificationChannel, NotificationChannel

logger = logging.getLogger(__name__)


class WechatChannel(BaseNotificationChannel):
    """企业微信通知渠道"""

    def __init__(self, config: dict):
        """
        初始化企业微信渠道

        Args:
            config: 配置字典，包含：
                - webhook_url: 企业微信 Webhook URL
                - max_bytes: 最大字节数（默认4000）
        """
        super().__init__(config)
        self.webhook_url = config.get("webhook_url")
        self.max_bytes = config.get("max_bytes", 4000)

    def get_channel_name(self) -> str:
        return "企业微信"

    def is_configured(self) -> bool:
        """检查企业微信配置是否完整"""
        return bool(self.webhook_url)

    def send(self, content: str, **kwargs) -> bool:
        """
        推送消息到企业微信机器人

        企业微信 Webhook 消息格式：
        {
            "msgtype": "markdown",
            "markdown": {
                "content": "Markdown 内容"
            }
        }

        注意：企业微信 Markdown 限制 4096 字节（非字符），超长内容会自动分批发送

        Args:
            content: Markdown 格式的消息内容

        Returns:
            是否发送成功
        """
        if not self.is_configured():
            logger.warning("企业微信 Webhook 未配置，跳过推送")
            return False

        # 检查字节长度，超长则分批发送
        content_bytes = len(content.encode("utf-8"))
        if content_bytes > self.max_bytes:
            logger.info(f"消息内容超长({content_bytes}字节/{len(content)}字符)，将分批发送")
            return self._send_chunked(content, self.max_bytes)

        try:
            return self._send_message(content)
        except Exception as e:
            logger.error(f"发送企业微信消息失败: {e}")
            return False

    def _send_chunked(self, content: str, max_bytes: int) -> bool:
        """
        分批发送长消息到企业微信

        按股票分析块（以 --- 或 ### 分隔）智能分割，确保每批不超过限制

        Args:
            content: 完整消息内容
            max_bytes: 单条消息最大字节数

        Returns:
            是否全部发送成功
        """

        def get_bytes(s: str) -> int:
            """获取字符串的 UTF-8 字节数"""
            return len(s.encode("utf-8"))

        # 智能分割：优先按 "---" 分隔（股票之间的分隔线）
        # 如果没有分隔线，按 "### " 标题分割（每只股票的标题）
        if "\n---\n" in content:
            sections = content.split("\n---\n")
            separator = "\n---\n"
        elif "\n### " in content:
            # 按 ### 分割，但保留 ### 前缀
            parts = content.split("\n### ")
            sections = [parts[0]] + [f"### {p}" for p in parts[1:]]
            separator = "\n"
        else:
            # 无法智能分割，按字符强制分割
            return self._send_force_chunked(content, max_bytes)

        chunks = []
        current_chunk = []
        current_bytes = 0
        separator_bytes = get_bytes(separator)

        for section in sections:
            section_bytes = get_bytes(section) + separator_bytes

            # 如果单个 section 就超长，需要强制截断
            if section_bytes > max_bytes:
                # 先发送当前积累的内容
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_bytes = 0

                # 强制截断这个超长 section（按字节截断）
                truncated = self._truncate_to_bytes(section, max_bytes - 200)
                truncated += "\n\n...(本段内容过长已截断)"
                chunks.append(truncated)
                continue

            # 检查加入后是否超长
            if current_bytes + section_bytes > max_bytes:
                # 保存当前块，开始新块
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                current_chunk = [section]
                current_bytes = section_bytes
            else:
                current_chunk.append(section)
                current_bytes += section_bytes

        # 添加最后一块
        if current_chunk:
            chunks.append(separator.join(current_chunk))

        # 分批发送
        total_chunks = len(chunks)
        success_count = 0

        logger.info(f"企业微信分批发送：共 {total_chunks} 批")

        for i, chunk in enumerate(chunks):
            # 添加分页标记
            if total_chunks > 1:
                page_marker = f"\n\n📄 *({i+1}/{total_chunks})*"
                chunk_with_marker = chunk + page_marker
            else:
                chunk_with_marker = chunk

            try:
                if self._send_message(chunk_with_marker):
                    success_count += 1
                    logger.info(f"企业微信第 {i+1}/{total_chunks} 批发送成功")
                else:
                    logger.error(f"企业微信第 {i+1}/{total_chunks} 批发送失败")
            except Exception as e:
                logger.error(f"企业微信第 {i+1}/{total_chunks} 批发送异常: {e}")

            # 批次间隔，避免触发频率限制
            if i < total_chunks - 1:
                time.sleep(1)

        return success_count == total_chunks

    def _send_force_chunked(self, content: str, max_bytes: int) -> bool:
        """
        强制按字节分割发送（无法智能分割时的 fallback）

        Args:
            content: 完整消息内容
            max_bytes: 单条消息最大字节数
        """
        chunks = []
        current_chunk = ""

        # 按行分割，确保不会在多字节字符中间截断
        lines = content.split("\n")

        for line in lines:
            test_chunk = current_chunk + ("\n" if current_chunk else "") + line
            if len(test_chunk.encode("utf-8")) > max_bytes - 100:  # 预留空间给分页标记
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk = test_chunk

        if current_chunk:
            chunks.append(current_chunk)

        total_chunks = len(chunks)
        success_count = 0

        logger.info(f"企业微信强制分批发送：共 {total_chunks} 批")

        for i, chunk in enumerate(chunks):
            page_marker = f"\n\n📄 *({i+1}/{total_chunks})*" if total_chunks > 1 else ""

            try:
                if self._send_message(chunk + page_marker):
                    success_count += 1
            except Exception as e:
                logger.error(f"企业微信第 {i+1}/{total_chunks} 批发送异常: {e}")

            if i < total_chunks - 1:
                time.sleep(1)

        return success_count == total_chunks

    def _send_message(self, content: str) -> bool:
        """发送企业微信消息"""
        payload = {"msgtype": "markdown", "markdown": {"content": content}}

        response = requests.post(self.webhook_url, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get("errcode") == 0:
                logger.info("企业微信消息发送成功")
                return True
            else:
                logger.error(f"企业微信返回错误: {result}")
                return False
        else:
            logger.error(f"企业微信请求失败: {response.status_code}")
            return False
