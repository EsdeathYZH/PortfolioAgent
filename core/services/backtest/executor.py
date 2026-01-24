# -*- coding: utf-8 -*-
"""
回测执行器

模拟交易执行逻辑
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from core.domain.signal import SignalType, TradingSignal


@dataclass
class Position:
    """持仓"""

    code: str
    quantity: int  # 持仓数量（股）
    avg_price: float  # 平均成本
    entry_date: date  # 建仓日期
    entry_signal: TradingSignal  # 建仓信号


@dataclass
class Trade:
    """交易记录"""

    code: str
    signal: TradingSignal
    quantity: int  # 交易数量（股）
    price: float  # 交易价格
    amount: float  # 交易金额
    date: date
    type: str  # "buy" or "sell"


@dataclass
class BacktestResult:
    """回测结果"""

    start_date: date
    end_date: date
    initial_capital: float  # 初始资金
    final_capital: float  # 最终资金
    total_return: float  # 总收益率
    trades: List[Trade] = field(default_factory=list)
    positions: List[Position] = field(default_factory=list)
    daily_equity: List[Dict[str, Any]] = field(default_factory=list)  # 每日权益


class BacktestExecutor:
    """
    回测执行器

    模拟交易执行逻辑，处理买卖信号
    """

    def __init__(self, initial_capital: float = 100000.0):
        """
        初始化回测执行器

        Args:
            initial_capital: 初始资金（元）
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Position] = {}  # 持仓字典 {code: Position}
        self.trades: List[Trade] = []

    def execute_signal(
        self, signal: TradingSignal, current_price: float, available_capital: Optional[float] = None
    ) -> Optional[Trade]:
        """
        执行交易信号

        Args:
            signal: 交易信号
            current_price: 当前价格
            available_capital: 可用资金（可选，默认使用self.current_capital）

        Returns:
            Trade 交易记录，如果无法执行则返回None
        """
        if available_capital is None:
            available_capital = self.current_capital

        if signal.signal_type == SignalType.BUY:
            return self._execute_buy(signal, current_price, available_capital)
        elif signal.signal_type == SignalType.SELL:
            return self._execute_sell(signal, current_price)
        elif signal.signal_type == SignalType.CLOSE:
            return self._execute_close(signal, current_price)
        else:
            # HOLD 不执行
            return None

    def _execute_buy(self, signal: TradingSignal, price: float, available_capital: float) -> Optional[Trade]:
        """执行买入信号"""
        # 计算可买入数量（假设使用可用资金的80%）
        use_capital = available_capital * 0.8
        quantity = int(use_capital / price / 100) * 100  # 按手（100股）买入

        if quantity < 100:
            # 资金不足，无法买入
            return None

        amount = quantity * price

        # 创建交易记录
        trade = Trade(
            code=signal.code, signal=signal, quantity=quantity, price=price, amount=amount, date=signal.date, type="buy"
        )

        # 更新持仓
        if signal.code in self.positions:
            # 加仓
            pos = self.positions[signal.code]
            total_cost = pos.avg_price * pos.quantity + amount
            pos.quantity += quantity
            pos.avg_price = total_cost / pos.quantity
        else:
            # 新建仓
            self.positions[signal.code] = Position(
                code=signal.code, quantity=quantity, avg_price=price, entry_date=signal.date, entry_signal=signal
            )

        # 更新资金
        self.current_capital -= amount
        self.trades.append(trade)

        return trade

    def _execute_sell(self, signal: TradingSignal, price: float) -> Optional[Trade]:
        """执行卖出信号"""
        if signal.code not in self.positions:
            # 无持仓，无法卖出
            return None

        pos = self.positions[signal.code]

        # 卖出全部持仓
        quantity = pos.quantity
        amount = quantity * price

        # 创建交易记录
        trade = Trade(
            code=signal.code,
            signal=signal,
            quantity=quantity,
            price=price,
            amount=amount,
            date=signal.date,
            type="sell",
        )

        # 更新持仓（清仓）
        del self.positions[signal.code]

        # 更新资金
        self.current_capital += amount
        self.trades.append(trade)

        return trade

    def _execute_close(self, signal: TradingSignal, price: float) -> Optional[Trade]:
        """执行平仓信号（与卖出相同）"""
        return self._execute_sell(signal, price)

    def get_current_positions(self) -> List[Position]:
        """获取当前持仓"""
        return list(self.positions.values())

    def get_total_equity(self, current_prices: Dict[str, float]) -> float:
        """
        计算总权益（现金 + 持仓市值）

        Args:
            current_prices: 当前价格字典 {code: price}

        Returns:
            float 总权益
        """
        equity = self.current_capital

        for code, pos in self.positions.items():
            if code in current_prices:
                equity += pos.quantity * current_prices[code]

        return equity

    def reset(self) -> None:
        """重置执行器状态"""
        self.current_capital = self.initial_capital
        self.positions.clear()
        self.trades.clear()
