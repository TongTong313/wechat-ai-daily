"""
前端监控服务器

FastAPI + WebSocket 服务器，用于：
1. 托管前端 HTML 页面
2. 建立 WebSocket 连接
3. 转发测试进度信息到前端
4. 接收前端控制命令（启动/停止测试）
"""

import asyncio
import logging
import json
import threading
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# 获取当前文件所在目录
FRONTEND_DIR = Path(__file__).parent

# 创建 FastAPI 应用
app = FastAPI(title="微信公众号自动化测试监控")

# 全局 ProgressReporter（由测试代码注入）
_progress_reporter = None

# 控制信号（使用 threading.Event 而不是 asyncio.Event，因为跨线程）
_start_event = threading.Event()  # 启动信号
_stop_event = threading.Event()   # 停止信号


def set_progress_reporter(reporter):
    """设置全局的 ProgressReporter 实例
    
    由测试代码调用，将 reporter 注入到服务器中
    """
    global _progress_reporter
    _progress_reporter = reporter
    logging.info("ProgressReporter 已注入到服务器")


def get_start_event():
    """获取启动事件（供测试代码等待）"""
    return _start_event


def get_stop_event():
    """获取停止事件（供测试代码检查）"""
    return _stop_event


def reset_events():
    """重置所有事件"""
    global _start_event, _stop_event
    # 创建新的事件对象，而不是仅清除
    # 这样可以确保之前等待事件的线程不会受影响
    _start_event = threading.Event()
    _stop_event = threading.Event()
    logging.info("事件已重置（创建了新的事件对象）")


@app.get("/", response_class=HTMLResponse)
async def get_index():
    """返回前端 HTML 页面"""
    index_file = FRONTEND_DIR / "index.html"
    with open(index_file, "r", encoding="utf-8") as f:
        return f.read()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接端点"""
    await websocket.accept()
    
    # 将客户端添加到 reporter
    if _progress_reporter:
        _progress_reporter.add_client(websocket)
    
    try:
        # 保持连接，接收前端消息
        while True:
            data = await websocket.receive_text()
            
            # 解析前端发送的命令
            try:
                message = json.loads(data)
                action = message.get('action')
                
                if action == 'start':
                    logging.info("收到前端启动命令")
                    _start_event.set()  # 触发启动信号
                    
                elif action == 'stop':
                    logging.info("收到前端停止命令")
                    _stop_event.set()  # 触发停止信号
                    
                else:
                    logging.warning(f"未知的前端命令: {action}")
                    
            except json.JSONDecodeError:
                logging.warning(f"无法解析前端消息: {data}")
            
    except WebSocketDisconnect:
        logging.info("WebSocket 客户端断开连接")
    except Exception as e:
        logging.error(f"WebSocket 错误: {e}")
    finally:
        # 移除客户端
        if _progress_reporter:
            _progress_reporter.remove_client(websocket)


def start_server(host: str = "127.0.0.1", port: int = 8765, reporter=None):
    """启动前端监控服务器
    
    Args:
        host: 服务器地址
        port: 服务器端口
        reporter: ProgressReporter 实例
    """
    if reporter:
        set_progress_reporter(reporter)
    
    # 重置事件
    reset_events()
    
    logging.info(f"启动前端监控服务器: http://{host}:{port}")
    logging.info(f"WebSocket 地址: ws://{host}:{port}/ws")
    
    # 启动服务器前，将事件循环注入到 reporter
    # uvicorn 会在当前线程创建并运行事件循环
    # 我们需要在服务器运行时获取这个循环的引用
    
    # 创建自定义的服务器配置
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    
    # 运行服务器（会创建新的事件循环）
    # 在服务器启动回调中注入事件循环到 reporter
    import asyncio
    
    async def serve_with_loop_injection():
        """启动服务器并注入事件循环到 reporter"""
        # 获取当前事件循环
        loop = asyncio.get_running_loop()
        
        # 注入到 reporter
        if _progress_reporter:
            _progress_reporter.server_loop = loop
            logging.info("事件循环已注入到 ProgressReporter")
        
        # 启动服务器
        await server.serve()
    
    # 运行服务器
    asyncio.run(serve_with_loop_injection())


if __name__ == "__main__":
    # 直接运行服务器（用于调试）
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    start_server()
