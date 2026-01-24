# -*- coding: utf-8 -*-
"""
格式化器工具函数

共享的辅助方法
"""

# 导入AnalysisResult
import sys
from pathlib import Path
from typing import Tuple

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.domain.analysis import AnalysisResult


def get_signal_level(result: AnalysisResult) -> Tuple[str, str, str]:
    """
    根据操作建议获取信号等级和颜色

    Args:
        result: 分析结果

    Returns:
        (信号文字, emoji, 颜色标记)
    """
    advice = result.operation_advice
    score = result.sentiment_score

    if advice in ["强烈买入"] or score >= 80:
        return ("强烈买入", "💚", "强买")
    elif advice in ["买入", "加仓"] or score >= 65:
        return ("买入", "🟢", "买入")
    elif advice in ["持有"] or 55 <= score < 65:
        return ("持有", "🟡", "持有")
    elif advice in ["观望"] or 45 <= score < 55:
        return ("观望", "⚪", "观望")
    elif advice in ["减仓"] or 35 <= score < 45:
        return ("减仓", "🟠", "减仓")
    elif advice in ["卖出", "强烈卖出"] or score < 35:
        return ("卖出", "🔴", "卖出")
    else:
        return ("观望", "⚪", "观望")
