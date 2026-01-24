# -*- coding: utf-8 -*-
"""
搜索引擎提供者模块
"""

# 暂时保持向后兼容
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导出原有接口以保持兼容
from search_service import BaseSearchProvider, BochaSearchProvider, SerpAPISearchProvider, TavilySearchProvider

__all__ = [
    "BaseSearchProvider",
    "TavilySearchProvider",
    "SerpAPISearchProvider",
    "BochaSearchProvider",
]
