# -*- coding: utf-8 -*-
"""
GUI 后台工作线程模块

包含执行工作流的后台线程，避免阻塞 UI。
"""

from .workflow_worker import WorkflowWorker

__all__ = ["WorkflowWorker"]
