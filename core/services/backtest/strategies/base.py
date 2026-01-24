# -*- coding: utf-8 -*-
"""
策略基类

定义统一的策略接口，所有回测策略都应实现此接口
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, List, Optional

from core.domain.advice import InvestmentAdvice
from core.domain.signal import SignalType, TradingSignal


class Strategy(ABC):
    """
    策略抽象基类

    所有回测策略都应继承此类并实现 generate_signals 方法
    """

    def __init__(self, name: str):
        """
        初始化策略

        Args:
            name: 策略名称
        """
        self.name = name

    @abstractmethod
    def generate_signals(
        self, advice: InvestmentAdvice, asset_data: Dict[str, Any], indicators: Dict[str, Any]
    ) -> List[TradingSignal]:
        """
        生成交易信号

        Args:
            advice: 投资建议
            asset_data: 资产数据
            indicators: 技术指标

        Returns:
            List[TradingSignal] 交易信号列表
        """
        pass

    def get_name(self) -> str:
        """获取策略名称"""
        return self.name
