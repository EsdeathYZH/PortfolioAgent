# -*- coding: utf-8 -*-
"""
趋势规则

基于均线排列和趋势强度生成投资建议
从StockTrendAnalyzer的趋势分析逻辑迁移
"""

from typing import Any, Dict, Optional

from core.domain.advice import AdviceType, ConfidenceLevel

from .base import BaseRule, RuleResult


class TrendRule(BaseRule):
    """
    趋势规则

    基于均线排列判断趋势，生成投资建议
    核心逻辑：MA5>MA10>MA20 多头排列
    """

    def __init__(self, weight: float = 1.0):
        """
        初始化趋势规则

        Args:
            weight: 规则权重（默认1.0）
        """
        super().__init__(name="趋势规则", weight=weight)

    def evaluate(
        self, asset_data: Dict[str, Any], indicators: Dict[str, Any], news_context: Optional[str] = None
    ) -> RuleResult:
        """
        评估趋势规则

        Args:
            asset_data: 资产数据
            indicators: 技术指标（需包含ma5, ma10, ma20）
            news_context: 新闻上下文（可选）

        Returns:
            RuleResult 规则评估结果
        """
        ma5 = indicators.get("ma5", 0)
        ma10 = indicators.get("ma10", 0)
        ma20 = indicators.get("ma20", 0)
        current_price = asset_data.get("current_price", 0)

        reasons = []
        risk_factors = []
        score = 0
        advice_type = AdviceType.WAIT
        confidence = ConfidenceLevel.MEDIUM

        # 判断均线排列
        if ma5 > ma10 > ma20 and ma20 > 0:
            # 多头排列
            # 检查间距是否在扩大（强势）
            spread = (ma5 - ma20) / ma20 * 100 if ma20 > 0 else 0

            if spread > 5:
                # 强势多头
                score = 40
                advice_type = AdviceType.BUY
                confidence = ConfidenceLevel.HIGH
                reasons.append("✅ 强势多头排列，均线发散上行")
            else:
                # 普通多头
                score = 35
                advice_type = AdviceType.BUY
                confidence = ConfidenceLevel.MEDIUM
                reasons.append("✅ 多头排列 MA5>MA10>MA20")

        elif ma5 > ma10 and ma10 <= ma20:
            # 弱势多头
            score = 25
            advice_type = AdviceType.HOLD
            confidence = ConfidenceLevel.MEDIUM
            reasons.append("⚠️ 弱势多头，MA5>MA10 但 MA10≤MA20")

        elif ma5 < ma10 < ma20 and ma5 > 0:
            # 空头排列
            spread = (ma20 - ma5) / ma5 * 100 if ma5 > 0 else 0

            if spread > 5:
                # 强势空头
                score = 0
                advice_type = AdviceType.STRONG_SELL
                confidence = ConfidenceLevel.HIGH
                risk_factors.append("❌ 强势空头排列，均线发散下行")
            else:
                # 普通空头
                score = 5
                advice_type = AdviceType.SELL
                confidence = ConfidenceLevel.MEDIUM
                risk_factors.append("❌ 空头排列 MA5<MA10<MA20")

        elif ma5 < ma10 and ma10 >= ma20:
            # 弱势空头
            score = 10
            advice_type = AdviceType.HOLD
            confidence = ConfidenceLevel.MEDIUM
            risk_factors.append("⚠️ 弱势空头，MA5<MA10 但 MA10≥MA20")

        else:
            # 均线缠绕
            score = 15
            advice_type = AdviceType.WAIT
            confidence = ConfidenceLevel.LOW
            reasons.append("⚪ 均线缠绕，趋势不明")

        return RuleResult(
            rule_name=self.name,
            advice_type=advice_type,
            confidence=confidence,
            score=score,
            reasons=reasons,
            risk_factors=risk_factors,
            metadata={
                "ma5": ma5,
                "ma10": ma10,
                "ma20": ma20,
                "current_price": current_price,
            },
        )
