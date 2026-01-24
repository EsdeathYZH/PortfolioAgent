# -*- coding: utf-8 -*-
"""
ServerChan通知渠道
"""

import logging
import time
from datetime import datetime
from typing import Optional

import requests

from .base import BaseNotificationChannel, NotificationChannel

logger = logging.getLogger(__name__)


class ServerchanChannel(BaseNotificationChannel):
    """ServerChan通知渠道"""

    def __init__(self, config: dict):
        """
        初始化ServerChan渠道

        Args:
            config: 配置字典，包含：
                - send_key: ServerChan Send Key
                - channel: 推送通道（可选）
                - noip: 是否隐藏IP（可选）
        """
        super().__init__(config)
        self.send_key = config.get("send_key")
        self.channel = config.get("channel")
        self.noip = config.get("noip", False)
        self.max_desp_bytes = 32 * 1024  # Server酱 desp 最大长度 32KB（32768字节）

    @property
    def name(self) -> str:
        """返回渠道名称"""
        return "Server酱"

    def is_configured(self) -> bool:
        """检查ServerChan配置是否完整"""
        return bool(self.send_key)

    def send(self, content: str, title: Optional[str] = None, **kwargs) -> bool:
        """
        推送消息到 Server酱/Web推送API

        Server酱 API 格式：
        POST https://sctapi.ftqq.com/{send_key}.send
        参数：
        - title: 必填，消息标题，最大长度32
        - desp: 选填，消息内容，支持Markdown，最大长度32KB
        - short: 选填，消息卡片内容，最大长度64，如果不指定会从desp中截取
        - noip: 选填，是否隐藏调用IP，为1则隐藏
        - channel: 选填，动态指定本次推送使用的消息通道，支持最多两个通道，多个通道值用竖线|隔开

        Args:
            content: 消息内容（Markdown 格式）
            title: 消息标题（可选，默认自动生成）

        Returns:
            是否发送成功
        """
        if not self.is_configured():
            logger.warning("Server酱配置不完整，跳过推送")
            return False

        # 构建 API URL
        api_url = f"https://sctapi.ftqq.com/{self.send_key}.send"

        # 生成标题
        if title is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            title = f"📈 A股分析报告 - {date_str}"

        # 确保标题不超过32字符
        if len(title) > 32:
            title = title[:29] + "..."

        # 检查内容长度
        content_bytes = len(content.encode("utf-8"))
        if content_bytes > self.max_desp_bytes:
            logger.info(f"Server酱消息内容超长({content_bytes}字节)，将分批发送")
            return self._send_chunked(api_url, content, title)

        # 单条消息发送
        return self._send_message(api_url, content, title)

    def _send_message(self, api_url: str, content: str, title: str) -> bool:
        """
        发送单条 Server酱消息

        Args:
            api_url: API URL
            content: 消息内容
            title: 消息标题
        """
        try:
            # 构建请求参数
            data = {
                "title": title,
                "desp": content,
            }

            # 可选参数
            if self.channel:
                data["channel"] = self.channel

            if self.noip:
                data["noip"] = "1"

            # 发送 POST 请求
            response = requests.post(api_url, data=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                # Server酱成功返回 {"code": 0, "message": "success", ...}
                if result.get("code") == 0:
                    logger.info("Server酱消息发送成功")
                    return True
                else:
                    error_msg = result.get("message", "未知错误")
                    logger.error(f"Server酱返回错误: {error_msg}")
                    return False
            else:
                logger.error(f"Server酱请求失败: HTTP {response.status_code}")
                logger.debug(f"响应内容: {response.text}")
                return False

        except Exception as e:
            logger.error(f"发送 Server酱消息失败: {e}")
            import traceback

            logger.debug(traceback.format_exc())
            return False

    def _send_chunked(self, api_url: str, content: str, title: str) -> bool:
        """
        分批发送长 Server酱消息

        按段落（---）或标题（###）分割，确保每批不超过限制
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
            # 无法智能分割，按行强制分割
            return self._send_force_chunked(api_url, content, title)

        chunks = []
        current_chunk = []
        current_bytes = 0
        separator_bytes = get_bytes(separator)

        for section in sections:
            section_bytes = get_bytes(section) + separator_bytes

            # 如果单个 section 就超长，需要强制截断
            if section_bytes > self.max_desp_bytes:
                # 先发送当前积累的内容
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_bytes = 0

                # 强制截断这个超长 section（按字节截断）
                truncated = self._truncate_to_bytes(section, self.max_desp_bytes - 200)
                truncated += "\n\n...(本段内容过长已截断)"
                chunks.append(truncated)
                continue

            # 检查加入后是否超长
            if current_bytes + section_bytes > self.max_desp_bytes:
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

        logger.info(f"Server酱分批发送：共 {total_chunks} 批")

        for i, chunk in enumerate(chunks):
            # 添加分页标记到标题
            chunk_title = f"{title} ({i+1}/{total_chunks})" if total_chunks > 1 else title

            if self._send_message(api_url, chunk, chunk_title):
                success_count += 1
                logger.info(f"Server酱第 {i+1}/{total_chunks} 批发送成功")
            else:
                logger.error(f"Server酱第 {i+1}/{total_chunks} 批发送失败")

            # 批次间隔，避免触发频率限制
            if i < total_chunks - 1:
                time.sleep(1)

        return success_count == total_chunks

    def _send_force_chunked(self, api_url: str, content: str, title: str) -> bool:
        """
        强制按字节分割发送（无法智能分割时的 fallback）
        """

        def get_bytes(s: str) -> int:
            return len(s.encode("utf-8"))

        chunks = []
        current_chunk = ""

        # 按行分割，确保不会在多字节字符中间截断
        lines = content.split("\n")

        for line in lines:
            test_chunk = current_chunk + ("\n" if current_chunk else "") + line
            if get_bytes(test_chunk) > self.max_desp_bytes - 200:  # 预留空间
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk = test_chunk

        if current_chunk:
            chunks.append(current_chunk)

        total_chunks = len(chunks)
        success_count = 0

        logger.info(f"Server酱强制分批发送：共 {total_chunks} 批")

        for i, chunk in enumerate(chunks):
            chunk_title = f"{title} ({i+1}/{total_chunks})" if total_chunks > 1 else title

            if self._send_message(api_url, chunk, chunk_title):
                success_count += 1
            else:
                logger.error(f"Server酱第 {i+1}/{total_chunks} 批发送失败")

            if i < total_chunks - 1:
                time.sleep(1)

        return success_count == total_chunks

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
