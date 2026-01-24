# -*- coding: utf-8 -*-
"""
邮件通知渠道
"""

import logging
import re
import smtplib
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from .base import BaseNotificationChannel, NotificationChannel

logger = logging.getLogger(__name__)


# SMTP 服务器配置（自动识别）
SMTP_CONFIGS = {
    "qq.com": {"server": "smtp.qq.com", "port": 465, "ssl": True},
    "163.com": {"server": "smtp.163.com", "port": 465, "ssl": True},
    "126.com": {"server": "smtp.126.com", "port": 465, "ssl": True},
    "sina.com": {"server": "smtp.sina.com", "port": 465, "ssl": True},
    "gmail.com": {"server": "smtp.gmail.com", "port": 587, "ssl": False},
    "outlook.com": {"server": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "hotmail.com": {"server": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "yahoo.com": {"server": "smtp.mail.yahoo.com", "port": 587, "ssl": False},
}


class EmailChannel(BaseNotificationChannel):
    """邮件通知渠道"""

    def __init__(self, config: dict):
        """
        初始化邮件渠道

        Args:
            config: 配置字典，包含：
                - sender: 发件人邮箱
                - password: 邮箱授权码
                - receivers: 收件人邮箱列表
        """
        super().__init__(config)
        self.sender = config.get("sender")
        self.password = config.get("password")
        self.receivers = config.get("receivers", [])
        if not self.receivers and self.sender:
            self.receivers = [self.sender]

    @property
    def name(self) -> str:
        """返回渠道名称"""
        return "邮件"

    def is_configured(self) -> bool:
        """检查邮件配置是否完整"""
        return bool(self.sender and self.password and self.receivers)

    def send(self, content: str, subject: Optional[str] = None, **kwargs) -> bool:
        """
        通过 SMTP 发送邮件（自动识别 SMTP 服务器）

        Args:
            content: 邮件内容（支持 Markdown，会转换为 HTML）
            subject: 邮件主题（可选，默认自动生成）

        Returns:
            是否发送成功
        """
        if not self.is_configured():
            logger.warning("邮件配置不完整，跳过推送")
            return False

        try:
            # 生成主题
            if subject is None:
                date_str = datetime.now().strftime("%Y-%m-%d")
                subject = f"📈 A股智能分析报告 - {date_str}"

            # 将 Markdown 转换为简单 HTML
            html_content = self._markdown_to_html(content)

            # 构建邮件
            msg = MIMEMultipart("alternative")
            msg["Subject"] = Header(subject, "utf-8")
            msg["From"] = self.sender
            msg["To"] = ", ".join(self.receivers)

            # 添加纯文本和 HTML 两个版本
            text_part = MIMEText(content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(text_part)
            msg.attach(html_part)

            # 自动识别 SMTP 配置
            domain = self.sender.split("@")[-1].lower()
            smtp_config = SMTP_CONFIGS.get(domain)

            if smtp_config:
                smtp_server = smtp_config["server"]
                smtp_port = smtp_config["port"]
                use_ssl = smtp_config["ssl"]
                logger.info(f"自动识别邮箱类型: {domain} -> {smtp_server}:{smtp_port}")
            else:
                # 未知邮箱，尝试通用配置
                smtp_server = f"smtp.{domain}"
                smtp_port = 465
                use_ssl = True
                logger.warning(f"未知邮箱类型 {domain}，尝试通用配置: {smtp_server}:{smtp_port}")

            # 根据配置选择连接方式
            if use_ssl:
                # SSL 连接（端口 465）
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
            else:
                # TLS 连接（端口 587）
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                server.starttls()

            server.login(self.sender, self.password)
            server.send_message(msg)
            server.quit()

            logger.info(f"邮件发送成功，收件人: {self.receivers}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("邮件发送失败：认证错误，请检查邮箱和授权码是否正确")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"邮件发送失败：无法连接 SMTP 服务器 - {e}")
            return False
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False

    def _markdown_to_html(self, markdown_text: str) -> str:
        """
        将 Markdown 转换为简单的 HTML

        支持：标题、加粗、列表、分隔线
        """
        html = markdown_text

        # 转义 HTML 特殊字符
        html = html.replace("&", "&amp;")
        html = html.replace("<", "&lt;")
        html = html.replace(">", "&gt;")

        # 标题 (# ## ###)
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)

        # 加粗 **text**
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)

        # 斜体 *text*
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

        # 分隔线 ---
        html = re.sub(r"^---$", r"<hr>", html, flags=re.MULTILINE)

        # 列表项 - item
        html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)

        # 引用 > text
        html = re.sub(r"^&gt; (.+)$", r"<blockquote>\1</blockquote>", html, flags=re.MULTILINE)

        # 换行
        html = html.replace("\n", "<br>\n")

        # 包装 HTML
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }}
                h1, h2, h3 {{ color: #333; }}
                hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
                blockquote {{ border-left: 4px solid #ddd; padding-left: 16px; color: #666; }}
                li {{ margin: 4px 0; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
