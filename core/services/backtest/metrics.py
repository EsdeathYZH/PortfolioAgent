# -*- coding: utf-8 -*-
"""
回测指标计算

计算收益率、夏普比率、最大回撤等指标
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, List

from .executor import BacktestResult, Trade


@dataclass
class BacktestMetrics:
    """回测指标"""

    total_return: float  # 总收益率
    annual_return: float  # 年化收益率
    sharpe_ratio: float  # 夏普比率
    max_drawdown: float  # 最大回撤
    win_rate: float  # 胜率
    profit_factor: float  # 盈亏比
    total_trades: int  # 总交易次数
    winning_trades: int  # 盈利交易次数
    losing_trades: int  # 亏损交易次数


class MetricsCalculator:
    """
    回测指标计算器

    计算各种回测指标
    """

    @staticmethod
    def calculate(result: BacktestResult, daily_equity: List[float]) -> BacktestMetrics:
        """
        计算回测指标

        Args:
            result: 回测结果
            daily_equity: 每日权益列表

        Returns:
            BacktestMetrics 回测指标
        """
        # 总收益率
        total_return = (result.final_capital - result.initial_capital) / result.initial_capital * 100

        # 年化收益率
        days = (result.end_date - result.start_date).days
        if days > 0:
            annual_return = ((result.final_capital / result.initial_capital) ** (365.0 / days) - 1) * 100
        else:
            annual_return = 0.0

        # 最大回撤
        max_drawdown = MetricsCalculator._calculate_max_drawdown(daily_equity)

        # 夏普比率（简化版，假设无风险利率为0）
        sharpe_ratio = MetricsCalculator._calculate_sharpe_ratio(daily_equity)

        # 交易统计
        win_count = 0
        lose_count = 0
        total_profit = 0.0
        total_loss = 0.0

        # 按股票分组计算盈亏
        stock_trades: Dict[str, List[Trade]] = {}
        for trade in result.trades:
            if trade.code not in stock_trades:
                stock_trades[trade.code] = []
            stock_trades[trade.code].append(trade)

        for code, trades in stock_trades.items():
            # 计算该股票的盈亏
            buy_amount = sum(t.amount for t in trades if t.type == "buy")
            sell_amount = sum(t.amount for t in trades if t.type == "sell")

            if sell_amount > 0:
                profit = sell_amount - buy_amount
                if profit > 0:
                    win_count += 1
                    total_profit += profit
                else:
                    lose_count += 1
                    total_loss += abs(profit)

        # 胜率
        total_trades = win_count + lose_count
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0.0

        # 盈亏比
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0.0

        return BacktestMetrics(
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            winning_trades=win_count,
            losing_trades=lose_count,
        )

    @staticmethod
    def _calculate_max_drawdown(daily_equity: List[float]) -> float:
        """
        计算最大回撤

        Args:
            daily_equity: 每日权益列表

        Returns:
            float 最大回撤（百分比）
        """
        if not daily_equity:
            return 0.0

        max_equity = daily_equity[0]
        max_drawdown = 0.0

        for equity in daily_equity:
            if equity > max_equity:
                max_equity = equity

            drawdown = (max_equity - equity) / max_equity * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return max_drawdown

    @staticmethod
    def _calculate_sharpe_ratio(daily_equity: List[float]) -> float:
        """
        计算夏普比率（简化版）

        Args:
            daily_equity: 每日权益列表

        Returns:
            float 夏普比率
        """
        if len(daily_equity) < 2:
            return 0.0

        # 计算日收益率
        returns = []
        for i in range(1, len(daily_equity)):
            if daily_equity[i - 1] > 0:
                ret = (daily_equity[i] - daily_equity[i - 1]) / daily_equity[i - 1]
                returns.append(ret)

        if not returns:
            return 0.0

        # 计算平均收益率和标准差
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = math.sqrt(variance) if variance > 0 else 0.0

        # 夏普比率 = (平均收益率 - 无风险利率) / 标准差
        # 简化版：假设无风险利率为0，年化
        if std_dev > 0:
            sharpe = (avg_return / std_dev) * math.sqrt(252)  # 年化（252个交易日）
        else:
            sharpe = 0.0

        return sharpe
