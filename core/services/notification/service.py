# -*- coding: utf-8 -*-
"""
通知服务统一接口

暂时保持向后兼容，逐步迁移到新架构
"""

import logging

# 暂时导入原有模块以保持向后兼容
import sys
from pathlib import Path
from pathlib import Path as PathLib
from typing import List, Optional

# 添加项目根目录到路径
project_root = PathLib(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config
from core.domain.analysis import AnalysisResult

logger = logging.getLogger(__name__)


class NotificationService:
    """
    通知服务（重构版）

    职责：
    1. 生成 Markdown 格式的分析日报
    2. 向所有已配置的渠道推送消息（多渠道并发）
    3. 支持本地保存日报

    暂时保持向后兼容，逐步迁移到新架构
    """

    def __init__(self):
        """初始化通知服务"""
        # 暂时使用原有实现，逐步迁移
        try:
            # 尝试导入原有模块
            from notification import NotificationService as OldNotificationService

            self._old_service = OldNotificationService()
            self._use_old = True
            logger.info("使用原有通知服务实现（向后兼容）")
        except ImportError:
            self._old_service = None
            self._use_old = False
            logger.warning("无法导入原有通知服务，将使用新实现")

        # 初始化新架构的渠道（逐步迁移）
        self._channels = []
        self._init_channels()

    def _init_channels(self):
        """初始化通知渠道"""
        config = get_config()

        # 企业微信
        if config.wechat_webhook_url:
            try:
                from .channels.wechat import WechatChannel

                self._channels.append(
                    WechatChannel(
                        {
                            "webhook_url": config.wechat_webhook_url,
                            "max_bytes": getattr(config, "wechat_max_bytes", 4000),
                        }
                    )
                )
            except Exception as e:
                logger.warning(f"初始化企业微信渠道失败: {e}")

        # 飞书
        feishu_url = getattr(config, "feishu_webhook_url", None)
        if feishu_url:
            try:
                from .channels.feishu import FeishuChannel

                self._channels.append(
                    FeishuChannel(
                        {
                            "webhook_url": feishu_url,
                            "max_bytes": getattr(config, "feishu_max_bytes", 20000),
                        }
                    )
                )
            except Exception as e:
                logger.warning(f"初始化飞书渠道失败: {e}")

        # Telegram
        telegram_bot_token = getattr(config, "telegram_bot_token", None)
        telegram_chat_id = getattr(config, "telegram_chat_id", None)
        if telegram_bot_token and telegram_chat_id:
            try:
                from .channels.telegram import TelegramChannel

                self._channels.append(
                    TelegramChannel(
                        {
                            "bot_token": telegram_bot_token,
                            "chat_id": telegram_chat_id,
                        }
                    )
                )
            except Exception as e:
                logger.warning(f"初始化Telegram渠道失败: {e}")

        # Email
        email_sender = config.email_sender
        email_password = config.email_password
        if email_sender and email_password:
            try:
                from .channels.email import EmailChannel

                email_receivers = config.email_receivers or ([email_sender] if email_sender else [])
                self._channels.append(
                    EmailChannel(
                        {
                            "sender": email_sender,
                            "password": email_password,
                            "receivers": email_receivers,
                        }
                    )
                )
            except Exception as e:
                logger.warning(f"初始化邮件渠道失败: {e}")

        # Pushover
        pushover_user_key = getattr(config, "pushover_user_key", None)
        pushover_api_token = getattr(config, "pushover_api_token", None)
        if pushover_user_key and pushover_api_token:
            try:
                from .channels.pushover import PushoverChannel

                self._channels.append(
                    PushoverChannel(
                        {
                            "user_key": pushover_user_key,
                            "api_token": pushover_api_token,
                        }
                    )
                )
            except Exception as e:
                logger.warning(f"初始化Pushover渠道失败: {e}")

        # ServerChan
        serverchan_send_key = getattr(config, "serverchan_send_key", None)
        if serverchan_send_key:
            try:
                from .channels.serverchan import ServerchanChannel

                self._channels.append(
                    ServerchanChannel(
                        {
                            "send_key": serverchan_send_key,
                            "channel": getattr(config, "serverchan_channel", None),
                            "noip": getattr(config, "serverchan_noip", False),
                        }
                    )
                )
            except Exception as e:
                logger.warning(f"初始化ServerChan渠道失败: {e}")

        # Custom Webhook
        custom_webhook_urls = getattr(config, "custom_webhook_urls", []) or []
        if custom_webhook_urls:
            try:
                from .channels.custom import CustomChannel

                self._channels.append(
                    CustomChannel(
                        {
                            "webhook_urls": custom_webhook_urls,
                            "bearer_token": getattr(config, "custom_webhook_bearer_token", None),
                        }
                    )
                )
            except Exception as e:
                logger.warning(f"初始化Custom Webhook渠道失败: {e}")

    def is_available(self) -> bool:
        """检查通知服务是否可用"""
        if self._use_old and self._old_service:
            return self._old_service.is_available()
        return len(self._channels) > 0

    def get_available_channels(self):
        """获取所有已配置的渠道"""
        if self._use_old and self._old_service:
            return self._old_service.get_available_channels()
        if self._use_old and self._old_service:
            return self._old_service.get_available_channels()
        return [ch.name for ch in self._channels if ch.is_configured]

    def generate_daily_report(self, results: List[AnalysisResult], report_date: Optional[str] = None) -> str:
        """
        生成 Markdown 格式的日报（详细版）

        暂时使用原有实现
        """
        if self._use_old and self._old_service:
            return self._old_service.generate_daily_report(results, report_date)

        # TODO: 使用新的formatters实现
        from .formatters.daily_report import DailyReportFormatter

        formatter = DailyReportFormatter()
        return formatter.format(results, report_date)

    def generate_dashboard_report(self, results: List[AnalysisResult], report_date: Optional[str] = None) -> str:
        """
        生成决策仪表盘格式的日报

        暂时使用原有实现
        """
        if self._use_old and self._old_service:
            return self._old_service.generate_dashboard_report(results, report_date)

        # TODO: 使用新的formatters实现
        from .formatters.dashboard import DashboardFormatter

        formatter = DashboardFormatter()
        return formatter.format(results, report_date)

    def generate_single_stock_report(self, result: AnalysisResult) -> str:
        """
        生成单只股票的分析报告

        暂时使用原有实现
        """
        if self._use_old and self._old_service:
            return self._old_service.generate_single_stock_report(result)

        # TODO: 使用新的formatters实现
        from .formatters.single_stock import SingleStockFormatter

        formatter = SingleStockFormatter()
        return formatter.format(result)

    def send(self, content: str) -> bool:
        """
        统一发送接口 - 向所有已配置的渠道发送

        暂时使用原有实现，逐步迁移到新架构
        """
        if self._use_old and self._old_service:
            return self._old_service.send(content)

        # 使用新架构的渠道
        success_count = 0
        for channel in self._channels:
            try:
                if channel.send(content):
                    success_count += 1
            except Exception as e:
                logger.error(f"{channel.get_channel_name()} 发送失败: {e}")

        return success_count > 0

    def save_report_to_file(self, content: str, filename: Optional[str] = None) -> str:
        """
        保存日报到本地文件

        Args:
            content: 日报内容
            filename: 文件名（可选，默认按日期生成）

        Returns:
            保存的文件路径
        """
        from datetime import datetime

        if filename is None:
            date_str = datetime.now().strftime("%Y%m%d")
            filename = f"report_{date_str}.md"

        # 确保 reports 目录存在
        reports_dir = Path(__file__).parent.parent.parent.parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        filepath = reports_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"日报已保存到: {filepath}")
        return str(filepath)


# 便捷函数（保持向后兼容）
def get_notification_service() -> NotificationService:
    """获取通知服务实例"""
    return NotificationService()


def send_daily_report(results: List[AnalysisResult]) -> bool:
    """
    发送每日报告的快捷方式

    自动识别渠道并推送
    """
    service = get_notification_service()

    # 生成报告
    report = service.generate_daily_report(results)

    # 保存到本地
    service.save_report_to_file(report)

    # 推送到配置的渠道（自动识别）
    return service.send(report)
