# -*- coding: utf-8 -*-
"""
投资建议规则库

定义各种投资建议规则
"""

from .base import BaseRule
from .bias_rule import BiasRule
from .risk_rule import RiskRule
from .support_rule import SupportRule
from .trend_rule import TrendRule
from .volume_rule import VolumeRule

__all__ = [
    "BaseRule",
    "TrendRule",
    "BiasRule",
    "VolumeRule",
    "SupportRule",
    "RiskRule",
]
