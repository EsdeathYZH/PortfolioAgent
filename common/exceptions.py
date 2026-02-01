# -*- coding: utf-8 -*-
"""
自定义异常

定义项目通用异常类
"""


class AnalysisError(Exception):
    """分析错误基类"""

    pass


class DataFetchError(AnalysisError):
    """数据获取错误"""

    pass


class AnalysisServiceError(AnalysisError):
    """分析服务错误"""

    pass


class NotificationError(Exception):
    """通知错误"""

    pass


class SearchError(Exception):
    """搜索错误"""

    pass


class BacktestError(Exception):
    """回测错误"""

    pass


class ConfigError(Exception):
    """配置错误"""

    pass
