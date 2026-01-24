# -*- coding: utf-8 -*-
"""
趋势交易分析器（向后兼容）

此文件保持向后兼容，实际实现已迁移到 core/services/analysis/trend_analyzer.py
"""

# 从新位置导入所有内容
from core.services.analysis import (
    BuySignal,
    StockTrendAnalyzer,
    TrendAnalysisResult,
    TrendStatus,
    VolumeStatus,
    analyze_stock,
)

# 导出以保持向后兼容
__all__ = [
    "StockTrendAnalyzer",
    "TrendAnalysisResult",
    "TrendStatus",
    "VolumeStatus",
    "BuySignal",
    "analyze_stock",
]
