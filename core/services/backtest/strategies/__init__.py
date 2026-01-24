# -*- coding: utf-8 -*-
"""
回测策略

定义各种回测策略
"""

from .base import Strategy
from .trend_following import TrendFollowingStrategy

__all__ = [
    "Strategy",
    "TrendFollowingStrategy",
]
