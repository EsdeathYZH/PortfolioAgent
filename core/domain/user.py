# -*- coding: utf-8 -*-
"""
用户配置领域模型
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class UserConfig:
    """
    用户配置数据类

    封装用户的股票订阅和通知渠道配置
    """

    username: str
    """用户名"""

    stocks: List[str]
    """订阅的股票代码列表"""

    channels: Dict[str, Dict[str, Any]]
    """
    通知渠道配置字典

    格式: {
        "email": {"sender": "...", "password": "...", "receivers": [...]},
        "serverchan": {"send_key": "...", "channel": "...", "noip": False},
        "wechat": {"webhook_url": "..."},
        "feishu": {"webhook_url": "..."},
        "telegram": {"bot_token": "...", "chat_id": "..."},
        "pushover": {"user_key": "...", "api_token": "..."},
        "custom": {"webhook_urls": [...], "bearer_token": "..."}
    }
    """

    def has_channel(self, channel_type: str) -> bool:
        """检查是否配置了指定类型的渠道"""
        return channel_type in self.channels

    def get_channel_config(self, channel_type: str) -> Dict[str, Any]:
        """获取指定渠道的配置"""
        return self.channels.get(channel_type, {})
