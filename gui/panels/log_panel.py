# -*- coding: utf-8 -*-
"""
日志面板

实时显示工作流执行日志。
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont

from ..styles import Colors, Sizes, get_log_level_color, Fonts


class LogPanel(QWidget):
    """日志面板
    
    实时显示工作流执行日志，支持自动滚动和颜色区分。
    """
    
    MAX_LOG_LINES = 2000
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._auto_scroll = True
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(Sizes.MARGIN_SMALL)
        layout.setContentsMargins(Sizes.MARGIN_LARGE, Sizes.MARGIN_LARGE, Sizes.MARGIN_LARGE, Sizes.MARGIN_LARGE)
        
        # 顶部工具栏
        toolbar = QHBoxLayout()
        
        title = QLabel("运行日志")
        title.setStyleSheet(f"font-size: {Fonts.SIZE_TITLE}px; font-weight: bold;")
        toolbar.addWidget(title)
        
        toolbar.addStretch()
        
        self.btn_auto_scroll = QPushButton("自动滚动: 开")
        self.btn_auto_scroll.setCheckable(True)
        self.btn_auto_scroll.setChecked(True)
        self.btn_auto_scroll.clicked.connect(self._toggle_auto_scroll)
        self.btn_auto_scroll.setFixedWidth(120)  # 确保中文完整显示
        toolbar.addWidget(self.btn_auto_scroll)
        
        self.btn_copy = QPushButton("复制")
        self.btn_copy.clicked.connect(self._copy_logs)
        self.btn_copy.setFixedWidth(60)
        toolbar.addWidget(self.btn_copy)
        
        self.btn_clear = QPushButton("清空")
        self.btn_clear.clicked.connect(self.clear_logs)
        self.btn_clear.setFixedWidth(60)
        toolbar.addWidget(self.btn_clear)
        
        layout.addLayout(toolbar)
        
        # 日志内容
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        # 样式已在 styles.py 中定义
        layout.addWidget(self.log_text)
        
    @pyqtSlot(str, int)
    def append_log(self, message: str, level: int = logging.INFO) -> None:
        color = get_log_level_color(level)
        
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        char_format = QTextCharFormat()
        char_format.setForeground(QColor(color))
        
        cursor.insertText(message + "\n", char_format)
        
        self._trim_logs()
        
        if self._auto_scroll:
            self.log_text.setTextCursor(cursor)
            self.log_text.ensureCursorVisible()
    
    def _trim_logs(self) -> None:
        document = self.log_text.document()
        if document.blockCount() > self.MAX_LOG_LINES:
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            lines_to_remove = document.blockCount() - self.MAX_LOG_LINES
            for _ in range(lines_to_remove):
                cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
    
    def clear_logs(self) -> None:
        self.log_text.clear()
    
    def _toggle_auto_scroll(self) -> None:
        self._auto_scroll = self.btn_auto_scroll.isChecked()
        self.btn_auto_scroll.setText("自动滚动: 开" if self._auto_scroll else "自动滚动: 关")
        if self._auto_scroll:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)

    def _copy_logs(self) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_text.toPlainText())
        QMessageBox.information(self, "提示", "日志已复制到剪贴板")

    def get_log_content(self) -> str:
        return self.log_text.toPlainText()
