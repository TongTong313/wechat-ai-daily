"""微信 API 客户端基类"""

import logging
from typing import Optional


class BaseClient:
    """
    微信 API 客户端基类
    
    提供通用的日志记录功能和工具方法。
    """
    
    def __init__(self):
        """初始化基类"""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _log_init_success(self, info: dict):
        """
        记录初始化成功日志
        
        Args:
            info: 初始化信息字典
        """
        self.logger.info(f"{self.__class__.__name__} 初始化成功")
        for key, value in info.items():
            self.logger.info(f"  {key}: {value}")
