# -*- coding: utf-8 -*-
"""
大盘复盘分析模块（向后兼容）

此文件保持向后兼容，实际实现已迁移到 core/services/analysis/market_analyzer.py
"""

# 从新位置导入所有内容
from core.services.analysis import MarketAnalyzer, MarketIndex, MarketOverview

# 导出以保持向后兼容
__all__ = [
    "MarketAnalyzer",
    "MarketIndex",
    "MarketOverview",
]
