# -*- coding: utf-8 -*-
"""
投资建议引擎

综合多个规则生成投资建议
"""

from typing import Any, Dict, List, Optional

from core.domain.advice import AdviceType, ConfidenceLevel, InvestmentAdvice
from core.domain.asset import Asset

from .aggregator import RuleAggregator
from .rules.base import BaseRule
from .rules.bias_rule import BiasRule
from .rules.risk_rule import RiskRule
from .rules.support_rule import SupportRule
from .rules.trend_rule import TrendRule
from .rules.volume_rule import VolumeRule


class AdviceEngine:
    """
    投资建议引擎

    综合多个规则生成投资建议
    """

    def __init__(self, rules: Optional[List[BaseRule]] = None):
        """
        初始化建议引擎

        Args:
            rules: 规则列表（可选，默认使用内置规则）
        """
        if rules is None:
            # 使用默认规则
            self.rules = [
                TrendRule(weight=1.0),  # 趋势规则（权重40%）
                BiasRule(weight=1.0),  # 乖离率规则（权重30%）
                VolumeRule(weight=1.0),  # 量能规则（权重20%）
                SupportRule(weight=1.0),  # 支撑规则（权重10%）
                RiskRule(weight=1.0),  # 风险规则（权重10%）
            ]
        else:
            self.rules = rules

        self.aggregator = RuleAggregator()

    def generate_advice(self, asset: Asset, news_context: Optional[str] = None) -> InvestmentAdvice:
        """
        生成投资建议

        Args:
            asset: 资产对象
            news_context: 新闻上下文（可选）

        Returns:
            InvestmentAdvice 投资建议
        """
        # 获取资产数据
        latest_price = asset.get_latest_price()
        latest_indicators = asset.get_latest_indicators()

        if not latest_price or not latest_indicators:
            # 数据不足，返回观望建议
            return InvestmentAdvice(
                code=asset.code,
                name=asset.name,
                advice_type=AdviceType.WAIT,
                confidence=ConfidenceLevel.LOW,
                current_price=0,
                reasons=["数据不足，无法生成建议"],
            )

        # 准备数据
        asset_data = {
            "current_price": latest_price.close,
            "price_change_pct": latest_price.pct_chg,
        }

        indicators = {
            "ma5": latest_indicators.ma5,
            "ma10": latest_indicators.ma10,
            "ma20": latest_indicators.ma20,
            "bias_ma5": latest_indicators.bias_ma5,
            "volume_ratio": latest_indicators.volume_ratio,
        }

        # 执行所有规则
        rule_results = []
        for rule in self.rules:
            try:
                result = rule.evaluate(asset_data, indicators, news_context)
                rule_results.append(result)
            except Exception as e:
                # 规则执行失败，跳过
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"规则 {rule.name} 执行失败: {e}")
                continue

        # 准备规则权重映射
        rule_weights = {rule.name: rule.get_weight() for rule in self.rules}

        # 聚合规则结果
        advice = self.aggregator.aggregate(
            rule_results=rule_results,
            code=asset.code,
            name=asset.name,
            current_price=latest_price.close,
            rule_weights=rule_weights,
        )

        return advice

    def generate_advice_from_data(
        self,
        code: str,
        name: str,
        asset_data: Dict[str, Any],
        indicators: Dict[str, Any],
        news_context: Optional[str] = None,
    ) -> InvestmentAdvice:
        """
        从数据生成投资建议（便捷方法）

        Args:
            code: 资产代码
            name: 资产名称
            asset_data: 资产数据字典
            indicators: 技术指标字典
            news_context: 新闻上下文（可选）

        Returns:
            InvestmentAdvice 投资建议
        """
        # 执行所有规则
        rule_results = []
        for rule in self.rules:
            try:
                result = rule.evaluate(asset_data, indicators, news_context)
                rule_results.append(result)
            except Exception as e:
                # 规则执行失败，跳过
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"规则 {rule.name} 执行失败: {e}")
                continue

        # 准备规则权重映射
        rule_weights = {rule.name: rule.get_weight() for rule in self.rules}

        # 聚合规则结果
        current_price = asset_data.get("current_price", 0)
        advice = self.aggregator.aggregate(
            rule_results=rule_results, code=code, name=name, current_price=current_price, rule_weights=rule_weights
        )

        return advice
