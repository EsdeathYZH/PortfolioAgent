# -*- coding: utf-8 -*-
"""
数据获取层

从data_provider迁移的数据获取器
"""

# 从data_provider导入所有内容（保持兼容）
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data_provider import BaseFetcher, ChipDistribution, DataFetcherManager, RealtimeQuote

__all__ = [
    "DataFetcherManager",
    "BaseFetcher",
    "RealtimeQuote",
    "ChipDistribution",
]
