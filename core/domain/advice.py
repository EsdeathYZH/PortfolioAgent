# -*- coding: utf-8 -*-
"""
投资建议实体

定义投资建议的数据结构和相关方法
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AdviceType(Enum):
    """建议类型"""

    STRONG_BUY = "强烈买入"
    BUY = "买入"
    HOLD = "持有"
    REDUCE = "减仓"
    SELL = "卖出"
    STRONG_SELL = "强烈卖出"
    WAIT = "观望"


class ConfidenceLevel(Enum):
    """置信度等级"""

    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


@dataclass
class InvestmentAdvice:
    """
    投资建议实体

    包含完整的投资建议信息，用于生成交易决策
    """

    # 基本信息
    code: str  # 资产代码
    name: str  # 资产名称
    advice_type: AdviceType  # 建议类型
    confidence: ConfidenceLevel  # 置信度

    # 价格相关
    current_price: float  # 当前价格
    target_price: Optional[float] = None  # 目标价
    stop_loss_price: Optional[float] = None  # 止损价

    # 建议理由
    reasons: List[str] = field(default_factory=list)  # 买入/卖出理由
    risk_factors: List[str] = field(default_factory=list)  # 风险因素

    # 仓位建议
    suggested_position: Optional[str] = None  # 建议仓位（如"3成"、"轻仓"等）
    entry_plan: Optional[str] = None  # 建仓计划描述

    # 时间相关
    advice_date: date = field(default_factory=lambda: date.today())  # 建议日期
    valid_until: Optional[date] = None  # 有效期至
    time_sensitivity: str = "不急"  # 时间敏感性（立即行动/今日内/本周内/不急）

    # 评分
    score: int = 0  # 综合评分 0-100

    # 来源信息
    source: str = "系统分析"  # 建议来源
    rule_sources: List[str] = field(default_factory=list)  # 规则来源（如"趋势规则"、"乖离率规则"等）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "name": self.name,
            "advice_type": self.advice_type.value,
            "confidence": self.confidence.value,
            "current_price": self.current_price,
            "target_price": self.target_price,
            "stop_loss_price": self.stop_loss_price,
            "reasons": self.reasons,
            "risk_factors": self.risk_factors,
            "suggested_position": self.suggested_position,
            "entry_plan": self.entry_plan,
            "advice_date": self.advice_date.isoformat(),
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "time_sensitivity": self.time_sensitivity,
            "score": self.score,
            "source": self.source,
            "rule_sources": self.rule_sources,
        }

    def is_buy_advice(self) -> bool:
        """判断是否为买入建议"""
        return self.advice_type in [AdviceType.STRONG_BUY, AdviceType.BUY]

    def is_sell_advice(self) -> bool:
        """判断是否为卖出建议"""
        return self.advice_type in [AdviceType.STRONG_SELL, AdviceType.SELL, AdviceType.REDUCE]

    def is_hold_advice(self) -> bool:
        """判断是否为持有建议"""
        return self.advice_type == AdviceType.HOLD

    def is_wait_advice(self) -> bool:
        """判断是否为观望建议"""
        return self.advice_type == AdviceType.WAIT

    def get_emoji(self) -> str:
        """获取建议对应的emoji"""
        emoji_map = {
            AdviceType.STRONG_BUY: "🟢",
            AdviceType.BUY: "🟢",
            AdviceType.HOLD: "🟡",
            AdviceType.REDUCE: "🟠",
            AdviceType.SELL: "🔴",
            AdviceType.STRONG_SELL: "🔴",
            AdviceType.WAIT: "⚪",
        }
        return emoji_map.get(self.advice_type, "⚪")

    def get_summary(self) -> str:
        """获取建议摘要"""
        emoji = self.get_emoji()
        return f"{emoji} {self.name}({self.code}): {self.advice_type.value} | 评分 {self.score} | 置信度 {self.confidence.value}"
