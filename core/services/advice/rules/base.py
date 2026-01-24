# -*- coding: utf-8 -*-
"""
投资建议规则基类

定义统一的规则接口，所有投资建议规则都应实现此接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from core.domain.advice import AdviceType, ConfidenceLevel, InvestmentAdvice


@dataclass
class RuleResult:
    """规则评估结果"""

    rule_name: str  # 规则名称
    advice_type: AdviceType  # 建议类型
    confidence: ConfidenceLevel  # 置信度
    score: int  # 评分 0-100
    reasons: list  # 理由列表
    risk_factors: list  # 风险因素列表
    metadata: Dict[str, Any]  # 元数据（可扩展）


class BaseRule(ABC):
    """
    投资建议规则基类

    所有投资建议规则都应继承此类并实现 evaluate 方法
    """

    def __init__(self, name: str, weight: float = 1.0):
        """
        初始化规则

        Args:
            name: 规则名称
            weight: 规则权重（用于聚合）
        """
        self.name = name
        self.weight = weight

    @abstractmethod
    def evaluate(
        self, asset_data: Dict[str, Any], indicators: Dict[str, Any], news_context: Optional[str] = None
    ) -> RuleResult:
        """
        评估规则并生成建议

        Args:
            asset_data: 资产数据（价格、成交量等）
            indicators: 技术指标（MA、量比、乖离率等）
            news_context: 新闻上下文（可选）

        Returns:
            RuleResult 规则评估结果
        """
        pass

    def get_weight(self) -> float:
        """获取规则权重"""
        return self.weight

    def set_weight(self, weight: float) -> None:
        """设置规则权重"""
        self.weight = weight
