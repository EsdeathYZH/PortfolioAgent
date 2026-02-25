# -*- coding: utf-8 -*-
"""点金术分析管线（与 StockAnalysisPipeline 同级）。"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from common.config import Config, get_config
from core.domain.user import UserConfig
from core.services.notification import NotificationService
from core.services.notification.formatters.point_gold_report import PointGoldReportFormatter
from infrastructure.fetchers import AkshareFetcher, DataFetcherManager

from .point_gold_models import (
    BUY_DIVIDEND_YIELD_THRESHOLD,
    BUY_MA120_BIAS_THRESHOLD,
    BUY_PE_THRESHOLD,
    SELL_MA120_BIAS_THRESHOLD,
    PointGoldAsset,
    PointGoldSnapshot,
)
from .point_gold_pool_loader import PointGoldPoolLoader

logger = logging.getLogger(__name__)


class PointGoldAnalysisPipeline:
    """点金术策略分析管线（非 AI）。"""

    def __init__(
        self,
        config: Optional[Config] = None,
        user_config: Optional[UserConfig] = None,
        pool_loader: Optional[PointGoldPoolLoader] = None,
        fetcher_manager: Optional[DataFetcherManager] = None,
        akshare_fetcher: Optional[AkshareFetcher] = None,
    ):
        if user_config is None:
            raise ValueError("user_config 参数是必需的，请传入 UserConfig 对象")

        self.config = config or get_config()
        self.user_config = user_config
        self.notifier = NotificationService(user_config=user_config)

        self.pool_loader = pool_loader or PointGoldPoolLoader()
        self.fetcher_manager = fetcher_manager or DataFetcherManager()
        self.akshare_fetcher = akshare_fetcher or AkshareFetcher()
        self.formatter = PointGoldReportFormatter()
        self._spot_cache: Dict[str, object] = {}

    def run(self, send_notification: bool = True) -> Dict[str, List[PointGoldSnapshot]]:
        grouped = self._analyze_all()
        content = self.formatter.format(grouped)

        date_str = datetime.now().strftime("%Y%m%d")
        username = self.user_config.username
        filename = f"point_gold_report_{date_str}_{username}.md"
        filepath = self.notifier.save_report_to_file(content, filename=filename)
        logger.info(f"点金术报告已保存: {filepath}")

        if send_notification and self.notifier.is_available():
            if self.notifier.send(content):
                logger.info("点金术报告推送成功")
            else:
                logger.warning("点金术报告推送失败")

        return grouped

    def _analyze_all(self, assets: Optional[List[PointGoldAsset]] = None) -> Dict[str, List[PointGoldSnapshot]]:
        pool = assets or self.pool_loader.load_assets()

        buy_candidates: List[PointGoldSnapshot] = []
        sell_candidates: List[PointGoldSnapshot] = []
        watch_list: List[PointGoldSnapshot] = []

        for asset in pool:
            snap = self._build_snapshot(asset)
            if snap.signal == "BUY":
                buy_candidates.append(snap)
            elif snap.signal == "SELL":
                sell_candidates.append(snap)
            else:
                watch_list.append(snap)

        return {
            "buy_candidates": self._sort_by_bias(buy_candidates),
            "sell_candidates": self._sort_by_bias(sell_candidates, reverse=True),
            "watch_list": self._sort_by_bias(watch_list),
        }

    def _build_snapshot(self, asset: PointGoldAsset) -> PointGoldSnapshot:
        price = None
        ma120 = None
        bias = None
        pe = None
        dividend_yield = None
        dividend_method = "missing"
        reason_parts: List[str] = []

        try:
            df, source_name = self.fetcher_manager.get_daily_data(asset.code, days=120)
            if df is not None and not df.empty:
                close_series = df["close"].dropna()
                if len(close_series) > 0:
                    price = float(close_series.iloc[-1])
                if len(close_series) >= 120:
                    ma120 = float(close_series.tail(120).mean())
                    if ma120 > 0 and price is not None:
                        bias = (price - ma120) / ma120 * 100
                else:
                    reason_parts.append("历史数据不足120日")
            else:
                reason_parts.append("日线数据为空")
            logger.debug(f"[点金术] {asset.code} 日线来源: {source_name}")
        except Exception as e:
            reason_parts.append(f"日线获取失败: {e}")

        try:
            quote = self.akshare_fetcher.get_realtime_quote(asset.code)
            if quote:
                if quote.price and quote.price > 0:
                    price = quote.price
                    if ma120 and ma120 > 0:
                        bias = (price - ma120) / ma120 * 100
                if quote.pe_ratio and quote.pe_ratio > 0:
                    pe = quote.pe_ratio
        except Exception as e:
            reason_parts.append(f"实时行情获取失败: {e}")

        try:
            dividend_yield, dividend_method = self._get_dividend_yield(asset.code, price)
            if dividend_method == "fallback":
                reason_parts.append("股息率使用fallback: 近12个月现金分红/当前价")
            elif dividend_method == "missing":
                reason_parts.append("股息率缺失，且fallback计算失败")
        except Exception as e:
            reason_parts.append(f"股息率获取失败: {e}")

        signal, signal_reason = self._decide_signal(bias, pe, dividend_yield)
        reason_parts.append(signal_reason)

        return PointGoldSnapshot(
            name=asset.name,
            code=asset.code,
            group=asset.group,
            price=price,
            ma120=ma120,
            bias_ma120_pct=bias,
            pe=pe,
            dividend_yield=dividend_yield,
            dividend_method=dividend_method,
            signal=signal,
            reason="; ".join([r for r in reason_parts if r]),
        )

    def _decide_signal(
        self, bias: Optional[float], pe: Optional[float], dividend_yield: Optional[float]
    ) -> tuple[str, str]:
        if bias is None:
            return "WATCH", "无法计算MA120偏离"

        if bias >= SELL_MA120_BIAS_THRESHOLD:
            return "SELL", f"偏离MA120={bias:.2f}% >= {SELL_MA120_BIAS_THRESHOLD}%"

        if (
            bias <= BUY_MA120_BIAS_THRESHOLD
            and dividend_yield is not None
            and dividend_yield > BUY_DIVIDEND_YIELD_THRESHOLD
            and pe is not None
            and pe < BUY_PE_THRESHOLD
        ):
            return "BUY", (
                f"偏离MA120={bias:.2f}% <= {BUY_MA120_BIAS_THRESHOLD}%, "
                f"股息率={dividend_yield:.2f}% > {BUY_DIVIDEND_YIELD_THRESHOLD}%, PE={pe:.2f} < {BUY_PE_THRESHOLD}"
            )

        return "WATCH", "未同时满足买入或卖出条件"

    def _get_dividend_yield(self, code: str, price: Optional[float]) -> tuple[Optional[float], str]:
        import akshare as ak

        cache_key = "a_spot"
        if cache_key not in self._spot_cache:
            self._spot_cache[cache_key] = ak.stock_zh_a_spot_em()

        df = self._spot_cache.get(cache_key)
        if df is None or df.empty:
            return self._calc_dividend_yield_fallback(code, price), "fallback"

        row = df[df["代码"] == code]
        if row.empty:
            return self._calc_dividend_yield_fallback(code, price), "fallback"
        row_data = row.iloc[0]

        candidates = [
            "股息率",
            "股息率(%)",
            "股息率-动态",
            "股息率TTM",
            "股息率ttm",
            "股息率 TTM",
            "DIVIDEND_YIELD",
        ]
        for col in candidates:
            if col in row_data.index:
                value = self._to_float(row_data.get(col))
                if value is not None and value > 0:
                    return value, "direct"

        fallback = self._calc_dividend_yield_fallback(code, price)
        if fallback is not None and fallback > 0:
            return fallback, "fallback"
        return None, "missing"

    def _calc_dividend_yield_fallback(self, code: str, price: Optional[float]) -> Optional[float]:
        """fallback：近12个月现金分红(每10股)折算到每股后除以当前价。"""
        import akshare as ak
        import pandas as pd

        if price is None or price <= 0:
            return None

        detail_df = ak.stock_history_dividend_detail(symbol=code, indicator="分红")
        if detail_df is None or detail_df.empty:
            return None

        date_col = self._pick_date_col(detail_df)
        cash_col = self._pick_cash_dividend_col(detail_df)
        if date_col is None or cash_col is None:
            return None

        tmp = detail_df.copy()
        tmp["__date__"] = pd.to_datetime(tmp[date_col], errors="coerce")
        tmp["__cash__"] = pd.to_numeric(tmp[cash_col], errors="coerce")

        one_year_ago = datetime.now() - timedelta(days=365)
        mask = (tmp["__date__"] >= one_year_ago) & (tmp["__cash__"] > 0)
        recent = tmp.loc[mask, "__cash__"].dropna()
        if recent.empty:
            return None

        # AKShare该字段常见口径为“每10股派息X元”
        per_share_dividend = float(recent.sum()) / 10.0
        if per_share_dividend <= 0:
            return None
        return per_share_dividend / float(price) * 100.0

    def _pick_date_col(self, df) -> Optional[str]:
        import pandas as pd

        best_col = None
        best_count = 0
        for col in df.columns:
            parsed = pd.to_datetime(df[col], errors="coerce")
            count = int(parsed.notna().sum())
            if count > best_count:
                best_count = count
                best_col = col
        return best_col if best_count > 0 else None

    def _pick_cash_dividend_col(self, df) -> Optional[str]:
        import pandas as pd

        preferred_keywords = ("派息", "分红", "现金", "税前")
        for col in df.columns:
            col_str = str(col)
            if any(k in col_str for k in preferred_keywords):
                series = pd.to_numeric(df[col], errors="coerce")
                valid = series.dropna()
                if not valid.empty and valid.max() < 100 and valid.gt(0).any():
                    return col

        best_col = None
        best_score = -1
        for col in df.columns:
            series = pd.to_numeric(df[col], errors="coerce")
            valid = series.dropna()
            if valid.empty:
                continue
            plausible = valid[(valid > 0) & (valid < 100)]
            score = int(plausible.count())
            if score > best_score:
                best_score = score
                best_col = col
        return best_col if best_score > 0 else None

    @staticmethod
    def _to_float(value) -> Optional[float]:
        import pandas as pd

        if value is None or pd.isna(value):
            return None
        try:
            cleaned = str(value).replace("%", "").strip()
            if cleaned == "":
                return None
            return float(cleaned)
        except Exception:
            return None

    @staticmethod
    def _sort_by_bias(items: List[PointGoldSnapshot], reverse: bool = False) -> List[PointGoldSnapshot]:
        def key_fn(item: PointGoldSnapshot) -> float:
            if item.bias_ma120_pct is None:
                return 9999.0
            return item.bias_ma120_pct

        return sorted(items, key=key_fn, reverse=reverse)
