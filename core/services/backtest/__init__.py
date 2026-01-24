# -*- coding: utf-8 -*-
"""
回测引擎

提供策略回测功能
"""

from .engine import BacktestEngine
from .executor import BacktestExecutor
from .metrics import BacktestMetrics
from .signal_generator import SignalGenerator

__all__ = [
    "BacktestEngine",
    "BacktestExecutor",
    "BacktestMetrics",
    "SignalGenerator",
]
