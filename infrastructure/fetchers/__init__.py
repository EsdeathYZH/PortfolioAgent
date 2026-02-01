# -*- coding: utf-8 -*-
"""
数据获取层

数据源策略层，实现统一的数据获取接口和自动故障切换
"""

from .akshare_fetcher import AkshareFetcher, ChipDistribution, RealtimeQuote
from .baostock_fetcher import BaostockFetcher
from .base import BaseFetcher, DataFetcherManager
from .efinance_fetcher import EfinanceFetcher
from .tushare_fetcher import TushareFetcher
from .yfinance_fetcher import YfinanceFetcher

__all__ = [
    "BaseFetcher",
    "DataFetcherManager",
    "AkshareFetcher",
    "BaostockFetcher",
    "EfinanceFetcher",
    "TushareFetcher",
    "YfinanceFetcher",
    "RealtimeQuote",
    "ChipDistribution",
]
