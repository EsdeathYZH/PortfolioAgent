# -*- coding: utf-8 -*-
"""
市场数据实体

定义市场相关的数据结构和实体
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MarketStatus(Enum):
    """市场状态"""

    TRADING = "交易中"
    CLOSED = "已收盘"
    SUSPENDED = "停牌"
    HOLIDAY = "休市"


@dataclass
class MarketIndex:
    """市场指数数据"""

    code: str  # 指数代码
    name: str  # 指数名称
    current: float  # 当前点位
    change: float  # 涨跌点数
    change_pct: float  # 涨跌幅(%)
    open: float  # 开盘点位
    high: float  # 最高点位
    low: float  # 最低点位
    prev_close: float  # 昨收点位
    volume: float  # 成交量
    amount: float  # 成交额
    amplitude: float  # 振幅(%)
    date: date = field(default_factory=lambda: date.today())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "name": self.name,
            "current": self.current,
            "change": self.change,
            "change_pct": self.change_pct,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "prev_close": self.prev_close,
            "volume": self.volume,
            "amount": self.amount,
            "amplitude": self.amplitude,
            "date": self.date.isoformat(),
        }


@dataclass
class MarketStatistics:
    """市场统计"""

    date: date
    up_count: int = 0  # 上涨家数
    down_count: int = 0  # 下跌家数
    flat_count: int = 0  # 平盘家数
    limit_up_count: int = 0  # 涨停家数
    limit_down_count: int = 0  # 跌停家数
    total_amount: float = 0.0  # 总成交额（亿元）
    north_flow: float = 0.0  # 北向资金净流入（亿元）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "date": self.date.isoformat(),
            "up_count": self.up_count,
            "down_count": self.down_count,
            "flat_count": self.flat_count,
            "limit_up_count": self.limit_up_count,
            "limit_down_count": self.limit_down_count,
            "total_amount": self.total_amount,
            "north_flow": self.north_flow,
        }


@dataclass
class SectorRanking:
    """板块排名"""

    name: str  # 板块名称
    change_pct: float  # 涨跌幅(%)
    amount: float  # 成交额（亿元）
    up_count: int = 0  # 上涨家数
    down_count: int = 0  # 下跌家数

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "change_pct": self.change_pct,
            "amount": self.amount,
            "up_count": self.up_count,
            "down_count": self.down_count,
        }


@dataclass
class MarketOverview:
    """市场概览"""

    date: date
    status: MarketStatus = MarketStatus.CLOSED
    indices: List[MarketIndex] = field(default_factory=list)  # 主要指数
    statistics: Optional[MarketStatistics] = None  # 市场统计
    top_sectors: List[SectorRanking] = field(default_factory=list)  # 涨幅前5板块
    bottom_sectors: List[SectorRanking] = field(default_factory=list)  # 跌幅前5板块

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "date": self.date.isoformat(),
            "status": self.status.value,
            "indices": [idx.to_dict() for idx in self.indices],
            "statistics": self.statistics.to_dict() if self.statistics else None,
            "top_sectors": [s.to_dict() for s in self.top_sectors],
            "bottom_sectors": [s.to_dict() for s in self.bottom_sectors],
        }
