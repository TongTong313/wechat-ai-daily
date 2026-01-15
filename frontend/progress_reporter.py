"""
进度上报器

用于在测试执行过程中实时推送进度、日志、截图等信息到前端监控界面。
采用完全异步非阻塞设计，不影响 RPA 主流程执行。
"""

import asyncio
import base64
import json
import logging
from typing import Set, Optional, Dict, Any
from datetime import datetime
from pathlib import Path


class ProgressReporter:
    """进度上报器
    
    负责将测试执行过程中的各类信息推送到前端：
    - 当前操作状态
    - 实时截图
    - 日志消息
    - 进度统计
    - 采集到的文章
    
    设计原则：
    1. 完全非阻塞：所有推送都使用 create_task，不等待完成
    2. 错误隔离：推送失败只记录日志，不影响主流程
    3. 可选功能：如果没有连接的客户端，推送会被忽略
    4. 跨线程安全：支持从任意线程安全推送消息到服务器线程
    """
    
    def __init__(self, server_loop: Optional[asyncio.AbstractEventLoop] = None):
        """初始化进度上报器
        
        Args:
            server_loop: 服务器运行的事件循环（用于跨线程调用）
                        如果为 None，则只能在同一事件循环中使用
        """
        self.clients: Set[Any] = set()  # 连接的 WebSocket 客户端
        self.logger = logging.getLogger(__name__)
        self.screenshot_min_interval = 2.0  # 截图推送最小间隔（秒）
        self._last_screenshot_time = 0
        self.server_loop = server_loop  # 服务器线程的事件循环
        
    def add_client(self, websocket):
        """添加 WebSocket 客户端"""
        self.clients.add(websocket)
        self.logger.info(f"前端客户端已连接，当前连接数: {len(self.clients)}")
        
    def remove_client(self, websocket):
        """移除 WebSocket 客户端"""
        self.clients.discard(websocket)
        self.logger.info(f"前端客户端已断开，当前连接数: {len(self.clients)}")
        
    async def _broadcast(self, message: Dict[str, Any]):
        """向所有客户端广播消息（内部方法）
        
        Args:
            message: 要发送的消息字典
        """
        if not self.clients:
            return  # 没有客户端，直接返回
            
        message_json = json.dumps(message, ensure_ascii=False)
        
        # 收集断开的客户端
        disconnected = set()
        
        for client in self.clients:
            try:
                # 确保 client 是 WebSocket 对象并且已连接
                if hasattr(client, 'send_text'):
                    await client.send_text(message_json)
                elif hasattr(client, 'send'):
                    await client.send(message_json)
                else:
                    self.logger.warning(f"客户端对象不支持发送消息: {type(client)}")
                    disconnected.add(client)
            except Exception as e:
                self.logger.warning(f"向客户端发送消息失败: {e}")
                disconnected.add(client)
        
        # 移除断开的客户端
        for client in disconnected:
            self.remove_client(client)
    
    def _safe_broadcast(self, message: Dict[str, Any]):
        """安全的非阻塞广播（fire-and-forget），支持跨线程调用
        
        Args:
            message: 要发送的消息字典
        """
        try:
            # 尝试获取当前事件循环
            try:
                loop = asyncio.get_running_loop()
                # 如果成功获取到当前循环，直接创建任务
                loop.create_task(self._broadcast(message))
                return
            except RuntimeError:
                # 没有运行中的事件循环，尝试使用服务器循环（跨线程）
                pass
            
            # 如果设置了服务器循环，使用 run_coroutine_threadsafe 跨线程调用
            if self.server_loop is not None:
                asyncio.run_coroutine_threadsafe(
                    self._broadcast(message),
                    self.server_loop
                )
            else:
                # 既没有当前循环，也没有服务器循环，无法发送
                self.logger.debug("无可用事件循环，跳过消息推送")
                
        except Exception as e:
            # 即使创建任务失败也不影响主流程
            self.logger.warning(f"创建广播任务失败: {e}")
    
    def send_status(self, step: str, detail: str = ""):
        """发送当前操作状态
        
        Args:
            step: 当前步骤名称（如 "正在打开微信..."）
            detail: 详细信息（可选）
        """
        message = {
            "type": "status",
            "data": {
                "step": step,
                "detail": detail,
                "timestamp": datetime.now().isoformat()
            }
        }
        self._safe_broadcast(message)
        
    def send_screenshot(self, img_path: str):
        """发送截图（base64编码）
        
        Args:
            img_path: 截图文件路径
        """
        import time
        
        # 频率限制：避免过于频繁推送
        current_time = time.time()
        if current_time - self._last_screenshot_time < self.screenshot_min_interval:
            return  # 跳过此次推送
        
        self._last_screenshot_time = current_time
        
        # 支持跨线程调用
        try:
            # 尝试在当前循环中创建任务
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._encode_and_send_screenshot(img_path))
                return
            except RuntimeError:
                pass
            
            # 使用服务器循环（跨线程）
            if self.server_loop is not None:
                asyncio.run_coroutine_threadsafe(
                    self._encode_and_send_screenshot(img_path),
                    self.server_loop
                )
            else:
                self.logger.debug("无可用事件循环，跳过截图推送")
                
        except Exception as e:
            self.logger.warning(f"发送截图任务创建失败: {e}")
        
    async def _encode_and_send_screenshot(self, img_path: str):
        """异步编码并发送截图（内部方法）"""
        try:
            # 读取并编码图片
            with open(img_path, "rb") as f:
                img_data = f.read()
            
            # Base64 编码
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            message = {
                "type": "screenshot",
                "data": {
                    "image": img_base64,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            await self._broadcast(message)
            
        except Exception as e:
            self.logger.warning(f"发送截图失败: {e}")
    
    def send_log(self, level: str, message: str):
        """发送日志消息
        
        Args:
            level: 日志级别（info/warning/error/success）
            message: 日志内容
        """
        log_message = {
            "type": "log",
            "data": {
                "level": level.lower(),
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        }
        self._safe_broadcast(log_message)
        
    def send_progress(self, current: int, total: int):
        """发送进度信息
        
        Args:
            current: 当前完成数量
            total: 总数量
        """
        message = {
            "type": "progress",
            "data": {
                "current": current,
                "total": total,
                "timestamp": datetime.now().isoformat()
            }
        }
        self._safe_broadcast(message)
        
    def send_article(self, title: str = "", link: str = "", date: str = ""):
        """发送采集到的文章信息
        
        Args:
            title: 文章标题（可选）
            link: 文章链接
            date: 发布日期（可选）
        """
        message = {
            "type": "article",
            "data": {
                "title": title,
                "link": link,
                "date": date,
                "timestamp": datetime.now().isoformat()
            }
        }
        self._safe_broadcast(message)
        
    def send_stats(self, **kwargs):
        """发送统计数据
        
        Args:
            **kwargs: 统计数据（如 articles=10, accounts=2）
        """
        message = {
            "type": "stats",
            "data": kwargs
        }
        self._safe_broadcast(message)
        
    def send_workflow_start(self, total_accounts: int):
        """发送工作流启动信号
        
        Args:
            total_accounts: 公众号总数
        """
        message = {
            "type": "workflow_start",
            "data": {
                "total_accounts": total_accounts,
                "timestamp": datetime.now().isoformat()
            }
        }
        self._safe_broadcast(message)
        self.send_log("info", f"工作流启动，共 {total_accounts} 个公众号待采集")
        
    def send_workflow_end(self, success: bool, error: Optional[str] = None, stats: Optional[Dict] = None):
        """发送工作流结束信号
        
        Args:
            success: 是否成功
            error: 错误信息（如果失败）
            stats: 统计数据（可选）
        """
        message = {
            "type": "workflow_end",
            "data": {
                "success": success,
                "error": error,
                "stats": stats or {},
                "timestamp": datetime.now().isoformat()
            }
        }
        self._safe_broadcast(message)
        
        if success:
            self.send_log("success", "工作流执行完成")
        else:
            self.send_log("error", f"工作流执行失败: {error}")
