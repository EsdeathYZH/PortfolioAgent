# -*- coding: utf-8 -*-
"""
命令行接口模块
"""

from .args import parse_arguments
from .logging_setup import setup_logging

__all__ = ["parse_arguments", "setup_logging"]
