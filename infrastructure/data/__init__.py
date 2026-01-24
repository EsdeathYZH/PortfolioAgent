# -*- coding: utf-8 -*-
"""
数据存储模块

从storage.py迁移的数据存储实现
"""

# 导出模型和数据库管理器
from .models import Base, StockDaily
from .storage import DatabaseManager, get_db

__all__ = [
    "StockDaily",
    "Base",
    "DatabaseManager",
    "get_db",
]
