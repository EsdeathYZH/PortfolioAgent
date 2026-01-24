# -*- coding: utf-8 -*-
"""
风险规则

基于新闻和风险因素生成投资建议
核心逻辑：识别重大利空，降低建议评分
"""

import re
from typing import Any, Dict, List, Optional

from core.domain.advice import AdviceType, ConfidenceLevel

from .base import BaseRule, RuleResult


class RiskRule(BaseRule):
    """
    风险规则

    基于新闻和风险因素判断投资风险
    重点关注：减持、处罚、业绩变脸等
    """

    # 风险关键词
    RISK_KEYWORDS = [
        "减持",
        "减持公告",
        "股东减持",
        "高管减持",
        "处罚",
        "立案调查",
        "监管处罚",
        "业绩预亏",
        "业绩下滑",
        "业绩变脸",
        "大额解禁",
        "限售股解禁",
        "退市风险",
        "ST",
        "*ST",
        "重大利空",
        "负面消息",
    ]

    # 利好关键词（可以抵消部分风险）
    POSITIVE_KEYWORDS = [
        "业绩预增",
        "业绩超预期",
        "增持",
        "回购",
        "合同",
        "订单",
        "中标",
        "利好",
        "重大利好",
    ]

    def __init__(self, weight: float = 1.0):
        """
        初始化风险规则

        Args:
            weight: 规则权重（默认1.0）
        """
        super().__init__(name="风险规则", weight=weight)

    def evaluate(
        self, asset_data: Dict[str, Any], indicators: Dict[str, Any], news_context: Optional[str] = None
    ) -> RuleResult:
        """
        评估风险规则

        Args:
            asset_data: 资产数据
            indicators: 技术指标
            news_context: 新闻上下文（重要）

        Returns:
            RuleResult 规则评估结果
        """
        reasons = []
        risk_factors = []
        score = 10  # 基础分（无风险时）
        advice_type = AdviceType.HOLD
        confidence = ConfidenceLevel.MEDIUM

        if not news_context:
            # 无新闻上下文，默认无风险
            return RuleResult(
                rule_name=self.name,
                advice_type=advice_type,
                confidence=confidence,
                score=score,
                reasons=reasons,
                risk_factors=risk_factors,
                metadata={"news_analyzed": False},
            )

        # 分析新闻中的风险因素
        risk_count = 0
        positive_count = 0

        news_lower = news_context.lower()

        for keyword in self.RISK_KEYWORDS:
            if keyword in news_lower:
                risk_count += 1
                risk_factors.append(f"⚠️ 发现风险关键词：{keyword}")

        for keyword in self.POSITIVE_KEYWORDS:
            if keyword in news_lower:
                positive_count += 1
                reasons.append(f"✅ 发现利好关键词：{keyword}")

        # 计算风险评分
        if risk_count > 0:
            # 有风险因素，降低评分
            score = max(0, 10 - risk_count * 3)

            if risk_count >= 2:
                advice_type = AdviceType.SELL
                confidence = ConfidenceLevel.HIGH
            elif risk_count == 1:
                advice_type = AdviceType.WAIT
                confidence = ConfidenceLevel.MEDIUM
        else:
            # 无风险因素
            if positive_count > 0:
                score = 15  # 有利好，加分
                advice_type = AdviceType.BUY
                confidence = ConfidenceLevel.MEDIUM

        return RuleResult(
            rule_name=self.name,
            advice_type=advice_type,
            confidence=confidence,
            score=score,
            reasons=reasons,
            risk_factors=risk_factors,
            metadata={
                "news_analyzed": True,
                "risk_count": risk_count,
                "positive_count": positive_count,
            },
        )
