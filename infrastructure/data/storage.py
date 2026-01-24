# -*- coding: utf-8 -*-
"""
数据库管理器

从storage.py迁移的DatabaseManager类和get_db函数
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import and_, create_engine, desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from shared.config import get_config

from .models import Base, StockDaily

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    数据库管理器 - 单例模式

    职责：
    1. 管理数据库连接池
    2. 提供 Session 上下文管理
    3. 封装数据存取操作
    """

    _instance: Optional["DatabaseManager"] = None

    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_url: Optional[str] = None):
        """
        初始化数据库管理器

        Args:
            db_url: 数据库连接 URL（可选，默认从配置读取）
        """
        if self._initialized:
            return

        if db_url is None:
            config = get_config()
            db_url = config.get_db_url()

        # 创建数据库引擎
        self._engine = create_engine(
            db_url,
            echo=False,  # 设为 True 可查看 SQL 语句
            pool_pre_ping=True,  # 连接健康检查
        )

        # 创建 Session 工厂
        self._SessionLocal = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
        )

        # 创建所有表
        Base.metadata.create_all(self._engine)

        self._initialized = True
        logger.info(f"数据库初始化完成: {db_url}")

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（用于测试）"""
        if cls._instance is not None:
            cls._instance._engine.dispose()
            cls._instance = None

    def get_session(self) -> Session:
        """
        获取数据库 Session

        使用示例:
            with db.get_session() as session:
                # 执行查询
                session.commit()  # 如果需要
        """
        session = self._SessionLocal()
        try:
            return session
        except Exception:
            session.close()
            raise

    def has_today_data(self, code: str, target_date: Optional[date] = None) -> bool:
        """
        检查是否已有指定日期的数据

        用于断点续传逻辑：如果已有数据则跳过网络请求

        Args:
            code: 股票代码
            target_date: 目标日期（默认今天）

        Returns:
            是否存在数据
        """
        if target_date is None:
            target_date = date.today()

        with self.get_session() as session:
            result = session.execute(
                select(StockDaily).where(and_(StockDaily.code == code, StockDaily.date == target_date))
            ).scalar_one_or_none()

            return result is not None

    def get_latest_data(self, code: str, days: int = 2) -> List[StockDaily]:
        """
        获取最近 N 天的数据

        用于计算"相比昨日"的变化

        Args:
            code: 股票代码
            days: 获取天数

        Returns:
            StockDaily 对象列表（按日期降序）
        """
        with self.get_session() as session:
            results = (
                session.execute(
                    select(StockDaily).where(StockDaily.code == code).order_by(desc(StockDaily.date)).limit(days)
                )
                .scalars()
                .all()
            )

            return list(results)

    def get_data_range(self, code: str, start_date: date, end_date: date) -> List[StockDaily]:
        """
        获取指定日期范围的数据

        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            StockDaily 对象列表
        """
        with self.get_session() as session:
            results = (
                session.execute(
                    select(StockDaily)
                    .where(and_(StockDaily.code == code, StockDaily.date >= start_date, StockDaily.date <= end_date))
                    .order_by(StockDaily.date)
                )
                .scalars()
                .all()
            )

            return list(results)

    def save_daily_data(self, df: pd.DataFrame, code: str, data_source: str = "Unknown") -> int:
        """
        保存日线数据到数据库

        策略：
        - 使用 UPSERT 逻辑（存在则更新，不存在则插入）
        - 跳过已存在的数据，避免重复

        Args:
            df: 包含日线数据的 DataFrame
            code: 股票代码
            data_source: 数据来源名称

        Returns:
            新增/更新的记录数
        """
        if df is None or df.empty:
            logger.warning(f"保存数据为空，跳过 {code}")
            return 0

        saved_count = 0

        with self.get_session() as session:
            try:
                for _, row in df.iterrows():
                    # 解析日期
                    row_date = row.get("date")
                    if isinstance(row_date, str):
                        row_date = datetime.strptime(row_date, "%Y-%m-%d").date()
                    elif isinstance(row_date, datetime):
                        row_date = row_date.date()
                    elif isinstance(row_date, pd.Timestamp):
                        row_date = row_date.date()

                    # 检查是否已存在
                    existing = session.execute(
                        select(StockDaily).where(and_(StockDaily.code == code, StockDaily.date == row_date))
                    ).scalar_one_or_none()

                    if existing:
                        # 更新现有记录
                        existing.open = row.get("open")
                        existing.high = row.get("high")
                        existing.low = row.get("low")
                        existing.close = row.get("close")
                        existing.volume = row.get("volume")
                        existing.amount = row.get("amount")
                        existing.pct_chg = row.get("pct_chg")
                        existing.ma5 = row.get("ma5")
                        existing.ma10 = row.get("ma10")
                        existing.ma20 = row.get("ma20")
                        existing.volume_ratio = row.get("volume_ratio")
                        existing.data_source = data_source
                        existing.updated_at = datetime.now()
                    else:
                        # 创建新记录
                        record = StockDaily(
                            code=code,
                            date=row_date,
                            open=row.get("open"),
                            high=row.get("high"),
                            low=row.get("low"),
                            close=row.get("close"),
                            volume=row.get("volume"),
                            amount=row.get("amount"),
                            pct_chg=row.get("pct_chg"),
                            ma5=row.get("ma5"),
                            ma10=row.get("ma10"),
                            ma20=row.get("ma20"),
                            volume_ratio=row.get("volume_ratio"),
                            data_source=data_source,
                        )
                        session.add(record)
                        saved_count += 1

                session.commit()
                logger.info(f"保存 {code} 数据成功，新增 {saved_count} 条")

            except Exception as e:
                session.rollback()
                logger.error(f"保存 {code} 数据失败: {e}")
                raise

        return saved_count

    def get_analysis_context(self, code: str, target_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        获取分析所需的上下文数据

        返回今日数据 + 昨日数据的对比信息

        Args:
            code: 股票代码
            target_date: 目标日期（默认今天）

        Returns:
            包含今日数据、昨日对比等信息的字典
        """
        if target_date is None:
            target_date = date.today()

        # 获取最近2天数据
        recent_data = self.get_latest_data(code, days=2)

        if not recent_data:
            logger.warning(f"未找到 {code} 的数据")
            return None

        today_data = recent_data[0]
        yesterday_data = recent_data[1] if len(recent_data) > 1 else None

        context = {
            "code": code,
            "date": today_data.date.isoformat(),
            "today": today_data.to_dict(),
        }

        if yesterday_data:
            context["yesterday"] = yesterday_data.to_dict()

            # 计算相比昨日的变化
            if yesterday_data.volume and yesterday_data.volume > 0:
                context["volume_change_ratio"] = round(today_data.volume / yesterday_data.volume, 2)

            if yesterday_data.close and yesterday_data.close > 0:
                context["price_change_ratio"] = round(
                    (today_data.close - yesterday_data.close) / yesterday_data.close * 100, 2
                )

            # 均线形态判断
            context["ma_status"] = self._analyze_ma_status(today_data)

        # 添加原始数据（用于趋势分析）
        raw_data = self.get_data_range(code, target_date - timedelta(days=30), target_date)
        context["raw_data"] = [record.to_dict() for record in raw_data]

        return context

    def _analyze_ma_status(self, data: StockDaily) -> str:
        """
        分析均线形态

        判断条件：
        - 多头排列：close > ma5 > ma10 > ma20
        - 空头排列：close < ma5 < ma10 < ma20
        - 震荡整理：其他情况
        """
        close = data.close or 0
        ma5 = data.ma5 or 0
        ma10 = data.ma10 or 0
        ma20 = data.ma20 or 0

        if close > ma5 > ma10 > ma20 > 0:
            return "多头排列 📈"
        elif close < ma5 < ma10 < ma20 and ma20 > 0:
            return "空头排列 📉"
        elif close > ma5 and ma5 > ma10:
            return "短期向好 🔼"
        elif close < ma5 and ma5 < ma10:
            return "短期走弱 🔽"
        else:
            return "震荡整理 ↔️"


# 便捷函数
def get_db() -> DatabaseManager:
    """获取数据库管理器实例的快捷方式"""
    return DatabaseManager.get_instance()
