# -*- coding: utf-8 -*-
"""
微信 AI 日报助手 - 桌面客户端模块

该模块提供桌面客户端界面，用于配置和执行公众号文章采集及公众号文章内容生成工作流。
"""

from .main_window import MainWindow
from .utils.config_manager import ConfigManager
from .utils.env_file_manager import EnvFileManager

__all__ = ["MainWindow", "ConfigManager", "EnvFileManager"]
