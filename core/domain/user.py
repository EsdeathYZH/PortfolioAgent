# -*- coding: utf-8 -*-
"""
用户配置领域模型
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class UserConfig:
    """
    用户配置数据类

    封装用户的股票订阅和通知渠道配置
    """

    username: str
    """用户名"""

    stocks: List[str]
    """订阅的股票代码列表（可以是股票代码或 "AU" 表示黄金）"""

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

    def get_asset_list(self) -> List[Tuple[str, str]]:
        """
        解析资产列表，返回 (code, asset_type) 元组列表

        资产类型识别规则：
        - "AU" (大小写不敏感) -> "gold" (黄金)
        - 其他代码 -> "stock" (股票)

        Returns:
            List[Tuple[str, str]]: [(code, "stock"), ("AU", "gold"), ...]

        Examples:
            >>> config = UserConfig(username="test", stocks=["600519", "AU"], channels={})
            >>> config.get_asset_list()
            [('600519', 'stock'), ('AU', 'gold')]
        """
        assets = []
        for code in self.stocks:
            code_upper = code.strip().upper()
            if code_upper == "AU":
                assets.append(("AU", "gold"))
            else:
                assets.append((code.strip(), "stock"))
        return assets

    def get_stock_codes(self) -> List[str]:
        """
        获取股票代码列表（排除黄金等非股票资产）

        Returns:
            List[str]: 股票代码列表
        """
        return [code for code, asset_type in self.get_asset_list() if asset_type == "stock"]

    def get_gold_codes(self) -> List[str]:
        """
        获取黄金代码列表

        Returns:
            List[str]: 黄金代码列表（通常是 ["AU"]）
        """
        return [code for code, asset_type in self.get_asset_list() if asset_type == "gold"]
