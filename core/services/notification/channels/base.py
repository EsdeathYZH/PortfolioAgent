# -*- coding: utf-8 -*-
"""
通知渠道基类
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class NotificationChannel(Enum):
    """通知渠道类型"""

    WECHAT = "wechat"  # 企业微信
    FEISHU = "feishu"  # 飞书
    TELEGRAM = "telegram"  # Telegram
    EMAIL = "email"  # 邮件
    PUSHOVER = "pushover"  # Pushover（手机/桌面推送）
    CUSTOM = "custom"  # 自定义 Webhook
    SERVERCHAN = "serverchan"  # Server酱/Web推送API
    UNKNOWN = "unknown"  # 未知


class BaseNotificationChannel(ABC):
    """
    通知渠道基类

    所有通知渠道都应该继承此类并实现 send 方法
    """

    def __init__(self, config: dict):
        """
        初始化渠道

        Args:
            config: 渠道配置字典
        """
        self.config = config

    @abstractmethod
    def send(self, content: str, **kwargs) -> bool:
        """
        发送消息

        Args:
            content: 消息内容
            **kwargs: 其他参数（如标题等）

        Returns:
            是否发送成功
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """
        检查渠道是否已配置

        Returns:
            是否已配置
        """
        pass

    def get_channel_name(self) -> str:
        """获取渠道中文名称"""
        return "未知渠道"

    def _truncate_to_bytes(self, text: str, max_bytes: int) -> str:
        """
        按字节数截断字符串，确保不会在多字节字符中间截断

        Args:
            text: 要截断的字符串
            max_bytes: 最大字节数

        Returns:
            截断后的字符串
        """
        encoded = text.encode("utf-8")
        if len(encoded) <= max_bytes:
            return text

        # 从 max_bytes 位置往前找，确保不截断多字节字符
        truncated = encoded[:max_bytes]
        # 尝试解码，如果失败则继续往前
        while truncated:
            try:
                return truncated.decode("utf-8")
            except UnicodeDecodeError:
                truncated = truncated[:-1]
        return ""


def get_channel_name(channel: NotificationChannel) -> str:
    """获取渠道中文名称"""
    names = {
        NotificationChannel.WECHAT: "企业微信",
        NotificationChannel.FEISHU: "飞书",
        NotificationChannel.TELEGRAM: "Telegram",
        NotificationChannel.EMAIL: "邮件",
        NotificationChannel.PUSHOVER: "Pushover",
        NotificationChannel.CUSTOM: "自定义Webhook",
        NotificationChannel.SERVERCHAN: "Server酱",
        NotificationChannel.UNKNOWN: "未知渠道",
    }
    return names.get(channel, "未知渠道")
