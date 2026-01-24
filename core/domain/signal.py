# -*- coding: utf-8 -*-
"""
交易信号实体

用于回测功能的交易信号定义
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Optional


class SignalType(Enum):
    """信号类型"""

    BUY = "买入"
    SELL = "卖出"
    HOLD = "持有"
    CLOSE = "平仓"


class SignalSource(Enum):
    """信号来源"""

    TREND_RULE = "趋势规则"
    BIAS_RULE = "乖离率规则"
    VOLUME_RULE = "量能规则"
    SUPPORT_RULE = "支撑规则"
    RISK_RULE = "风险规则"
    AI_ANALYSIS = "AI分析"
    MANUAL = "手动"
    SYSTEM = "系统"


@dataclass
class TradingSignal:
    """
    交易信号实体

    用于回测和策略执行，记录具体的交易信号
    """

    # 基本信息
    code: str  # 资产代码
    name: str  # 资产名称
    signal_type: SignalType  # 信号类型
    source: SignalSource  # 信号来源

    # 价格和时间
    price: float  # 信号价格
    timestamp: datetime  # 信号时间戳
    date: date  # 信号日期

    # 数量（可选，用于回测）
    quantity: Optional[int] = None  # 交易数量（股）
    amount: Optional[float] = None  # 交易金额（元）

    # 规则信息
    rule_name: Optional[str] = None  # 规则名称
    rule_params: Dict[str, Any] = None  # 规则参数

    # 信号强度
    strength: float = 1.0  # 信号强度 0.0-1.0

    # 备注
    note: Optional[str] = None  # 备注信息

    def __post_init__(self):
        """初始化后处理"""
        if self.rule_params is None:
            self.rule_params = {}
        if self.timestamp and not self.date:
            self.date = self.timestamp.date()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "name": self.name,
            "signal_type": self.signal_type.value,
            "source": self.source.value,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "date": self.date.isoformat(),
            "quantity": self.quantity,
            "amount": self.amount,
            "rule_name": self.rule_name,
            "rule_params": self.rule_params,
            "strength": self.strength,
            "note": self.note,
        }

    def is_buy_signal(self) -> bool:
        """判断是否为买入信号"""
        return self.signal_type == SignalType.BUY

    def is_sell_signal(self) -> bool:
        """判断是否为卖出信号"""
        return self.signal_type in [SignalType.SELL, SignalType.CLOSE]

    def get_summary(self) -> str:
        """获取信号摘要"""
        return f"{self.signal_type.value} {self.name}({self.code}) @ {self.price:.2f} | 来源: {self.source.value} | 强度: {self.strength:.2f}"
