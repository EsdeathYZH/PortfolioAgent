# -*- coding: utf-8 -*-
"""
飞书通知渠道
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional

import requests

from .base import BaseNotificationChannel, NotificationChannel

logger = logging.getLogger(__name__)


class FeishuChannel(BaseNotificationChannel):
    """飞书通知渠道"""

    def __init__(self, config: dict):
        """
        初始化飞书渠道

        Args:
            config: 配置字典，包含：
                - webhook_url: 飞书 Webhook URL
                - max_bytes: 最大字节数（默认20000）
        """
        super().__init__(config)
        self.webhook_url = config.get("webhook_url")
        self.max_bytes = config.get("max_bytes", 20000)

    @property
    def name(self) -> str:
        """返回渠道名称"""
        return "飞书"

    def is_configured(self) -> bool:
        """检查飞书配置是否完整"""
        return bool(self.webhook_url)

    def send(self, content: str, **kwargs) -> bool:
        """
        推送消息到飞书机器人

        飞书自定义机器人 Webhook 消息格式：
        {
            "msg_type": "text",
            "content": {
                "text": "文本内容"
            }
        }

        说明：飞书文本消息不会渲染 Markdown，需使用交互卡片（lark_md）格式

        注意：飞书文本消息限制约 20KB，超长内容会自动分批发送

        Args:
            content: 消息内容（Markdown 会转为纯文本）

        Returns:
            是否发送成功
        """
        if not self.is_configured():
            logger.warning("飞书 Webhook 未配置，跳过推送")
            return False

        # 飞书 lark_md 支持有限，先做格式转换
        formatted_content = self._format_feishu_markdown(content)

        # 检查字节长度，超长则分批发送
        content_bytes = len(formatted_content.encode("utf-8"))
        if content_bytes > self.max_bytes:
            logger.info(f"飞书消息内容超长({content_bytes}字节/{len(content)}字符)，将分批发送")
            return self._send_chunked(formatted_content, self.max_bytes)

        try:
            return self._send_message(formatted_content)
        except Exception as e:
            logger.error(f"发送飞书消息失败: {e}")
            return False

    def _send_chunked(self, content: str, max_bytes: int) -> bool:
        """
        分批发送长消息到飞书

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
            # 无法智能分割，按行强制分割
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

        logger.info(f"飞书分批发送：共 {total_chunks} 批")

        for i, chunk in enumerate(chunks):
            # 添加分页标记
            if total_chunks > 1:
                page_marker = f"\n\n📄 ({i+1}/{total_chunks})"
                chunk_with_marker = chunk + page_marker
            else:
                chunk_with_marker = chunk

            try:
                if self._send_message(chunk_with_marker):
                    success_count += 1
                    logger.info(f"飞书第 {i+1}/{total_chunks} 批发送成功")
                else:
                    logger.error(f"飞书第 {i+1}/{total_chunks} 批发送失败")
            except Exception as e:
                logger.error(f"飞书第 {i+1}/{total_chunks} 批发送异常: {e}")

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

        logger.info(f"飞书强制分批发送：共 {total_chunks} 批")

        for i, chunk in enumerate(chunks):
            page_marker = f"\n\n📄 ({i+1}/{total_chunks})" if total_chunks > 1 else ""

            try:
                if self._send_message(chunk + page_marker):
                    success_count += 1
            except Exception as e:
                logger.error(f"飞书第 {i+1}/{total_chunks} 批发送异常: {e}")

            if i < total_chunks - 1:
                time.sleep(1)

        return success_count == total_chunks

    def _send_message(self, content: str) -> bool:
        """发送单条飞书消息（优先使用 Markdown 卡片）"""

        def _post_payload(payload: Dict[str, Any]) -> bool:
            logger.debug(f"飞书请求 URL: {self.webhook_url}")
            logger.debug(f"飞书请求 payload 长度: {len(content)} 字符")

            response = requests.post(self.webhook_url, json=payload, timeout=30)

            logger.debug(f"飞书响应状态码: {response.status_code}")
            logger.debug(f"飞书响应内容: {response.text}")

            if response.status_code == 200:
                result = response.json()
                code = result.get("code") if "code" in result else result.get("StatusCode")
                if code == 0:
                    logger.info("飞书消息发送成功")
                    return True
                else:
                    error_msg = result.get("msg") or result.get("StatusMessage", "未知错误")
                    error_code = result.get("code") or result.get("StatusCode", "N/A")
                    logger.error(f"飞书返回错误 [code={error_code}]: {error_msg}")
                    logger.error(f"完整响应: {result}")
                    return False
            else:
                logger.error(f"飞书请求失败: HTTP {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return False

        # 1) 优先使用交互卡片（支持 Markdown 渲染）
        card_payload = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {"title": {"tag": "plain_text", "content": "A股智能分析报告"}},
                "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": content}}],
            },
        }

        if _post_payload(card_payload):
            return True

        # 2) 回退为普通文本消息
        text_payload = {"msg_type": "text", "content": {"text": content}}

        return _post_payload(text_payload)

    def _format_feishu_markdown(self, content: str) -> str:
        """
        将通用 Markdown 转换为飞书 lark_md 更友好的格式
        - 飞书不支持 Markdown 标题（# / ## / ###），用加粗代替
        - 引用块使用前缀替代
        - 分隔线统一为细线
        - 表格转换为条目列表
        """

        def _flush_table_rows(buffer: List[str], output: List[str]) -> None:
            if not buffer:
                return

            def _parse_row(row: str) -> List[str]:
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                return [c for c in cells if c]

            rows = []
            for raw in buffer:
                if re.match(r"^\s*\|?\s*[:-]+\s*(\|\s*[:-]+\s*)+\|?\s*$", raw):
                    continue
                parsed = _parse_row(raw)
                if parsed:
                    rows.append(parsed)

            if not rows:
                return

            header = rows[0]
            data_rows = rows[1:] if len(rows) > 1 else []
            for row in data_rows:
                pairs = []
                for idx, cell in enumerate(row):
                    key = header[idx] if idx < len(header) else f"列{idx + 1}"
                    pairs.append(f"{key}：{cell}")
                output.append(f"• {' | '.join(pairs)}")

        lines = []
        table_buffer: List[str] = []

        for raw_line in content.splitlines():
            line = raw_line.rstrip()

            if line.strip().startswith("|"):
                table_buffer.append(line)
                continue

            if table_buffer:
                _flush_table_rows(table_buffer, lines)
                table_buffer = []

            if re.match(r"^#{1,6}\s+", line):
                title = re.sub(r"^#{1,6}\s+", "", line).strip()
                line = f"**{title}**" if title else ""
            elif line.startswith("> "):
                quote = line[2:].strip()
                line = f"💬 {quote}" if quote else ""
            elif line.strip() == "---":
                line = "────────"
            elif line.startswith("- "):
                line = f"• {line[2:].strip()}"

            lines.append(line)

        if table_buffer:
            _flush_table_rows(table_buffer, lines)

        return "\n".join(lines).strip()

    def _truncate_to_bytes(self, text: str, max_bytes: int) -> str:
        """
        按字节数截断文本，确保不会在多字节字符中间截断

        Args:
            text: 要截断的文本
            max_bytes: 最大字节数

        Returns:
            截断后的文本
        """
        encoded = text.encode("utf-8")
        if len(encoded) <= max_bytes:
            return text

        # 从后往前截断，确保不会在多字节字符中间截断
        truncated = encoded[:max_bytes]
        # 尝试解码，如果失败则继续截断
        while True:
            try:
                return truncated.decode("utf-8")
            except UnicodeDecodeError:
                truncated = truncated[:-1]
                if not truncated:
                    return ""
