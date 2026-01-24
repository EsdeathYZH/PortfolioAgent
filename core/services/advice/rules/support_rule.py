# -*- coding: utf-8 -*-
"""
支撑规则

基于均线支撑位生成投资建议
核心逻辑：回踩 MA5/MA10 获得支撑是好的买点
"""

from typing import Any, Dict, Optional

from core.domain.advice import AdviceType, ConfidenceLevel

from .base import BaseRule, RuleResult


class SupportRule(BaseRule):
    """
    支撑规则

    基于均线支撑位判断买点
    买点偏好：回踩 MA5/MA10 获得支撑
    """

    MA_SUPPORT_TOLERANCE = 0.02  # MA 支撑判断容忍度（2%）

    def __init__(self, weight: float = 1.0):
        """
        初始化支撑规则

        Args:
            weight: 规则权重（默认1.0）
        """
        super().__init__(name="支撑规则", weight=weight)

    def evaluate(
        self, asset_data: Dict[str, Any], indicators: Dict[str, Any], news_context: Optional[str] = None
    ) -> RuleResult:
        """
        评估支撑规则

        Args:
            asset_data: 资产数据
            indicators: 技术指标（需包含ma5, ma10, ma20）
            news_context: 新闻上下文（可选）

        Returns:
            RuleResult 规则评估结果
        """
        current_price = asset_data.get("current_price", 0)
        ma5 = indicators.get("ma5", 0)
        ma10 = indicators.get("ma10", 0)
        ma20 = indicators.get("ma20", 0)

        reasons = []
        risk_factors = []
        score = 0
        advice_type = AdviceType.WAIT
        confidence = ConfidenceLevel.MEDIUM

        # 检查是否在 MA5 附近获得支撑
        support_ma5 = False
        support_ma10 = False

        if ma5 > 0:
            ma5_distance = abs(current_price - ma5) / ma5
            if ma5_distance <= self.MA_SUPPORT_TOLERANCE and current_price >= ma5:
                support_ma5 = True
                score += 5
                reasons.append("✅ MA5支撑有效")

        # 检查是否在 MA10 附近获得支撑
        if ma10 > 0:
            ma10_distance = abs(current_price - ma10) / ma10
            if ma10_distance <= self.MA_SUPPORT_TOLERANCE and current_price >= ma10:
                support_ma10 = True
                score += 5
                reasons.append("✅ MA10支撑有效")

        # 判断建议类型
        if support_ma5 or support_ma10:
            advice_type = AdviceType.BUY
            confidence = ConfidenceLevel.HIGH
        elif ma20 > 0 and current_price < ma20:
            score = 0
            advice_type = AdviceType.SELL
            confidence = ConfidenceLevel.MEDIUM
            risk_factors.append("⚠️ 跌破MA20，趋势转弱")
        else:
            advice_type = AdviceType.HOLD
            confidence = ConfidenceLevel.MEDIUM

        return RuleResult(
            rule_name=self.name,
            advice_type=advice_type,
            confidence=confidence,
            score=score,
            reasons=reasons,
            risk_factors=risk_factors,
            metadata={
                "current_price": current_price,
                "ma5": ma5,
                "ma10": ma10,
                "ma20": ma20,
                "support_ma5": support_ma5,
                "support_ma10": support_ma10,
            },
        )
