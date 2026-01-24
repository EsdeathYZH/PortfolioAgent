# -*- coding: utf-8 -*-
"""
回测引擎

整合执行器和指标计算，提供统一接口
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from core.domain.asset import Asset
from core.domain.signal import TradingSignal

from .executor import BacktestExecutor, BacktestResult, Trade
from .metrics import BacktestMetrics, MetricsCalculator
from .signal_generator import SignalGenerator
from .strategies.base import Strategy


class BacktestEngine:
    """
    回测引擎

    输入：历史数据、交易信号
    输出：回测结果和指标
    """

    def __init__(self, initial_capital: float = 100000.0, signal_generator: Optional[SignalGenerator] = None):
        """
        初始化回测引擎

        Args:
            initial_capital: 初始资金（元）
            signal_generator: 信号生成器（可选）
        """
        self.initial_capital = initial_capital
        self.executor = BacktestExecutor(initial_capital)
        self.signal_generator = signal_generator or SignalGenerator()
        self.metrics_calculator = MetricsCalculator()

    def run_backtest(
        self, signals: List[TradingSignal], price_data: Dict[date, Dict[str, float]], start_date: date, end_date: date
    ) -> BacktestResult:
        """
        运行回测

        Args:
            signals: 交易信号列表
            price_data: 价格数据字典 {date: {code: price}}
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            BacktestResult 回测结果
        """
        # 重置执行器
        self.executor.reset()

        # 按日期排序信号
        sorted_signals = sorted(signals, key=lambda s: s.date)

        # 执行所有信号
        daily_equity = [self.initial_capital]
        current_date = start_date

        for signal in sorted_signals:
            # 跳过不在回测日期范围内的信号
            if signal.date < start_date or signal.date > end_date:
                continue

            # 获取信号日期的价格
            if signal.date in price_data:
                prices = price_data[signal.date]
                if signal.code in prices:
                    current_price = prices[signal.code]

                    # 执行信号
                    trade = self.executor.execute_signal(signal, current_price)

                    # 计算当日权益
                    equity = self.executor.get_total_equity(prices)
                    daily_equity.append(equity)

        # 计算最终权益
        if end_date in price_data:
            final_prices = price_data[end_date]
            final_equity = self.executor.get_total_equity(final_prices)
        else:
            final_equity = self.executor.current_capital

        # 创建回测结果
        result = BacktestResult(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_equity,
            total_return=(final_equity - self.initial_capital) / self.initial_capital * 100,
            trades=self.executor.trades.copy(),
            positions=self.executor.get_current_positions(),
            daily_equity=[{"date": start_date.isoformat(), "equity": eq} for eq in daily_equity],
        )

        return result

    def calculate_metrics(self, result: BacktestResult) -> BacktestMetrics:
        """
        计算回测指标

        Args:
            result: 回测结果

        Returns:
            BacktestMetrics 回测指标
        """
        # 提取每日权益
        daily_equity = [item["equity"] for item in result.daily_equity]

        # 计算指标
        metrics = self.metrics_calculator.calculate(result, daily_equity)

        return metrics

    def run_full_backtest(
        self, signals: List[TradingSignal], price_data: Dict[date, Dict[str, float]], start_date: date, end_date: date
    ) -> tuple[BacktestResult, BacktestMetrics]:
        """
        运行完整回测（包含指标计算）

        Args:
            signals: 交易信号列表
            price_data: 价格数据字典
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            tuple[BacktestResult, BacktestMetrics] 回测结果和指标
        """
        # 运行回测
        result = self.run_backtest(signals, price_data, start_date, end_date)

        # 计算指标
        metrics = self.calculate_metrics(result)

        return result, metrics
