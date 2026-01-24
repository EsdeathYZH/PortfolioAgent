# -*- coding: utf-8 -*-
"""
领域模型

定义业务领域的核心实体和值对象
"""

from .advice import AdviceType, ConfidenceLevel, InvestmentAdvice

# 导入所有领域模型
from .analysis import AnalysisResult
from .asset import Asset, AssetMetadata, IndicatorData, PriceData, StockAsset
from .market import MarketIndex, MarketOverview, MarketStatistics, MarketStatus, SectorRanking
from .signal import SignalSource, SignalType, TradingSignal

__all__ = [
    # 分析结果
    "AnalysisResult",
    # 资产
    "Asset",
    "StockAsset",
    "PriceData",
    "IndicatorData",
    "AssetMetadata",
    # 投资建议
    "InvestmentAdvice",
    "AdviceType",
    "ConfidenceLevel",
    # 交易信号
    "TradingSignal",
    "SignalType",
    "SignalSource",
    # 市场数据
    "MarketIndex",
    "MarketStatistics",
    "SectorRanking",
    "MarketOverview",
    "MarketStatus",
]
