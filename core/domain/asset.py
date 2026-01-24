# -*- coding: utf-8 -*-
"""
资产抽象基类

定义统一的资产接口，支持多资产类型（股票、基金、债券等）
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional


@dataclass
class PriceData:
    """价格数据"""

    code: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    pct_chg: float  # 涨跌幅(%)


@dataclass
class IndicatorData:
    """技术指标数据"""

    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    volume_ratio: Optional[float] = None  # 量比
    bias_ma5: Optional[float] = None  # 乖离率
    rsi: Optional[float] = None
    macd: Optional[float] = None
    # 可扩展其他指标


@dataclass
class AssetMetadata:
    """资产元数据"""

    code: str
    name: str
    asset_type: str  # "stock", "fund", "bond", etc.
    market: str  # "A股", "港股", "美股", etc.
    sector: Optional[str] = None  # 行业/板块
    list_date: Optional[date] = None  # 上市日期
    # 可扩展其他元数据


class Asset(ABC):
    """
    资产抽象基类

    定义统一的资产接口，所有资产类型（股票、基金、债券等）都应实现此接口
    """

    def __init__(self, code: str, name: str):
        """
        初始化资产

        Args:
            code: 资产代码
            name: 资产名称
        """
        self.code = code
        self.name = name

    @abstractmethod
    def get_price_data(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[PriceData]:
        """
        获取价格数据

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选，默认今天）

        Returns:
            价格数据列表
        """
        pass

    @abstractmethod
    def get_indicators(self, target_date: Optional[date] = None) -> IndicatorData:
        """
        获取技术指标

        Args:
            target_date: 目标日期（可选，默认今天）

        Returns:
            技术指标数据
        """
        pass

    @abstractmethod
    def get_metadata(self) -> AssetMetadata:
        """
        获取资产元数据

        Returns:
            资产元数据
        """
        pass

    def get_latest_price(self) -> Optional[PriceData]:
        """
        获取最新价格数据（便捷方法）

        Returns:
            最新价格数据，如果不存在则返回None
        """
        price_data = self.get_price_data()
        return price_data[-1] if price_data else None

    def get_latest_indicators(self) -> Optional[IndicatorData]:
        """
        获取最新技术指标（便捷方法）

        Returns:
            最新技术指标，如果不存在则返回None
        """
        return self.get_indicators()

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（用于序列化）

        Returns:
            资产信息的字典表示
        """
        metadata = self.get_metadata()
        latest_price = self.get_latest_price()
        latest_indicators = self.get_latest_indicators()

        return {
            "code": self.code,
            "name": self.name,
            "metadata": (
                {
                    "asset_type": metadata.asset_type,
                    "market": metadata.market,
                    "sector": metadata.sector,
                    "list_date": metadata.list_date.isoformat() if metadata.list_date else None,
                }
                if metadata
                else None
            ),
            "latest_price": (
                {
                    "date": latest_price.date.isoformat() if latest_price else None,
                    "close": latest_price.close if latest_price else None,
                    "pct_chg": latest_price.pct_chg if latest_price else None,
                }
                if latest_price
                else None
            ),
            "latest_indicators": (
                {
                    "ma5": latest_indicators.ma5 if latest_indicators else None,
                    "ma10": latest_indicators.ma10 if latest_indicators else None,
                    "ma20": latest_indicators.ma20 if latest_indicators else None,
                    "bias_ma5": latest_indicators.bias_ma5 if latest_indicators else None,
                }
                if latest_indicators
                else None
            ),
        }


class StockAsset(Asset):
    """
    股票资产实现（示例）

    这是一个示例实现，展示如何实现Asset接口
    实际使用时，应该从数据源获取数据
    """

    def __init__(self, code: str, name: str, market: str = "A股"):
        """
        初始化股票资产

        Args:
            code: 股票代码
            name: 股票名称
            market: 市场类型（A股、港股、美股等）
        """
        super().__init__(code, name)
        self.market = market
        self._price_cache: Dict[date, PriceData] = {}
        self._indicator_cache: Dict[date, IndicatorData] = {}

    def get_price_data(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[PriceData]:
        """
        获取股票价格数据

        注意：这是一个示例实现，实际应该从数据源获取
        """
        # TODO: 从数据源获取价格数据
        # 这里返回空列表作为示例
        return []

    def get_indicators(self, target_date: Optional[date] = None) -> IndicatorData:
        """
        获取股票技术指标

        注意：这是一个示例实现，实际应该从数据源获取或计算
        """
        # TODO: 从数据源获取或计算技术指标
        # 这里返回空指标作为示例
        return IndicatorData()

    def get_metadata(self) -> AssetMetadata:
        """
        获取股票元数据

        注意：这是一个示例实现，实际应该从数据源获取
        """
        return AssetMetadata(
            code=self.code,
            name=self.name,
            asset_type="stock",
            market=self.market,
            sector=None,
            list_date=None,
        )
