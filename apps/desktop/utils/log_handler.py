# -*- coding: utf-8 -*-
"""
日志处理器

将 Python logging 日志输出重定向到 PyQt6 的文本组件，实现实时日志显示。
"""

import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class LogSignal(QObject):
    """日志信号类
    
    用于在日志线程和 UI 线程之间传递日志消息。
    """
    # 日志消息信号：(消息文本, 日志级别)
    log_message = pyqtSignal(str, int)


class QTextEditLogHandler(logging.Handler):
    """Qt 文本编辑器日志处理器
    
    将 logging 日志重定向到 Qt 信号，用于在 UI 中显示实时日志。
    
    使用方法：
        handler = QTextEditLogHandler()
        handler.log_signal.log_message.connect(your_slot_function)
        logging.getLogger().addHandler(handler)
    """
    
    def __init__(self, level: int = logging.NOTSET):
        """初始化日志处理器
        
        Args:
            level: 日志级别，默认为 NOTSET（记录所有级别）
        """
        super().__init__(level)
        
        # 创建信号对象
        self.log_signal = LogSignal()
        
        # 设置日志格式
        self.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)-5s %(message)s",
            datefmt="%H:%M:%S"
        ))
    
    def emit(self, record: logging.LogRecord) -> None:
        """发送日志记录
        
        将日志记录格式化后通过信号发送。
        
        Args:
            record: 日志记录对象
        """
        try:
            # 格式化日志消息
            msg = self.format(record)
            # 通过信号发送日志消息和级别
            self.log_signal.log_message.emit(msg, record.levelno)
        except Exception:
            # 处理日志时出错，调用父类的错误处理
            self.handleError(record)


class LogManager:
    """日志管理器
    
    统一管理应用的日志配置，包括文件日志和 UI 日志。
    """
    
    _instance: Optional["LogManager"] = None
    _qt_handler: Optional[QTextEditLogHandler] = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化日志管理器"""
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._qt_handler = None
    
    def setup_logging(
        self,
        level: int = logging.INFO,
        log_file: Optional[str] = None
    ) -> QTextEditLogHandler:
        """配置日志系统
        
        Args:
            level: 日志级别
            log_file: 日志文件路径（可选）
            
        Returns:
            QTextEditLogHandler: Qt 日志处理器，用于连接 UI
        """
        # 获取根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # 清除现有的处理器（避免重复添加）
        root_logger.handlers.clear()
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        ))
        root_logger.addHandler(console_handler)
        
        # 添加文件处理器（如果指定了文件）
        if log_file:
            try:
                from pathlib import Path
                Path(log_file).parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file, encoding="utf-8")
                file_handler.setLevel(level)
                file_handler.setFormatter(logging.Formatter(
                    "%(asctime)s - %(levelname)s - %(message)s"
                ))
                root_logger.addHandler(file_handler)
            except Exception as e:
                logging.warning(f"无法创建日志文件: {e}")
        
        # 创建并添加 Qt 处理器
        self._qt_handler = QTextEditLogHandler(level)
        root_logger.addHandler(self._qt_handler)
        
        return self._qt_handler
    
    def get_qt_handler(self) -> Optional[QTextEditLogHandler]:
        """获取 Qt 日志处理器
        
        Returns:
            QTextEditLogHandler: Qt 日志处理器，如果未初始化返回 None
        """
        return self._qt_handler
