# -*- coding: utf-8 -*-
"""
AI接口基类
"""

# 暂时导入原有模块
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.domain.analysis import AnalysisResult


class BaseAIAnalyzer(ABC):
    """
    AI分析器基类

    所有AI分析器都应该继承此类
    """

    @abstractmethod
    def analyze(self, context: str, news_context: Optional[str] = None) -> AnalysisResult:
        """
        执行分析

        Args:
            context: 分析上下文（技术面数据等）
            news_context: 新闻上下文（可选）

        Returns:
            分析结果
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查分析器是否可用

        Returns:
            是否可用
        """
        pass
