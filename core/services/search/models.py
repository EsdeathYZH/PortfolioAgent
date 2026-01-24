# -*- coding: utf-8 -*-
"""
搜索服务数据模型

从search_service.py迁移的SearchResult和SearchResponse类
"""

# 暂时保持向后兼容，直接导入原有实现
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from search_service import SearchResponse, SearchResult

# 导出以保持兼容
__all__ = ["SearchResult", "SearchResponse"]
