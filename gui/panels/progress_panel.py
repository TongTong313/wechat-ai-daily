# -*- coding: utf-8 -*-
"""
进度面板

显示工作流执行进度、状态信息等。
"""

from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, pyqtSlot

from ..styles import Colors, Sizes, Fonts


class ProgressPanel(QFrame):
    """进度面板 (Footer Style)
    
    显示工作流执行的进度和状态信息。
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_colors = {}
        self._setup_ui()
        self.reset()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(Sizes.MARGIN_LARGE, 12, Sizes.MARGIN_LARGE, 12)
        
        # 上半部分：状态和统计
        top_row = QHBoxLayout()
        
        self.status_label = QLabel("就绪")
        # 样式将在 update_theme 中设置
        top_row.addWidget(self.status_label)
        
        top_row.addStretch()
        
        self.stats_label = QLabel("")
        # 样式将在 update_theme 中设置
        top_row.addWidget(self.stats_label)
        
        layout.addLayout(top_row)
        
        # 中间：进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 下半部分：详细信息
        self.detail_label = QLabel("")
        # 样式将在 update_theme 中设置
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.detail_label)

    def update_theme(self, colors: Dict[str, str]):
        """更新主题样式"""
        self._current_colors = colors
        
        self.setStyleSheet(f"""
            ProgressPanel {{
                background-color: {colors['window_bg']};
                border-top: 1px solid {colors['border_light']};
            }}
            QProgressBar {{
                border: none;
                background-color: {colors['progress_bg']};
                border-radius: 2px;
                height: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {colors['progress_chunk']};
                border-radius: 2px;
            }}
        """)
        
        self.status_label.setStyleSheet(f"font-weight: bold; color: {colors['text_primary']};")
        self.stats_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: {Fonts.SIZE_SMALL}px;")
        self.detail_label.setStyleSheet(f"color: {colors['text_hint']}; font-size: {Fonts.SIZE_SMALL}px;")

    def reset(self) -> None:
        self.set_status("就绪")
        self.set_progress(0)
        self.set_stats("")
        self.set_detail("")
    
    @pyqtSlot(str, str)
    def set_status(self, status: str, color_key: str = None) -> None:
        """设置状态
        
        Args:
            status: 状态文本
            color_key: 颜色键名 (如 'success', 'error', 'info')，如果为 None 则使用默认文字颜色
        """
        self.status_label.setText(status)
        
        colors = self._current_colors
        if not colors:
            return
            
        if color_key and color_key in colors:
            color = colors[color_key]
        elif color_key and color_key.startswith("#"): # 兼容旧代码传入的具体颜色值
            color = color_key
        else:
            color = colors['text_primary']
            
        self.status_label.setStyleSheet(f"font-weight: bold; color: {color};")
    
    @pyqtSlot(int)
    def set_progress(self, value: int) -> None:
        self.progress_bar.setValue(min(100, max(0, value)))
    
    @pyqtSlot(str)
    def set_stats(self, stats: str) -> None:
        self.stats_label.setText(stats)
    
    @pyqtSlot(str)
    def set_detail(self, detail: str) -> None:
        self.detail_label.setText(detail)
    
    def set_running(self, task_name: str = "执行中") -> None:
        self.set_status(f"⏳ {task_name}...", "info")
    
    def set_success(self, message: str = "完成") -> None:
        self.set_status(f"✅ {message}", "success")
        self.set_progress(100)
    
    def set_error(self, message: str = "失败") -> None:
        self.set_status(f"❌ {message}", "error")
    
    def set_warning(self, message: str) -> None:
        self.set_status(f"⚠️ {message}", "warning")
