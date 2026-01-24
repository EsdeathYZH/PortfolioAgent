# -*- coding: utf-8 -*-
"""
趋势跟踪策略

基于趋势分析生成交易信号
"""

from typing import Any, Dict, List

from core.domain.advice import AdviceType, InvestmentAdvice
from core.domain.signal import SignalSource, SignalType, TradingSignal

from .base import Strategy


class TrendFollowingStrategy(Strategy):
    """
    趋势跟踪策略

    基于趋势分析生成交易信号
    核心逻辑：多头排列买入，空头排列卖出
    """

    def __init__(self):
        """初始化趋势跟踪策略"""
        super().__init__(name="趋势跟踪策略")

    def generate_signals(
        self, advice: InvestmentAdvice, asset_data: Dict[str, Any], indicators: Dict[str, Any]
    ) -> List[TradingSignal]:
        """
        生成交易信号

        Args:
            advice: 投资建议
            asset_data: 资产数据
            indicators: 技术指标

        Returns:
            List[TradingSignal] 交易信号列表
        """
        signals = []

        # 根据建议类型生成信号
        if advice.advice_type in [AdviceType.STRONG_BUY, AdviceType.BUY]:
            # 买入信号
            signal = TradingSignal(
                code=advice.code,
                name=advice.name,
                signal_type=SignalType.BUY,
                source=SignalSource.SYSTEM,
                price=advice.current_price,
                timestamp=advice.advice_date,
                date=advice.advice_date,
                rule_name=self.name,
                rule_params={
                    "advice_type": advice.advice_type.value,
                    "score": advice.score,
                },
                strength=advice.score / 100.0,
                note=f"趋势跟踪策略：{advice.advice_type.value}",
            )
            signals.append(signal)

        elif advice.advice_type in [AdviceType.SELL, AdviceType.STRONG_SELL]:
            # 卖出信号
            signal = TradingSignal(
                code=advice.code,
                name=advice.name,
                signal_type=SignalType.SELL,
                source=SignalSource.SYSTEM,
                price=advice.current_price,
                timestamp=advice.advice_date,
                date=advice.advice_date,
                rule_name=self.name,
                rule_params={
                    "advice_type": advice.advice_type.value,
                    "score": advice.score,
                },
                strength=advice.score / 100.0,
                note=f"趋势跟踪策略：{advice.advice_type.value}",
            )
            signals.append(signal)

        return signals
