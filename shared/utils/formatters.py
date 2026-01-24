# -*- coding: utf-8 -*-
"""
格式化工具

提取通用的格式化函数
"""

from typing import Optional


def format_volume(volume: Optional[float]) -> str:
    """
    格式化成交量

    Args:
        volume: 成交量（股）

    Returns:
        str 格式化后的成交量字符串
    """
    if volume is None or volume == 0:
        return "0"

    if volume >= 1e8:
        return f"{volume / 1e8:.2f}亿"
    elif volume >= 1e4:
        return f"{volume / 1e4:.2f}万"
    else:
        return f"{volume:.0f}"


def format_amount(amount: Optional[float]) -> str:
    """
    格式化成交额

    Args:
        amount: 成交额（元）

    Returns:
        str 格式化后的成交额字符串
    """
    if amount is None or amount == 0:
        return "0"

    if amount >= 1e8:
        return f"{amount / 1e8:.2f}亿"
    elif amount >= 1e4:
        return f"{amount / 1e4:.2f}万"
    else:
        return f"{amount:.2f}"


def format_percentage(value: Optional[float], decimals: int = 2) -> str:
    """
    格式化百分比

    Args:
        value: 百分比值
        decimals: 小数位数

    Returns:
        str 格式化后的百分比字符串
    """
    if value is None:
        return "N/A"

    return f"{value:.{decimals}f}%"


def format_price(price: Optional[float], decimals: int = 2) -> str:
    """
    格式化价格

    Args:
        price: 价格
        decimals: 小数位数

    Returns:
        str 格式化后的价格字符串
    """
    if price is None:
        return "N/A"

    return f"{price:.{decimals}f}"
