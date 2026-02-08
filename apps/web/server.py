# -*- coding: utf-8 -*-
"""
Web 端服务入口

提供：
- 静态前端页面
- 工作流控制 API
- WebSocket 实时日志与进度推送
"""

from __future__ import annotations

import asyncio
import logging
import os
import queue
from collections import deque
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from apps.desktop.utils.config_manager import ConfigManager
from wechat_ai_daily.workflows import (
    APIArticleCollector,
    DailyGenerator,
    DailyPublisher,
    RPAArticleCollector,
)
from wechat_ai_daily.workflows.base import CancelledError

# ==================== 基础路径 ====================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UI_DIR = PROJECT_ROOT / "apps" / "web" / "ui"
OUTPUT_DIR = PROJECT_ROOT / "output"
CONFIG_PATH = PROJECT_ROOT / "configs" / "config.yaml"

# 统一设置项目根目录，便于 ConfigManager 读取
os.environ.setdefault("WECHAT_AI_DAILY_ROOT", str(PROJECT_ROOT))


# ==================== 工具函数 ====================

def _parse_datetime_str(value: Any, field_name: str) -> Optional[datetime]:
    """解析日期时间字符串（支持 YYYY-MM-DD 或 YYYY-MM-DD HH:mm）"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M")
        except ValueError:
            pass
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            logging.warning(
                f"无法解析 {field_name} '{value}'，格式应为 'YYYY-MM-DD HH:mm' 或 'YYYY-MM-DD'"
            )
            return None
    return None


def _safe_output_path(relative_path: str) -> Path:
    """将前端传入的相对路径安全映射到 output 目录"""
    if not relative_path:
        raise HTTPException(status_code=400, detail="文件路径不能为空")
    candidate = (OUTPUT_DIR / relative_path).resolve()
    if not candidate.is_relative_to(OUTPUT_DIR.resolve()):
        raise HTTPException(status_code=400, detail="非法的文件路径")
    if not candidate.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return candidate


def _normalize_config(value: Any) -> Any:
    """将配置中的日期类型转换为字符串，保证可序列化"""
    if isinstance(value, dict):
        return {key: _normalize_config(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_config(item) for item in value]
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return value


# ==================== WebSocket 管理 ====================

class WebSocketManager:
    """管理 WebSocket 连接并广播消息"""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, payload: Dict[str, Any]) -> None:
        async with self._lock:
            connections = list(self._connections)
        if not connections:
            return
        remove_list = []
        for ws in connections:
            try:
                await ws.send_json(payload)
            except Exception:
                remove_list.append(ws)
        if remove_list:
            async with self._lock:
                for ws in remove_list:
                    self._connections.discard(ws)


# ==================== 日志缓冲 ====================

class WebLogBuffer(logging.Handler):
    """缓存日志并推送到 WebSocket

    使用线程安全的 queue.Queue 替代 asyncio.Queue，
    确保在同步代码阻塞事件循环时，日志仍能被正确缓存和推送。
    """

    def __init__(self, max_lines: int = 2000) -> None:
        super().__init__(logging.INFO)
        self._lines: deque[Dict[str, Any]] = deque(maxlen=max_lines)
        # 使用线程安全的队列，避免事件循环阻塞时日志丢失
        self._queue: queue.Queue[Dict[str, Any]] = queue.Queue()
        self.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)-5s %(message)s",
            datefmt="%H:%M:%S"
        ))

    def emit(self, record: logging.LogRecord) -> None:
        """写入日志缓存并投递到队列"""
        try:
            text = self.format(record)
            entry = {
                "text": text,
                "level": record.levelname,
                "time": datetime.now().strftime("%H:%M:%S"),
            }
            self._lines.append(entry)
            # 直接放入线程安全队列，无需依赖事件循环
            self._queue.put_nowait(entry)
        except Exception:
            self.handleError(record)

    async def consume(self, ws_manager: WebSocketManager) -> None:
        """持续消费日志并广播"""
        loop = asyncio.get_running_loop()
        while True:
            # 使用 run_in_executor 在线程池中等待队列，避免阻塞事件循环
            entry = await loop.run_in_executor(None, self._queue.get)
            await ws_manager.broadcast({"type": "log", **entry})

    def list_lines(self) -> List[Dict[str, Any]]:
        """获取当前日志缓存"""
        return list(self._lines)


# ==================== 工作流状态 ====================

class WorkflowState:
    """工作流运行状态（线程安全）"""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._state: Dict[str, Any] = {
            "running": False,
            "workflow": None,
            "mode": None,
            "progress": 0,
            "status": "就绪",
            "detail": "",
            "output": "",
            "error": "",
            "started_at": None,
            "finished_at": None,
        }

    async def update(self, **kwargs: Any) -> None:
        async with self._lock:
            self._state.update(kwargs)

    async def snapshot(self) -> Dict[str, Any]:
        async with self._lock:
            return dict(self._state)


# ==================== 工作流请求模型 ====================

class SaveOptions(BaseModel):
    api_key_to_env: bool = False
    api_token_to_env: bool = False
    api_cookie_to_env: bool = False
    appid_to_env: bool = False
    appsecret_to_env: bool = False


class ApiConfigPayload(BaseModel):
    token: Optional[str] = None
    cookie: Optional[str] = None
    account_names: Optional[List[str]] = None


class ModelConfigPayload(BaseModel):
    model: Optional[str] = None
    api_key: Optional[str] = None
    thinking_budget: Optional[int] = None
    enable_thinking: Optional[bool] = None


class PublishConfigPayload(BaseModel):
    appid: Optional[str] = None
    appsecret: Optional[str] = None
    author: Optional[str] = None
    cover_path: Optional[str] = None
    default_title: Optional[str] = None
    digest: Optional[str] = None


class GuiConfigPayload(BaseModel):
    search_website: Optional[str] = None
    three_dots: Optional[str] = None
    turnback: Optional[str] = None


class ConfigUpdateRequest(BaseModel):
    target_date: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    article_urls: Optional[List[str]] = None
    api_config: Optional[ApiConfigPayload] = None
    llm: Optional[ModelConfigPayload] = None
    vlm: Optional[ModelConfigPayload] = None
    publish_config: Optional[PublishConfigPayload] = None
    gui_config: Optional[GuiConfigPayload] = None
    save_options: SaveOptions = Field(default_factory=SaveOptions)


class WorkflowStartRequest(BaseModel):
    workflow: str = Field(..., description="collect|generate|publish|full")
    mode: str = Field("api", description="api|rpa")
    markdown_file: Optional[str] = None
    html_file: Optional[str] = None
    title: Optional[str] = None
    target_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


# ==================== 工作流执行器 ====================

@dataclass
class WorkflowParams:
    workflow: str
    mode: str
    markdown_file: Optional[str]
    html_file: Optional[str]
    title: Optional[str]
    target_date: datetime
    start_time: Optional[datetime]
    end_time: Optional[datetime]


class WorkflowRunner:
    """负责执行工作流并推送进度"""

    def __init__(self, state: WorkflowState, ws_manager: WebSocketManager) -> None:
        self._state = state
        self._ws_manager = ws_manager
        self._task: Optional[asyncio.Task] = None
        self._cancel_event = asyncio.Event()
        self._lock = asyncio.Lock()

    async def start(self, params: WorkflowParams) -> None:
        async with self._lock:
            if self._task and not self._task.done():
                raise HTTPException(status_code=409, detail="已有任务在运行中")
            self._cancel_event = asyncio.Event()
            self._task = asyncio.create_task(self._run(params))

    async def stop(self) -> None:
        """请求停止当前工作流"""
        self._cancel_event.set()
        await self._state.update(status="正在停止...", detail="用户请求取消任务")
        await self._broadcast_progress()

    def _is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    async def _run(self, params: WorkflowParams) -> None:
        await self._state.update(
            running=True,
            workflow=params.workflow,
            mode=params.mode,
            progress=0,
            status="启动中",
            detail="初始化工作流...",
            output="",
            error="",
            started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            finished_at=None,
        )
        await self._broadcast_progress()

        try:
            if params.workflow == "collect":
                output = await self._run_collect(params)
                await self._finish_success(output)
            elif params.workflow == "generate":
                output = await self._run_generate(params)
                await self._finish_success(output)
            elif params.workflow == "publish":
                output = await self._run_publish(params)
                await self._finish_success(output)
            elif params.workflow == "full":
                output = await self._run_full(params)
                await self._finish_success(output)
            else:
                raise ValueError("未知的工作流类型")
        except CancelledError:
            await self._finish_cancelled()
        except Exception as exc:
            # 统一记录异常堆栈，确保错误能被前端日志面板看到
            error_message = str(exc).strip()
            if not error_message:
                # 某些异常没有消息，避免前端只显示“等待执行”
                error_message = f"{exc.__class__.__name__}（未提供错误信息）"
            logging.exception("工作流执行失败: %s", error_message)
            await self._finish_error(error_message)

    async def _finish_success(self, output: str) -> None:
        await self._state.update(
            running=False,
            progress=100,
            status="完成",
            detail="工作流执行完成",
            output=output,
            finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        await self._broadcast_progress()

    async def _finish_cancelled(self) -> None:
        await self._state.update(
            running=False,
            progress=0,
            status="已取消",
            detail="用户取消了任务",
            finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        await self._broadcast_progress()

    async def _finish_error(self, message: str) -> None:
        # 防止空错误导致前端状态详情为空
        safe_message = message.strip() if message else ""
        if not safe_message:
            safe_message = "工作流执行失败，详情见日志"
        await self._state.update(
            running=False,
            progress=0,
            status="失败",
            detail=safe_message,
            error=safe_message,
            finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        await self._broadcast_progress()

    async def _broadcast_progress(self) -> None:
        state = await self._state.snapshot()
        await self._ws_manager.broadcast({"type": "progress", **state})

    async def _run_collect(self, params: WorkflowParams) -> str:
        mode_text = "API" if params.mode == "api" else "RPA"
        await self._state.update(
            progress=0,
            status=f"正在采集公众号文章 ({mode_text}模式)",
            detail="初始化采集器...",
        )
        await self._broadcast_progress()

        if params.mode == "api":
            collector = APIArticleCollector(config=str(CONFIG_PATH))
            collector.set_cancel_checker(self._is_cancelled)
            await self._state.update(
                progress=10,
                status=f"正在采集公众号文章 ({mode_text}模式)",
                detail="采集器已初始化，开始采集...",
            )
            await self._broadcast_progress()
            output_file = await asyncio.to_thread(collector.run)
        else:
            collector = RPAArticleCollector(config=str(CONFIG_PATH))
            collector.set_cancel_checker(self._is_cancelled)
            await self._state.update(
                progress=10,
                status=f"正在采集公众号文章 ({mode_text}模式)",
                detail="采集器已初始化，开始采集...",
            )
            await self._broadcast_progress()
            output_file = await collector.run()

        if self._is_cancelled():
            raise CancelledError()

        await self._state.update(
            progress=100,
            status="采集完成",
            detail=f"输出文件: {output_file}",
        )
        await self._broadcast_progress()
        return output_file

    async def _run_generate(self, params: WorkflowParams) -> str:
        if not params.markdown_file:
            raise ValueError("生成内容需要提供 Markdown 文件")

        # 将相对路径转换为完整路径
        markdown_path = str(OUTPUT_DIR / params.markdown_file)

        await self._state.update(
            progress=0,
            status="正在生成公众号文章内容",
            detail="初始化生成器...",
        )
        await self._broadcast_progress()

        generator = DailyGenerator(config=str(CONFIG_PATH))
        generator.set_cancel_checker(self._is_cancelled)

        await self._state.update(
            progress=10,
            status="正在生成公众号文章内容",
            detail="生成器已初始化，开始生成...",
        )
        await self._broadcast_progress()

        start_time = params.start_time if params.mode == "api" else None
        end_time = params.end_time if params.mode == "api" else None
        output_file = await generator.run(
            markdown_file=markdown_path,
            date=params.target_date,
            start_time=start_time,
            end_time=end_time,
        )

        if self._is_cancelled():
            raise CancelledError()

        await self._state.update(
            progress=100,
            status="公众号文章内容生成完成",
            detail=f"输出文件: {output_file}",
        )
        await self._broadcast_progress()
        return output_file or ""

    async def _run_publish(self, params: WorkflowParams) -> str:
        if not params.html_file:
            raise ValueError("发布草稿需要提供 HTML 文件")

        # 将相对路径转换为完整路径
        html_path = str(OUTPUT_DIR / params.html_file)

        await self._state.update(
            progress=0,
            status="正在发布草稿",
            detail="初始化发布器...",
        )
        await self._broadcast_progress()

        publisher = DailyPublisher(config=str(CONFIG_PATH))
        publisher.set_cancel_checker(self._is_cancelled)

        await self._state.update(
            progress=20,
            status="正在发布草稿",
            detail="发布器已初始化，开始发布...",
        )
        await self._broadcast_progress()

        title = params.title or f"AI日报 - {params.target_date.strftime('%Y-%m-%d')}"
        # 从配置读取摘要描述
        cfg_manager = ConfigManager(str(CONFIG_PATH))
        cfg_manager.load_config()
        digest = cfg_manager.get_publish_digest()
        draft_media_id = await asyncio.to_thread(
            publisher.run,
            html_path=html_path,
            title=title,
            digest=digest,
        )

        if self._is_cancelled():
            raise CancelledError()

        await self._state.update(
            progress=100,
            status="发布完成",
            detail=f"草稿 media_id: {draft_media_id}",
        )
        await self._broadcast_progress()
        return f"draft:{draft_media_id}"

    async def _run_full(self, params: WorkflowParams) -> str:
        mode_text = "API" if params.mode == "api" else "RPA"
        await self._state.update(
            progress=0,
            status=f"阶段 1/3: 采集公众号文章 ({mode_text}模式)",
            detail="初始化采集器...",
        )
        await self._broadcast_progress()

        # 阶段 1：采集
        if params.mode == "api":
            collector = APIArticleCollector(config=str(CONFIG_PATH))
            collector.set_cancel_checker(self._is_cancelled)
            await self._state.update(
                progress=5,
                status=f"阶段 1/3: 采集公众号文章 ({mode_text}模式)",
                detail="采集器已初始化，开始采集...",
            )
            await self._broadcast_progress()
            markdown_file = await asyncio.to_thread(collector.run)
        else:
            collector = RPAArticleCollector(config=str(CONFIG_PATH))
            collector.set_cancel_checker(self._is_cancelled)
            await self._state.update(
                progress=5,
                status=f"阶段 1/3: 采集公众号文章 ({mode_text}模式)",
                detail="采集器已初始化，开始采集...",
            )
            await self._broadcast_progress()
            markdown_file = await collector.run()

        if self._is_cancelled():
            raise CancelledError()

        await self._state.update(
            progress=33,
            status="阶段 1/3: 采集完成",
            detail=f"已采集到文章链接: {markdown_file}",
        )
        await self._broadcast_progress()

        # 阶段 2：生成
        generator = DailyGenerator(config=str(CONFIG_PATH))
        generator.set_cancel_checker(self._is_cancelled)
        await self._state.update(
            progress=35,
            status="阶段 2/3: 生成公众号文章内容",
            detail="初始化生成器...",
        )
        await self._broadcast_progress()

        await self._state.update(
            progress=40,
            status="阶段 2/3: 生成公众号文章内容",
            detail="生成器已初始化，开始生成...",
        )
        await self._broadcast_progress()

        start_time = params.start_time if params.mode == "api" else None
        end_time = params.end_time if params.mode == "api" else None
        html_file = await generator.run(
            markdown_file=markdown_file,
            date=params.target_date,
            start_time=start_time,
            end_time=end_time,
        )

        if self._is_cancelled():
            raise CancelledError()

        await self._state.update(
            progress=66,
            status="阶段 2/3: 生成完成",
            detail=f"公众号文章内容文件: {html_file}",
        )
        await self._broadcast_progress()

        # 阶段 3：发布
        publisher = DailyPublisher(config=str(CONFIG_PATH))
        publisher.set_cancel_checker(self._is_cancelled)
        await self._state.update(
            progress=70,
            status="阶段 3/3: 发布到公众号草稿",
            detail="初始化发布器...",
        )
        await self._broadcast_progress()

        await self._state.update(
            progress=75,
            status="阶段 3/3: 发布到公众号草稿",
            detail="发布器已初始化，开始发布...",
        )
        await self._broadcast_progress()

        title = params.title or f"AI日报 - {params.target_date.strftime('%Y-%m-%d')}"
        # 从配置读取摘要描述
        cfg_manager = ConfigManager(str(CONFIG_PATH))
        cfg_manager.load_config()
        digest = cfg_manager.get_publish_digest()
        draft_media_id = await asyncio.to_thread(
            publisher.run,
            html_path=html_file,
            title=title,
            digest=digest,
        )

        if self._is_cancelled():
            raise CancelledError()

        await self._state.update(
            progress=100,
            status="全部完成",
            detail=f"草稿 media_id: {draft_media_id}",
        )
        await self._broadcast_progress()
        return f"draft:{draft_media_id}"


# ==================== FastAPI 实例 ====================

app = FastAPI(title="Wechat AI Daily Web")
ws_manager = WebSocketManager()
state_store = WorkflowState()
runner = WorkflowRunner(state_store, ws_manager)
log_buffer = WebLogBuffer(max_lines=2000)


def _setup_logging() -> None:
    """配置日志，追加 Web 日志处理器"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if not any(isinstance(h, WebLogBuffer) for h in root_logger.handlers):
        root_logger.addHandler(log_buffer)


@app.on_event("startup")
async def _on_startup() -> None:
    """启动时配置日志与后台任务"""
    _setup_logging()
    app.state.log_task = asyncio.create_task(log_buffer.consume(ws_manager))


# ==================== 静态资源 ====================

if UI_DIR.exists():
    app.mount("/static", StaticFiles(directory=UI_DIR), name="static")


@app.get("/")
async def index() -> FileResponse:
    index_file = UI_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="前端资源未构建")
    return FileResponse(index_file)


# ==================== API：配置 ====================

@app.get("/api/config")
async def get_config() -> Dict[str, Any]:
    manager = ConfigManager(str(CONFIG_PATH))
    manager.load_config()

    api_key, api_key_source = manager.get_api_key_with_source()
    token, token_source = manager.get_api_token_with_source()
    cookie, cookie_source = manager.get_api_cookie_with_source()
    appid, appid_source = manager.get_wechat_appid()
    appsecret, appsecret_source = manager.get_wechat_appsecret()

    return {
        "config": _normalize_config(manager.config),
        "sources": {
            "api_key": api_key_source,
            "api_token": token_source,
            "api_cookie": cookie_source,
            "wechat_appid": appid_source,
            "wechat_appsecret": appsecret_source,
        },
        "masked": {
            "api_key": api_key or "",
            "api_token": token or "",
            "api_cookie": cookie or "",
            "wechat_appid": appid or "",
            "wechat_appsecret": appsecret or "",
        },
    }


@app.post("/api/config")
async def update_config(payload: ConfigUpdateRequest) -> Dict[str, Any]:
    manager = ConfigManager(str(CONFIG_PATH))
    manager.load_config()

    # 时间配置
    if payload.target_date is not None:
        manager.set_target_date(payload.target_date or None)
    if payload.start_date is not None:
        manager.set_start_date(payload.start_date or None)
    if payload.end_date is not None:
        manager.set_end_date(payload.end_date or None)

    # RPA 文章链接
    if payload.article_urls is not None:
        manager.set_article_urls(payload.article_urls)

    # API 配置
    if payload.api_config:
        if payload.api_config.account_names is not None:
            manager.set_account_names(payload.api_config.account_names)
        if payload.api_config.token is not None:
            manager.set_api_token(
                payload.api_config.token,
                save_to_env=payload.save_options.api_token_to_env,
            )
        if payload.api_config.cookie is not None:
            manager.set_api_cookie(
                payload.api_config.cookie,
                save_to_env=payload.save_options.api_cookie_to_env,
            )

    # 模型配置
    if payload.llm:
        if payload.llm.model is not None:
            manager.set_llm_model(payload.llm.model)
        if payload.llm.enable_thinking is not None:
            manager.set_enable_thinking(payload.llm.enable_thinking)
        if payload.llm.thinking_budget is not None:
            manager.set_thinking_budget(payload.llm.thinking_budget)
        if payload.llm.api_key is not None:
            manager.set_api_key(
                payload.llm.api_key,
                save_to_env=payload.save_options.api_key_to_env,
            )

    if payload.vlm:
        if payload.vlm.model is not None:
            manager.set_vlm_model(payload.vlm.model)

    # 发布配置
    if payload.publish_config:
        if payload.publish_config.appid is not None:
            manager.set_wechat_appid(
                payload.publish_config.appid,
                save_to_config=not payload.save_options.appid_to_env,
            )
        if payload.publish_config.appsecret is not None:
            manager.set_wechat_appsecret(
                payload.publish_config.appsecret,
                save_to_config=not payload.save_options.appsecret_to_env,
            )
        if payload.publish_config.author is not None:
            manager.set_publish_author(payload.publish_config.author)
        if payload.publish_config.cover_path is not None:
            manager.set_publish_cover_path(payload.publish_config.cover_path)
        if payload.publish_config.default_title is not None:
            manager.set_publish_title(payload.publish_config.default_title)
        if payload.publish_config.digest is not None:
            manager.set_publish_digest(payload.publish_config.digest)

    # GUI 模板配置（RPA 识别用）
    if payload.gui_config:
        if payload.gui_config.search_website is not None:
            manager.set_gui_template_path("search_website", payload.gui_config.search_website)
        if payload.gui_config.three_dots is not None:
            manager.set_gui_template_path("three_dots", payload.gui_config.three_dots)
        if payload.gui_config.turnback is not None:
            manager.set_gui_template_path("turnback", payload.gui_config.turnback)

    if not manager.save_config():
        raise HTTPException(status_code=500, detail="保存配置失败")

    return await get_config()


# ==================== API：工作流控制 ====================

@app.post("/api/workflow/start")
async def start_workflow(payload: WorkflowStartRequest) -> Dict[str, Any]:
    manager = ConfigManager(str(CONFIG_PATH))
    manager.load_config()

    # 解析日期参数
    target_date = _parse_datetime_str(payload.target_date, "target_date")
    start_time = _parse_datetime_str(payload.start_time, "start_time")
    end_time = _parse_datetime_str(payload.end_time, "end_time")

    if payload.mode == "api":
        if start_time is None or end_time is None:
            start_time = _parse_datetime_str(manager.get_start_date(), "start_date")
            end_time = _parse_datetime_str(manager.get_end_date(), "end_date")
        target_date = target_date or start_time or datetime.now()
    else:
        if target_date is None:
            target_date = _parse_datetime_str(manager.get_target_date(), "target_date") or datetime.now()

    params = WorkflowParams(
        workflow=payload.workflow,
        mode=payload.mode,
        markdown_file=payload.markdown_file,
        html_file=payload.html_file,
        title=payload.title,
        target_date=target_date,
        start_time=start_time,
        end_time=end_time,
    )
    await runner.start(params)
    return {"ok": True}


@app.post("/api/workflow/stop")
async def stop_workflow() -> Dict[str, Any]:
    await runner.stop()
    return {"ok": True}


@app.get("/api/status")
async def get_status() -> Dict[str, Any]:
    return await state_store.snapshot()


# ==================== API：日志与文件 ====================

@app.get("/api/logs")
async def get_logs() -> Dict[str, Any]:
    return {"lines": log_buffer.list_lines()}


@app.get("/api/files")
async def list_files(file_type: str = "markdown") -> Dict[str, Any]:
    if not OUTPUT_DIR.exists():
        return {"files": []}
    if file_type == "markdown":
        pattern = "articles_*.md"
    elif file_type == "html":
        pattern = "daily_rich_text_*.html"
    else:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    files = sorted(OUTPUT_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    result = []
    for path in files:
        result.append({
            "name": path.name,
            "path": path.relative_to(OUTPUT_DIR).as_posix(),
            "size": path.stat().st_size,
            "mtime": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return {"files": result}


@app.get("/api/file")
async def get_file(path: str) -> FileResponse:
    file_path = _safe_output_path(path)
    return FileResponse(file_path)


# ==================== WebSocket：实时推送 ====================

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        # 连接建立后，先推送当前状态与日志
        await websocket.send_json({"type": "progress", **(await state_store.snapshot())})
        for line in log_buffer.list_lines():
            await websocket.send_json({"type": "log", **line})
        while True:
            # 保持连接活跃，忽略前端发送的数据
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)
