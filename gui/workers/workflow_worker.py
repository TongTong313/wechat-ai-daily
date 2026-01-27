# -*- coding: utf-8 -*-
"""
工作流后台线程

在后台线程中执行公众号文章采集、日报生成和发布工作流，避免阻塞 UI。
"""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Optional, Callable
from enum import Enum, auto
from PyQt6.QtCore import QThread, pyqtSignal

# 导入工作流模块（从 src 中导入）
from wechat_ai_daily.workflows import DailyGenerator, RPAArticleCollector, APIArticleCollector, DailyPublisher
from wechat_ai_daily.workflows.base import CancelledError


class WorkflowType(Enum):
    """工作流类型枚举"""
    COLLECT = auto()      # 仅采集文章
    GENERATE = auto()     # 仅生成日报
    PUBLISH = auto()      # 仅发布草稿
    FULL = auto()         # 完整流程（采集 + 生成 + 发布）


class WorkflowWorker(QThread):
    """工作流执行线程

    在后台线程中执行异步工作流，通过信号与 UI 线程通信。

    Signals:
        started_signal: 工作流开始时发出
        progress: 进度更新信号 (进度值 0-100, 状态文本, 详细信息)
        finished_signal: 工作流完成时发出 (是否成功, 结果消息, 输出文件路径)
        error: 发生错误时发出 (错误消息)
    """

    # 信号定义
    started_signal = pyqtSignal()
    progress = pyqtSignal(int, str, str)  # (进度值, 状态文本, 详细信息)
    finished_signal = pyqtSignal(bool, str, str)  # (成功, 消息, 输出文件)
    error = pyqtSignal(str)

    def __init__(
        self,
        config_path: str,
        workflow_type: WorkflowType,
        target_date: datetime,
        collect_mode: str = "api",
        markdown_file: Optional[str] = None,
        html_file: Optional[str] = None,
        title: Optional[str] = None,
        parent=None
    ):
        """初始化工作流线程

        Args:
            config_path: 配置文件路径
            workflow_type: 工作流类型
            target_date: 目标日期
            collect_mode: 采集模式，'api' 或 'rpa'，默认 'api'
            markdown_file: 文章链接文件路径（仅生成日报时需要）
            html_file: HTML 日报文件路径（仅发布草稿时需要）
            title: 文章标题（仅发布草稿时需要，为空则自动生成）
            parent: 父对象
        """
        super().__init__(parent)
        self.config_path = config_path
        self.workflow_type = workflow_type
        self.target_date = target_date
        self.collect_mode = collect_mode
        self.markdown_file = markdown_file
        self.html_file = html_file
        self.title = title
        self._is_cancelled = False

    def cancel(self) -> None:
        """取消工作流执行"""
        self._is_cancelled = True
        logging.warning("用户请求取消工作流")

    def run(self) -> None:
        """线程执行入口"""
        self.started_signal.emit()

        try:
            # 创建新的事件循环（因为在新线程中）
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 根据工作流类型执行对应任务
                if self.workflow_type == WorkflowType.COLLECT:
                    loop.run_until_complete(self._run_collect())
                elif self.workflow_type == WorkflowType.GENERATE:
                    loop.run_until_complete(self._run_generate())
                elif self.workflow_type == WorkflowType.PUBLISH:
                    loop.run_until_complete(self._run_publish())
                elif self.workflow_type == WorkflowType.FULL:
                    loop.run_until_complete(self._run_full())
            finally:
                loop.close()

        except Exception as e:
            error_msg = f"工作流执行失败: {str(e)}"
            logging.exception(error_msg)
            self.error.emit(error_msg)
            self.finished_signal.emit(False, error_msg, "")

    async def _run_collect(self) -> None:
        """执行文章采集工作流

        根据 collect_mode 选择使用 API 模式或 RPA 模式采集器。
        """
        mode_text = "API" if self.collect_mode == "api" else "RPA"

        logging.info("=" * 50)
        logging.info("开始执行文章采集工作流")
        logging.info(f"采集模式: {mode_text}")
        logging.info(f"目标日期: {self.target_date.strftime('%Y-%m-%d')}")
        logging.info("=" * 50)

        self.progress.emit(0, f"正在采集公众号文章 ({mode_text}模式)", "初始化采集器...")

        try:
            if self.collect_mode == "api":
                # API 模式：使用 APIArticleCollector（同步方法）
                collector = APIArticleCollector(config=self.config_path)
                # 设置取消检查回调
                collector.set_cancel_checker(lambda: self._is_cancelled)

                self.progress.emit(
                    10, f"正在采集公众号文章 ({mode_text}模式)", "采集器已初始化，开始采集...")

                # 执行采集（同步调用）
                output_file = collector.run()
            else:
                # RPA 模式：使用 RPAArticleCollector（异步方法）
                collector = RPAArticleCollector(config=self.config_path)
                # 设置取消检查回调
                collector.set_cancel_checker(lambda: self._is_cancelled)

                self.progress.emit(
                    10, f"正在采集公众号文章 ({mode_text}模式)", "采集器已初始化，开始采集...")

                # 执行采集（异步调用）
                output_file = await collector.run()

            if self._is_cancelled:
                self.finished_signal.emit(False, "用户取消了操作", "")
                return

            self.progress.emit(100, "采集完成", f"输出文件: {output_file}")
            logging.info(f"文章采集完成，输出文件: {output_file}")

            self.finished_signal.emit(True, "文章采集完成", output_file)

        except CancelledError:
            # 工作流被用户取消
            logging.info("文章采集已被用户取消")
            self.finished_signal.emit(False, "用户取消了操作", "")
        except Exception as e:
            raise Exception(f"文章采集失败: {str(e)}") from e

    async def _run_generate(self) -> None:
        """执行日报生成工作流"""
        if not self.markdown_file:
            raise ValueError("生成日报需要提供文章链接文件路径")

        logging.info("=" * 50)
        logging.info("开始执行日报生成工作流")
        logging.info(f"输入文件: {self.markdown_file}")
        logging.info(f"目标日期: {self.target_date.strftime('%Y-%m-%d')}")
        logging.info("=" * 50)

        self.progress.emit(0, "正在生成日报", "初始化生成器...")

        try:
            # 创建生成器
            generator = DailyGenerator(config=self.config_path)
            # 设置取消检查回调
            generator.set_cancel_checker(lambda: self._is_cancelled)

            self.progress.emit(10, "正在生成日报", "生成器已初始化，开始生成...")

            # 执行生成
            output_file = await generator.run(
                markdown_file=self.markdown_file,
                date=self.target_date
            )

            if self._is_cancelled:
                self.finished_signal.emit(False, "用户取消了操作", "")
                return

            self.progress.emit(100, "日报生成完成", f"输出文件: {output_file}")
            logging.info(f"日报生成完成，输出文件: {output_file}")

            self.finished_signal.emit(True, "日报生成完成", output_file or "")

        except CancelledError:
            # 工作流被用户取消
            logging.info("日报生成已被用户取消")
            self.finished_signal.emit(False, "用户取消了操作", "")
        except Exception as e:
            raise Exception(f"日报生成失败: {str(e)}") from e

    async def _run_publish(self) -> None:
        """执行发布草稿工作流"""
        if not self.html_file:
            raise ValueError("发布草稿需要提供 HTML 日报文件路径")

        logging.info("=" * 50)
        logging.info("开始执行发布草稿工作流")
        logging.info(f"输入文件: {self.html_file}")
        logging.info(f"目标日期: {self.target_date.strftime('%Y-%m-%d')}")
        logging.info("=" * 50)

        self.progress.emit(0, "正在发布草稿", "初始化发布器...")

        try:
            # 创建发布器
            publisher = DailyPublisher(config=self.config_path)
            # 设置取消检查回调
            publisher.set_cancel_checker(lambda: self._is_cancelled)

            self.progress.emit(20, "正在发布草稿", "发布器已初始化，开始发布...")

            # 确定标题（用户未填写则自动生成）
            title = self.title
            if not title:
                title = f"AI日报 - {self.target_date.strftime('%Y-%m-%d')}"

            logging.info(f"使用标题: {title}")

            # 执行发布（DailyPublisher.run 是同步方法）
            draft_media_id = publisher.run(
                html_path=self.html_file,
                title=title,
                digest=""
            )

            if self._is_cancelled:
                self.finished_signal.emit(False, "用户取消了操作", "")
                return

            self.progress.emit(100, "发布完成", f"草稿 media_id: {draft_media_id}")
            logging.info(f"草稿发布完成，media_id: {draft_media_id}")

            # 返回 media_id 作为输出（用特殊前缀标识）
            self.finished_signal.emit(
                True, "草稿发布完成", f"draft:{draft_media_id}")

        except CancelledError:
            # 工作流被用户取消
            logging.info("草稿发布已被用户取消")
            self.finished_signal.emit(False, "用户取消了操作", "")
        except Exception as e:
            raise Exception(f"发布草稿失败: {str(e)}") from e

    async def _run_full(self) -> None:
        """执行完整工作流（采集 + 生成 + 发布）

        根据 collect_mode 选择使用 API 模式或 RPA 模式采集器。
        """
        mode_text = "API" if self.collect_mode == "api" else "RPA"

        logging.info("=" * 50)
        logging.info("开始执行完整工作流")
        logging.info(f"采集模式: {mode_text}")
        logging.info(f"目标日期: {self.target_date.strftime('%Y-%m-%d')}")
        logging.info("=" * 50)

        # 阶段1：采集文章（根据模式选择采集器）
        self.progress.emit(0, f"阶段 1/3: 采集公众号文章 ({mode_text}模式)", "初始化采集器...")

        try:
            if self.collect_mode == "api":
                # API 模式：使用 APIArticleCollector（同步方法）
                collector = APIArticleCollector(config=self.config_path)
                # 设置取消检查回调
                collector.set_cancel_checker(lambda: self._is_cancelled)

                self.progress.emit(
                    5, f"阶段 1/3: 采集公众号文章 ({mode_text}模式)", "采集器已初始化，开始采集...")

                # 执行采集（同步调用）
                markdown_file = collector.run()
            else:
                # RPA 模式：使用 RPAArticleCollector（异步方法）
                collector = RPAArticleCollector(config=self.config_path)
                # 设置取消检查回调
                collector.set_cancel_checker(lambda: self._is_cancelled)

                self.progress.emit(
                    5, f"阶段 1/3: 采集公众号文章 ({mode_text}模式)", "采集器已初始化，开始采集...")

                # 执行采集（异步调用）
                markdown_file = await collector.run()

            if self._is_cancelled:
                self.finished_signal.emit(False, "用户取消了操作", "")
                return

            self.progress.emit(33, "阶段 1/3: 采集完成",
                               f"已采集到文章链接: {markdown_file}")
            logging.info(f"文章采集完成: {markdown_file}")

        except CancelledError:
            # 工作流被用户取消
            logging.info("完整工作流已被用户取消（采集阶段）")
            self.finished_signal.emit(False, "用户取消了操作", "")
            return
        except Exception as e:
            raise Exception(f"文章采集阶段失败: {str(e)}") from e

        # 阶段2：生成日报
        self.progress.emit(35, "阶段 2/3: 生成每日日报", "初始化生成器...")

        try:
            generator = DailyGenerator(config=self.config_path)
            # 设置取消检查回调
            generator.set_cancel_checker(lambda: self._is_cancelled)

            self.progress.emit(40, "阶段 2/3: 生成每日日报", "生成器已初始化，开始生成...")

            html_file = await generator.run(
                markdown_file=markdown_file,
                date=self.target_date
            )

            if self._is_cancelled:
                self.finished_signal.emit(False, "用户取消了操作", "")
                return

            self.progress.emit(66, "阶段 2/3: 生成完成", f"日报文件: {html_file}")
            logging.info(f"日报生成完成: {html_file}")

        except CancelledError:
            # 工作流被用户取消
            logging.info("完整工作流已被用户取消（生成阶段）")
            self.finished_signal.emit(False, "用户取消了操作", "")
            return
        except Exception as e:
            raise Exception(f"日报生成阶段失败: {str(e)}") from e

        # 阶段3：发布草稿
        self.progress.emit(70, "阶段 3/3: 发布到公众号草稿", "初始化发布器...")

        try:
            publisher = DailyPublisher(config=self.config_path)
            # 设置取消检查回调
            publisher.set_cancel_checker(lambda: self._is_cancelled)

            self.progress.emit(75, "阶段 3/3: 发布到公众号草稿", "发布器已初始化，开始发布...")

            # 确定标题（用户未填写则自动生成）
            title = self.title
            if not title:
                title = f"AI日报 - {self.target_date.strftime('%Y-%m-%d')}"

            logging.info(f"使用标题: {title}")

            # 执行发布（DailyPublisher.run 是同步方法）
            draft_media_id = publisher.run(
                html_path=html_file,
                title=title,
                digest=""
            )

            if self._is_cancelled:
                self.finished_signal.emit(False, "用户取消了操作", "")
                return

            self.progress.emit(100, "全部完成", f"草稿 media_id: {draft_media_id}")
            logging.info(f"草稿发布完成: {draft_media_id}")

            self.finished_signal.emit(
                True, "完整工作流执行完成", f"draft:{draft_media_id}")

        except CancelledError:
            # 工作流被用户取消
            logging.info("完整工作流已被用户取消（发布阶段）")
            self.finished_signal.emit(False, "用户取消了操作", "")
        except Exception as e:
            raise Exception(f"发布草稿阶段失败: {str(e)}") from e
