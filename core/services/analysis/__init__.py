# -*- coding: utf-8 -*-
"""
分析服务模块

从main.py、market_analyzer.py和stock_analyzer.py迁移的分析服务
"""

from .market_report import MarketAnalyzer, MarketIndex, MarketOverview
from .point_gold_report import PointGoldAnalysisPipeline
from .stock_report import (
    BuySignal,
    StockAnalysisPipeline,
    StockTrendAnalyzer,
    TrendAnalysisResult,
    TrendStatus,
    VolumeStatus,
    analyze_stock,
)

__all__ = [
    "StockAnalysisPipeline",
    "PointGoldAnalysisPipeline",
    "MarketAnalyzer",
    "MarketIndex",
    "MarketOverview",
    "StockTrendAnalyzer",
    "TrendAnalysisResult",
    "TrendStatus",
    "VolumeStatus",
    "BuySignal",
    "analyze_stock",
]
