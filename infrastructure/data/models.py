# -*- coding: utf-8 -*-
"""
数据模型定义

从storage.py迁移的ORM模型
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, Date, DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base

# SQLAlchemy ORM 基类
Base = declarative_base()


class StockDaily(Base):
    """
    股票日线数据模型

    存储每日行情数据和计算的技术指标
    支持多股票、多日期的唯一约束
    """

    __tablename__ = "stock_daily"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 股票代码（如 600519, 000001）
    code = Column(String(10), nullable=False, index=True)

    # 交易日期
    date = Column(Date, nullable=False, index=True)

    # OHLC 数据
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)

    # 成交数据
    volume = Column(Float)  # 成交量（股）
    amount = Column(Float)  # 成交额（元）
    pct_chg = Column(Float)  # 涨跌幅（%）

    # 技术指标
    ma5 = Column(Float)
    ma10 = Column(Float)
    ma20 = Column(Float)
    volume_ratio = Column(Float)  # 量比

    # 数据来源
    data_source = Column(String(50))  # 记录数据来源（如 AkshareFetcher）

    # 更新时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 唯一约束：同一股票同一日期只能有一条数据
    __table_args__ = (
        UniqueConstraint("code", "date", name="uix_code_date"),
        Index("ix_code_date", "code", "date"),
    )

    def __repr__(self):
        return f"<StockDaily(code={self.code}, date={self.date}, close={self.close})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "date": self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "amount": self.amount,
            "pct_chg": self.pct_chg,
            "ma5": self.ma5,
            "ma10": self.ma10,
            "ma20": self.ma20,
            "volume_ratio": self.volume_ratio,
            "data_source": self.data_source,
        }
