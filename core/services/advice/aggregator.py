# -*- coding: utf-8 -*-
"""
规则聚合器

综合多个规则的结果，生成最终投资建议
"""

from datetime import date
from typing import Any, Dict, List, Optional

from core.domain.advice import AdviceType, ConfidenceLevel, InvestmentAdvice

from .rules.base import RuleResult


class RuleAggregator:
    """
    规则聚合器

    综合多个规则的结果，生成最终投资建议
    """

    def __init__(self):
        """初始化聚合器"""
        pass

    def aggregate(
        self,
        rule_results: List[RuleResult],
        code: str,
        name: str,
        current_price: float,
        rule_weights: Optional[Dict[str, float]] = None,
    ) -> InvestmentAdvice:
        """
        聚合多个规则的结果，生成最终投资建议

        Args:
            rule_results: 规则评估结果列表
            code: 资产代码
            name: 资产名称
            current_price: 当前价格
            rule_weights: 规则权重字典（可选），格式：{规则名称: 权重值}

        Returns:
            InvestmentAdvice 最终投资建议
        """
        if not rule_results:
            # 无规则结果，返回观望建议
            return InvestmentAdvice(
                code=code,
                name=name,
                advice_type=AdviceType.WAIT,
                confidence=ConfidenceLevel.LOW,
                current_price=current_price,
                reasons=["无规则评估结果"],
            )

        # 计算加权总分
        total_score = 0
        total_weight = 0

        all_reasons = []
        all_risk_factors = []
        rule_sources = []

        # 统计各建议类型的投票
        advice_votes: Dict[AdviceType, float] = {}
        confidence_votes: Dict[ConfidenceLevel, float] = {}

        for result in rule_results:
            # 从rule_weights字典获取权重，如果没有则使用默认权重1.0
            rule_weight = (rule_weights or {}).get(result.rule_name, 1.0)

            # 加权评分
            total_score += result.score * rule_weight
            total_weight += rule_weight

            # 收集理由和风险
            all_reasons.extend(result.reasons)
            all_risk_factors.extend(result.risk_factors)
            rule_sources.append(result.rule_name)

            # 投票统计
            advice_votes[result.advice_type] = advice_votes.get(result.advice_type, 0) + rule_weight
            confidence_votes[result.confidence] = confidence_votes.get(result.confidence, 0) + rule_weight

        # 计算平均分
        final_score = int(total_score / total_weight) if total_weight > 0 else 0

        # 选择得票最多的建议类型
        final_advice_type = max(advice_votes.items(), key=lambda x: x[1])[0] if advice_votes else AdviceType.WAIT

        # 选择得票最多的置信度
        final_confidence = (
            max(confidence_votes.items(), key=lambda x: x[1])[0] if confidence_votes else ConfidenceLevel.MEDIUM
        )

        # 根据评分调整建议类型
        if final_score >= 80:
            final_advice_type = AdviceType.STRONG_BUY
        elif final_score >= 65:
            if final_advice_type not in [AdviceType.STRONG_BUY, AdviceType.BUY]:
                final_advice_type = AdviceType.BUY
        elif final_score >= 50:
            if final_advice_type in [AdviceType.SELL, AdviceType.STRONG_SELL]:
                final_advice_type = AdviceType.HOLD
        elif final_score >= 35:
            final_advice_type = AdviceType.WAIT
        else:
            if final_advice_type not in [AdviceType.SELL, AdviceType.STRONG_SELL]:
                final_advice_type = AdviceType.SELL

        # 生成投资建议
        advice = InvestmentAdvice(
            code=code,
            name=name,
            advice_type=final_advice_type,
            confidence=final_confidence,
            current_price=current_price,
            score=final_score,
            reasons=all_reasons,
            risk_factors=all_risk_factors,
            rule_sources=rule_sources,
            source="投资建议引擎",
            advice_date=date.today(),
        )

        return advice
