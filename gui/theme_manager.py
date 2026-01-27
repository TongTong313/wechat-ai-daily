# -*- coding: utf-8 -*-
"""
主题管理器

负责检测系统主题（Light/Dark），并提供语义化的颜色变量。
"""

import sys
import logging
import subprocess
from typing import Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

try:
    import darkdetect
    HAS_DARKDETECT = True
except ImportError:
    HAS_DARKDETECT = False
    logging.warning("未安装 darkdetect 库，尝试使用原生命令检测系统主题。")


class ThemeManager(QObject):
    """主题管理器"""

    # 主题切换信号
    theme_changed = pyqtSignal(str)  # 发送新主题名称 ("light" or "dark")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_theme = "light"
        self._auto_detect = True
        
        # 初始化主题
        self.detect_system_theme()

    def detect_system_theme(self) -> str:
        """检测系统主题"""
        if not self._auto_detect:
            return self._current_theme

        theme = "light"
        
        # 1. 优先尝试使用 darkdetect 库
        if HAS_DARKDETECT:
            try:
                if darkdetect.isDark():
                    theme = "dark"
            except Exception as e:
                logging.error(f"darkdetect 检测系统主题失败: {e}")
                
        # 2. 如果没有 darkdetect 或检测失败，且在 macOS 上，尝试使用原生命令
        if theme == "light" and sys.platform == "darwin":
            try:
                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    capture_output=True,
                    text=True
                )
                # 如果命令成功且输出包含 "Dark"，则为深色模式
                # 注意：浅色模式下该命令通常会报错（exit code 1）或输出为空
                if result.returncode == 0 and "Dark" in result.stdout:
                    theme = "dark"
            except Exception as e:
                logging.error(f"原生命令检测系统主题失败: {e}")
        
        # 如果检测结果变化，发送信号
        if theme != self._current_theme:
            self._current_theme = theme
            self.theme_changed.emit(theme)
            logging.info(f"系统主题切换为: {theme}")
            
        return theme

    def get_current_theme(self) -> str:
        """获取当前主题名称"""
        return self._current_theme

    def is_dark(self) -> bool:
        """是否为深色模式"""
        return self._current_theme == "dark"

    def get_colors(self) -> Dict[str, str]:
        """获取当前主题的颜色变量字典"""
        if self.is_dark():
            return self.DARK_THEME
        else:
            return self.LIGHT_THEME

    # ==================== 语义化颜色定义 ====================

    # 浅色模式 (Light Mode)
    LIGHT_THEME = {
        # 基础背景
        "window_bg": "#F5F7FA",      # 整体背景 (灰白)
        "content_bg": "#F5F7FA",     # 内容区背景
        "sidebar_bg": "#FFFFFF",     # 侧边栏背景 (纯白)
        
        # 卡片与容器
        "card_bg": "#FFFFFF",        # 卡片背景 (纯白)
        "input_bg": "#FFFFFF",       # 输入框背景
        "input_bg_hover": "#F5F7FA", # 输入框悬停背景
        
        # 文字颜色
        "text_primary": "#1F2329",   # 主要文字 (深黑)
        "text_secondary": "#646A73", # 次要文字 (深灰)
        "text_hint": "#8F959E",      # 提示文字 (浅灰)
        "text_white": "#FFFFFF",     # 反白文字
        "text_sidebar": "#1F2329",   # 侧边栏文字
        "text_sidebar_selected": "#07C160", # 侧边栏选中文字
        
        # 边框与分割线
        "border": "#DEE0E3",         # 常规边框
        "border_light": "#E8EAED",   # 浅色边框
        "splitter_handle": "#E8EAED",# 分割线颜色
        
        # 交互状态
        "sidebar_item_hover": "#F2F3F5",    # 侧边栏悬停
        "sidebar_item_selected": "#E8FFEA", # 侧边栏选中 (浅绿背景)
        "button_hover_bg": "#F2F3F5",       # 普通按钮悬停
        
        # 功能色
        "primary": "#07C160",        # 主色调 (微信绿)
        "primary_hover": "#06AD56",
        "primary_pressed": "#059B4C",
        "primary_light": "rgba(7, 193, 96, 0.1)",
        
        "error": "#F54A45",
        "warning": "#FF9500",
        "success": "#07C160",
        "info": "#3370FF",
        
        # 日志区域
        "log_bg": "#FFFFFF",         # 日志背景
        "log_text": "#1F2329",       # 日志文字
        "log_border": "#DEE0E3",
        
        # 特殊控件
        "shadow": "rgba(0, 0, 0, 0.05)",
        "progress_bg": "#F5F5F5",
        "progress_chunk": "#07C160",
    }

    # 深色模式 (Dark Mode)
    DARK_THEME = {
        # 基础背景
        "window_bg": "#1E1E1E",      # 整体背景 (深灰)
        "content_bg": "#1E1E1E",     # 内容区背景
        "sidebar_bg": "#252526",     # 侧边栏背景 (稍亮)
        
        # 卡片与容器
        "card_bg": "#2D2D2D",        # 卡片背景 (卡片灰)
        "input_bg": "#3C3C3C",       # 输入框背景
        "input_bg_hover": "#454545", # 输入框悬停背景
        
        # 文字颜色
        "text_primary": "#E0E0E0",   # 主要文字 (灰白)
        "text_secondary": "#AAAAAA", # 次要文字 (浅灰)
        "text_hint": "#666666",      # 提示文字 (深灰)
        "text_white": "#FFFFFF",     # 反白文字
        "text_sidebar": "#CCCCCC",   # 侧边栏文字
        "text_sidebar_selected": "#07C160", # 侧边栏选中文字
        
        # 边框与分割线
        "border": "#3E3E3E",         # 常规边框
        "border_light": "#454545",   # 浅色边框
        "splitter_handle": "#333333",# 分割线颜色
        
        # 交互状态
        "sidebar_item_hover": "#37373D",    # 侧边栏悬停
        "sidebar_item_selected": "#2D2D2D", # 侧边栏选中
        "button_hover_bg": "#3E3E3E",       # 普通按钮悬停
        
        # 功能色
        "primary": "#07C160",        # 主色调 (保持)
        "primary_hover": "#06AD56",
        "primary_pressed": "#059B4C",
        "primary_light": "rgba(7, 193, 96, 0.2)",
        
        "error": "#FF6B6B",          # 稍亮的红色
        "warning": "#FFC069",        # 稍亮的橙色
        "success": "#52C41A",        # 稍亮的绿色
        "info": "#5C93FF",           # 稍亮的蓝色
        
        # 日志区域
        "log_bg": "#1E1E1E",         # 日志背景
        "log_text": "#D4D4D4",       # 日志文字
        "log_border": "#3E3E3E",
        
        # 特殊控件
        "shadow": "rgba(0, 0, 0, 0.3)", # 深色模式阴影加深
        "progress_bg": "#333333",
        "progress_chunk": "#07C160",
    }
