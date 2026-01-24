# -*- coding: utf-8 -*-
"""
乖离率规则

基于乖离率判断是否追高，生成投资建议
核心逻辑：乖离率 > 5% 不买入（严进策略）
"""

from typing import Any, Dict, Optional

from core.domain.advice import AdviceType, ConfidenceLevel

from .base import BaseRule, RuleResult


class BiasRule(BaseRule):
    """
    乖离率规则

    基于价格与MA5的偏离度判断是否追高
    严进策略：乖离率超过 5% 不买入
    """

    BIAS_THRESHOLD = 5.0  # 乖离率阈值（%）

    def __init__(self, weight: float = 1.0):
        """
        初始化乖离率规则

        Args:
            weight: 规则权重（默认1.0）
        """
        super().__init__(name="乖离率规则", weight=weight)

    def evaluate(
        self, asset_data: Dict[str, Any], indicators: Dict[str, Any], news_context: Optional[str] = None
    ) -> RuleResult:
        """
        评估乖离率规则

        Args:
            asset_data: 资产数据
            indicators: 技术指标（需包含bias_ma5）
            news_context: 新闻上下文（可选）

        Returns:
            RuleResult 规则评估结果
        """
        bias_ma5 = indicators.get("bias_ma5", 0)
        current_price = asset_data.get("current_price", 0)
        ma5 = indicators.get("ma5", 0)

        reasons = []
        risk_factors = []
        score = 0
        advice_type = AdviceType.WAIT
        confidence = ConfidenceLevel.MEDIUM

        # 判断乖离率
        if bias_ma5 < 0:
            # 价格在 MA5 下方（回调中）
            if bias_ma5 > -3:
                score = 30
                advice_type = AdviceType.BUY
                confidence = ConfidenceLevel.HIGH
                reasons.append(f"✅ 价格略低于MA5({bias_ma5:.1f}%)，回踩买点")
            elif bias_ma5 > -5:
                score = 25
                advice_type = AdviceType.BUY
                confidence = ConfidenceLevel.MEDIUM
                reasons.append(f"✅ 价格回踩MA5({bias_ma5:.1f}%)，观察支撑")
            else:
                score = 10
                advice_type = AdviceType.WAIT
                confidence = ConfidenceLevel.MEDIUM
                risk_factors.append(f"⚠️ 乖离率过大({bias_ma5:.1f}%)，可能破位")

        elif bias_ma5 < 2:
            score = 28
            advice_type = AdviceType.BUY
            confidence = ConfidenceLevel.HIGH
            reasons.append(f"✅ 价格贴近MA5({bias_ma5:.1f}%)，介入好时机")

        elif bias_ma5 < self.BIAS_THRESHOLD:
            score = 20
            advice_type = AdviceType.BUY
            confidence = ConfidenceLevel.MEDIUM
            reasons.append(f"⚡ 价格略高于MA5({bias_ma5:.1f}%)，可小仓介入")

        else:
            score = 5
            advice_type = AdviceType.WAIT
            confidence = ConfidenceLevel.HIGH
            risk_factors.append(f"❌ 乖离率过高({bias_ma5:.1f}%>5%)，严禁追高！")

        return RuleResult(
            rule_name=self.name,
            advice_type=advice_type,
            confidence=confidence,
            score=score,
            reasons=reasons,
            risk_factors=risk_factors,
            metadata={
                "bias_ma5": bias_ma5,
                "current_price": current_price,
                "ma5": ma5,
            },
        )
