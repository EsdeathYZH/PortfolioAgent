# -*- coding: utf-8 -*-
"""
===================================
A股自选股智能分析系统 - 存储层（向后兼容）
===================================

此文件保持向后兼容，实际实现已迁移到 infrastructure/data/
"""

# 从新位置导入所有内容
from infrastructure.data import Base, DatabaseManager, StockDaily, get_db

# 导出以保持向后兼容
__all__ = [
    "StockDaily",
    "Base",
    "DatabaseManager",
    "get_db",
]
