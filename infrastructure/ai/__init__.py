# -*- coding: utf-8 -*-
"""
AI分析模块

从analyzer.py迁移的AI分析器实现
"""

# 从领域模型导入AnalysisResult
from core.domain.analysis import AnalysisResult

# 导入新实现
from .gemini import STOCK_NAME_MAP, GeminiAnalyzer, get_analyzer

# 导出以保持兼容
__all__ = [
    "GeminiAnalyzer",
    "get_analyzer",
    "AnalysisResult",
    "STOCK_NAME_MAP",
]
