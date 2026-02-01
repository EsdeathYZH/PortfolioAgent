# -*- coding: utf-8 -*-
"""
通知服务统一接口

支持多用户模式，根据 UserConfig 初始化通知渠道
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

from core.domain.analysis import AnalysisResult
from core.domain.user import UserConfig

logger = logging.getLogger(__name__)


class NotificationService:
    """
    通知服务

    职责：
    1. 生成 Markdown 格式的分析日报
    2. 向所有已配置的渠道推送消息（多渠道并发）
    3. 支持本地保存日报
    """

    def __init__(self, user_config: UserConfig):
        """
        初始化通知服务

        Args:
            user_config: 用户配置（必需）
        """
        self.user_config = user_config
        self._channels = []
        self._init_user_channels()

    def _init_user_channels(self):
        """从用户配置初始化通知渠道"""
        channels = self.user_config.channels

        # Email 渠道
        if self.user_config.has_channel("email"):
            try:
                from .channels.email import EmailChannel

                email_config = self.user_config.get_channel_config("email")
                self._channels.append(EmailChannel(email_config))
            except Exception as e:
                logger.warning(f"初始化邮件渠道失败: {e}")

        # ServerChan 渠道
        if self.user_config.has_channel("serverchan"):
            try:
                from .channels.serverchan import ServerchanChannel

                serverchan_config = self.user_config.get_channel_config("serverchan")
                self._channels.append(ServerchanChannel(serverchan_config))
            except Exception as e:
                logger.warning(f"初始化ServerChan渠道失败: {e}")

        # 企业微信渠道
        if self.user_config.has_channel("wechat"):
            try:
                from .channels.wechat import WechatChannel

                wechat_config = self.user_config.get_channel_config("wechat")
                self._channels.append(WechatChannel(wechat_config))
            except Exception as e:
                logger.warning(f"初始化企业微信渠道失败: {e}")

        # 飞书渠道
        if self.user_config.has_channel("feishu"):
            try:
                from .channels.feishu import FeishuChannel

                feishu_config = self.user_config.get_channel_config("feishu")
                self._channels.append(FeishuChannel(feishu_config))
            except Exception as e:
                logger.warning(f"初始化飞书渠道失败: {e}")

        # Telegram 渠道
        if self.user_config.has_channel("telegram"):
            try:
                from .channels.telegram import TelegramChannel

                telegram_config = self.user_config.get_channel_config("telegram")
                self._channels.append(TelegramChannel(telegram_config))
            except Exception as e:
                logger.warning(f"初始化Telegram渠道失败: {e}")

        # Pushover 渠道
        if self.user_config.has_channel("pushover"):
            try:
                from .channels.pushover import PushoverChannel

                pushover_config = self.user_config.get_channel_config("pushover")
                self._channels.append(PushoverChannel(pushover_config))
            except Exception as e:
                logger.warning(f"初始化Pushover渠道失败: {e}")

        # Custom Webhook 渠道
        if self.user_config.has_channel("custom"):
            try:
                from .channels.custom import CustomChannel

                custom_config = self.user_config.get_channel_config("custom")
                self._channels.append(CustomChannel(custom_config))
            except Exception as e:
                logger.warning(f"初始化Custom Webhook渠道失败: {e}")

        logger.info(f"用户 {self.user_config.username} 初始化了 {len(self._channels)} 个通知渠道")

    def is_available(self) -> bool:
        """检查通知服务是否可用"""
        return len(self._channels) > 0

    def get_available_channels(self):
        """获取所有已配置的渠道"""
        return [ch.name for ch in self._channels if ch.is_configured]

    def generate_daily_report(self, results: List[AnalysisResult], report_date: Optional[str] = None) -> str:
        """
        生成 Markdown 格式的日报（详细版）
        """
        from .formatters.daily_report import DailyReportFormatter

        formatter = DailyReportFormatter()
        return formatter.format(results, report_date)

    def generate_dashboard_report(self, results: List[AnalysisResult], report_date: Optional[str] = None) -> str:
        """
        生成决策仪表盘格式的日报
        """
        from .formatters.dashboard import DashboardFormatter

        formatter = DashboardFormatter()
        return formatter.format(results, report_date)

    def generate_single_stock_report(self, result: AnalysisResult) -> str:
        """
        生成单只股票的分析报告
        """
        from .formatters.single_stock import SingleStockFormatter

        formatter = SingleStockFormatter()
        return formatter.format(result)

    def send(self, content: str) -> bool:
        """
        统一发送接口 - 向所有已配置的渠道发送
        """
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


# 注意：移除了便捷函数，因为现在必须传入 UserConfig
