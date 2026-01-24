# -*- coding: utf-8 -*-
"""
A股自选股智能分析系统 - AI分析层（向后兼容）

此文件保持向后兼容，实际实现已迁移到 infrastructure/ai/ 和 core/domain/
"""

from core.domain.analysis import AnalysisResult

# 从新位置导入所有内容
from infrastructure.ai import STOCK_NAME_MAP, GeminiAnalyzer, get_analyzer

# 导出以保持向后兼容
__all__ = [
    "GeminiAnalyzer",
    "AnalysisResult",
    "STOCK_NAME_MAP",
    "get_analyzer",
]
