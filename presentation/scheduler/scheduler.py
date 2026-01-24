# -*- coding: utf-8 -*-
"""
定时任务调度器

从scheduler.py迁移的定时任务功能
"""

import logging
import time
from datetime import datetime
from datetime import time as dt_time
from typing import Callable, Optional

import schedule

logger = logging.getLogger(__name__)


class ScheduledTask:
    """
    定时任务封装

    用于封装定时任务的相关信息
    """

    def __init__(self, task: Callable, schedule_time: str, run_immediately: bool = False):
        """
        初始化定时任务

        Args:
            task: 要执行的任务函数
            schedule_time: 执行时间（格式：HH:MM）
            run_immediately: 是否立即执行一次
        """
        self.task = task
        self.schedule_time = schedule_time
        self.run_immediately = run_immediately


def run_with_schedule(task: Callable, schedule_time: str = "09:30", run_immediately: bool = False) -> None:
    """
    运行定时任务

    Args:
        task: 要执行的任务函数
        schedule_time: 每日执行时间（格式：HH:MM，默认09:30）
        run_immediately: 是否在启动时立即执行一次（默认False）
    """
    logger.info(f"定时任务已启动，每日执行时间: {schedule_time}")

    # 立即执行一次（如果启用）
    if run_immediately:
        logger.info("立即执行一次任务...")
        try:
            task()
        except Exception as e:
            logger.error(f"立即执行任务失败: {e}")

    # 设置定时任务
    schedule.every().day.at(schedule_time).do(_safe_execute_task, task)

    # 运行调度循环
    logger.info("定时任务调度器运行中...")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        logger.info("定时任务调度器已停止")


def _safe_execute_task(task: Callable) -> None:
    """
    安全执行任务（带异常处理）

    Args:
        task: 要执行的任务函数
    """
    try:
        logger.info(f"执行定时任务: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        task()
        logger.info("定时任务执行完成")
    except Exception as e:
        logger.error(f"定时任务执行失败: {e}", exc_info=True)
