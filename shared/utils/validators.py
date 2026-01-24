# -*- coding: utf-8 -*-
"""
验证工具

提取通用的验证函数
"""

import re
from typing import Optional


def validate_stock_code(code: str) -> bool:
    """
    验证股票代码格式

    Args:
        code: 股票代码

    Returns:
        bool 是否有效
    """
    if not code:
        return False

    # A股代码：6位数字
    # 港股代码：5位数字
    # 美股代码：1-5位字母
    pattern = r"^(\d{6}|\d{5}|[A-Z]{1,5})$"
    return bool(re.match(pattern, code))


def validate_email(email: str) -> bool:
    """
    验证邮箱格式

    Args:
        email: 邮箱地址

    Returns:
        bool 是否有效
    """
    if not email:
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    验证URL格式

    Args:
        url: URL地址

    Returns:
        bool 是否有效
    """
    if not url:
        return False

    pattern = r"^https?://.+"
    return bool(re.match(pattern, url))


def validate_positive_number(value: Optional[float]) -> bool:
    """
    验证正数

    Args:
        value: 数值

    Returns:
        bool 是否为正数
    """
    return value is not None and value > 0


def validate_percentage(value: Optional[float]) -> bool:
    """
    验证百分比值（0-100）

    Args:
        value: 百分比值

    Returns:
        bool 是否有效
    """
    return value is not None and 0 <= value <= 100
