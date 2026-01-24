# -*- coding: utf-8 -*-
"""
搜索服务模块

从search_service.py迁移的搜索服务实现
"""

from .models import SearchResponse, SearchResult

# 导入新实现
from .service import SearchService, get_search_service, reset_search_service

# 导出以保持兼容
__all__ = [
    "SearchService",
    "get_search_service",
    "reset_search_service",
    "SearchResult",
    "SearchResponse",
]
