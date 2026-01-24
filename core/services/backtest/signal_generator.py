# -*- coding: utf-8 -*-
"""
信号生成器

将投资建议转换为交易信号
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from core.domain.advice import AdviceType, InvestmentAdvice
from core.domain.signal import SignalSource, SignalType, TradingSignal


class SignalGenerationStrategy(Enum):
    """信号生成策略"""

    IMMEDIATE = "立即执行"  # 立即生成信号
    DELAYED = "延迟执行"  # 延迟N天后生成信号
    CONDITIONAL = "条件触发"  # 满足条件时生成信号


class SignalGenerator:
    """
    信号生成器

    将投资建议（Advice）转换为交易信号（Signal）
    支持不同的信号生成策略
    """

    def __init__(self, strategy: SignalGenerationStrategy = SignalGenerationStrategy.IMMEDIATE):
        """
        初始化信号生成器

        Args:
            strategy: 信号生成策略
        """
        self.strategy = strategy

    def generate_from_advice(
        self, advice: InvestmentAdvice, source: SignalSource = SignalSource.SYSTEM
    ) -> Optional[TradingSignal]:
        """
        从投资建议生成交易信号

        Args:
            advice: 投资建议
            source: 信号来源

        Returns:
            TradingSignal 交易信号，如果不应该生成信号则返回None
        """
        # 根据建议类型决定信号类型
        signal_type = self._map_advice_to_signal(advice.advice_type)

        if signal_type is None:
            # 不需要生成信号（如WAIT、HOLD）
            return None

        # 生成交易信号
        signal = TradingSignal(
            code=advice.code,
            name=advice.name,
            signal_type=signal_type,
            source=source,
            price=advice.current_price,
            timestamp=datetime.now(),
            date=advice.advice_date,
            rule_name=advice.source,
            rule_params={
                "advice_type": advice.advice_type.value,
                "confidence": advice.confidence.value,
                "score": advice.score,
            },
            strength=self._calculate_strength(advice),
            note=f"基于投资建议生成，评分: {advice.score}",
        )

        return signal

    def _map_advice_to_signal(self, advice_type: AdviceType) -> Optional[SignalType]:
        """
        将建议类型映射到信号类型

        Args:
            advice_type: 建议类型

        Returns:
            SignalType 信号类型，如果不应该生成信号则返回None
        """
        mapping = {
            AdviceType.STRONG_BUY: SignalType.BUY,
            AdviceType.BUY: SignalType.BUY,
            AdviceType.HOLD: None,  # 持有不生成信号
            AdviceType.REDUCE: SignalType.SELL,
            AdviceType.SELL: SignalType.SELL,
            AdviceType.STRONG_SELL: SignalType.SELL,
            AdviceType.WAIT: None,  # 观望不生成信号
        }
        return mapping.get(advice_type)

    def _calculate_strength(self, advice: InvestmentAdvice) -> float:
        """
        计算信号强度

        Args:
            advice: 投资建议

        Returns:
            float 信号强度 0.0-1.0
        """
        # 基于评分和置信度计算强度
        score_factor = min(advice.score / 100.0, 1.0)

        confidence_factors = {
            "高": 1.0,
            "中": 0.7,
            "低": 0.4,
        }
        confidence_factor = confidence_factors.get(advice.confidence.value, 0.5)

        return score_factor * confidence_factor

    def generate_batch(
        self, advice_list: List[InvestmentAdvice], source: SignalSource = SignalSource.SYSTEM
    ) -> List[TradingSignal]:
        """
        批量生成交易信号

        Args:
            advice_list: 投资建议列表
            source: 信号来源

        Returns:
            List[TradingSignal] 交易信号列表
        """
        signals = []
        for advice in advice_list:
            signal = self.generate_from_advice(advice, source)
            if signal:
                signals.append(signal)
        return signals
