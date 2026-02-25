# -*- coding: utf-8 -*-
"""点金术分析领域模型。"""

from dataclasses import dataclass
from typing import Optional

BUY_MA120_BIAS_THRESHOLD = -12.0
BUY_DIVIDEND_YIELD_THRESHOLD = 3.0
BUY_PE_THRESHOLD = 20.0
SELL_MA120_BIAS_THRESHOLD = 12.0


@dataclass
class PointGoldAsset:
    """点金术股票池标的。"""

    name: str
    code: str
    group: str
    enabled: bool = True


@dataclass
class PointGoldSnapshot:
    """单只标的的当日策略快照。"""

    name: str
    code: str
    group: str
    price: Optional[float]
    ma120: Optional[float]
    bias_ma120_pct: Optional[float]
    pe: Optional[float]
    dividend_yield: Optional[float]
    dividend_method: str
    signal: str
    reason: str
