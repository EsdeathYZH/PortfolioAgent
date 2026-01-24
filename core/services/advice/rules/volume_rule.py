# -*- coding: utf-8 -*-
"""
量能规则

基于成交量分析生成投资建议
核心逻辑：偏好缩量回调，警惕放量下跌
"""

from typing import Any, Dict, Optional

from core.domain.advice import AdviceType, ConfidenceLevel

from .base import BaseRule, RuleResult


class VolumeRule(BaseRule):
    """
    量能规则

    基于成交量变化判断市场情绪
    偏好：缩量回调 > 放量上涨 > 缩量上涨 > 放量下跌
    """

    VOLUME_SHRINK_RATIO = 0.7  # 缩量判断阈值
    VOLUME_HEAVY_RATIO = 1.5  # 放量判断阈值

    def __init__(self, weight: float = 1.0):
        """
        初始化量能规则

        Args:
            weight: 规则权重（默认1.0）
        """
        super().__init__(name="量能规则", weight=weight)

    def evaluate(
        self, asset_data: Dict[str, Any], indicators: Dict[str, Any], news_context: Optional[str] = None
    ) -> RuleResult:
        """
        评估量能规则

        Args:
            asset_data: 资产数据（需包含price_change_pct）
            indicators: 技术指标（需包含volume_ratio）
            news_context: 新闻上下文（可选）

        Returns:
            RuleResult 规则评估结果
        """
        volume_ratio = indicators.get("volume_ratio", 1.0)
        price_change_pct = asset_data.get("price_change_pct", 0)

        reasons = []
        risk_factors = []
        score = 0
        advice_type = AdviceType.WAIT
        confidence = ConfidenceLevel.MEDIUM

        # 判断量能状态
        if volume_ratio >= self.VOLUME_HEAVY_RATIO:
            # 放量
            if price_change_pct > 0:
                # 放量上涨
                score = 15
                advice_type = AdviceType.BUY
                confidence = ConfidenceLevel.MEDIUM
                reasons.append("✅ 放量上涨，多头力量强劲")
            else:
                # 放量下跌
                score = 0
                advice_type = AdviceType.SELL
                confidence = ConfidenceLevel.HIGH
                risk_factors.append("⚠️ 放量下跌，注意风险")

        elif volume_ratio <= self.VOLUME_SHRINK_RATIO:
            # 缩量
            if price_change_pct > 0:
                # 缩量上涨
                score = 8
                advice_type = AdviceType.HOLD
                confidence = ConfidenceLevel.LOW
                reasons.append("⚪ 缩量上涨，上攻动能不足")
            else:
                # 缩量回调（最佳）
                score = 20
                advice_type = AdviceType.BUY
                confidence = ConfidenceLevel.HIGH
                reasons.append("✅ 缩量回调，洗盘特征明显（好）")

        else:
            # 量能正常
            score = 12
            advice_type = AdviceType.HOLD
            confidence = ConfidenceLevel.MEDIUM
            reasons.append("⚪ 量能正常")

        return RuleResult(
            rule_name=self.name,
            advice_type=advice_type,
            confidence=confidence,
            score=score,
            reasons=reasons,
            risk_factors=risk_factors,
            metadata={
                "volume_ratio": volume_ratio,
                "price_change_pct": price_change_pct,
            },
        )
