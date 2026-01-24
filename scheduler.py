# -*- coding: utf-8 -*-
"""
定时任务调度器（向后兼容）

此文件保持向后兼容，实际实现已迁移到 presentation/scheduler/scheduler.py
"""

# 从新位置导入所有内容
from presentation.scheduler import ScheduledTask, run_with_schedule

# 导出以保持向后兼容
__all__ = [
    "run_with_schedule",
    "ScheduledTask",
]
