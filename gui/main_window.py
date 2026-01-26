# -*- coding: utf-8 -*-
"""
主窗口

微信 AI 日报助手的主窗口，整合所有面板组件。
"""

import os
import sys
import logging
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional
import glob

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QStackedWidget,
    QFileDialog, QApplication, QButtonGroup, QFrame,
    QSizePolicy, QComboBox, QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize
from PyQt6.QtGui import QIcon, QCloseEvent, QAction

from .panels import ConfigPanel, ProgressPanel, LogPanel
from .workers import WorkflowWorker
from .workers.workflow_worker import WorkflowType
from .utils import ConfigManager, LogManager
from .styles import get_main_stylesheet, Colors, Sizes, Fonts


class OutputPanel(QWidget):
    """输出结果面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._output_file = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(Sizes.MARGIN_LARGE)
        layout.setContentsMargins(
            Sizes.MARGIN_LARGE, Sizes.MARGIN_LARGE, Sizes.MARGIN_LARGE, Sizes.MARGIN_LARGE)

        # 标题
        title = QLabel("输出结果")
        title.setStyleSheet(
            f"font-size: {Fonts.SIZE_TITLE}px; font-weight: bold;")
        layout.addWidget(title)

        # 状态卡片
        self.card = QFrame()
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Sizes.RADIUS_LARGE}px;
            }}
        """)
        card_layout = QVBoxLayout(self.card)
        card_layout.setSpacing(Sizes.MARGIN_MEDIUM)
        card_layout.setContentsMargins(24, 24, 24, 24)

        self.status_icon = QLabel("📭")
        self.status_icon.setStyleSheet("font-size: 48px;")
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.status_icon)

        self.file_label = QLabel("尚未生成日报")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SUBTITLE}px; color: {Colors.TEXT_SECONDARY};")
        self.file_label.setWordWrap(True)
        card_layout.addWidget(self.file_label)

        # 按钮组
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_open_folder = QPushButton("打开文件夹")
        self.btn_open_folder.setEnabled(False)
        self.btn_open_folder.clicked.connect(self._open_folder)
        btn_layout.addWidget(self.btn_open_folder)

        self.btn_preview = QPushButton("浏览器预览")
        self.btn_preview.setEnabled(False)
        self.btn_preview.setProperty("primary", True)
        self.btn_preview.clicked.connect(self._preview)
        btn_layout.addWidget(self.btn_preview)

        self.btn_copy = QPushButton("复制内容")
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(self._copy)
        btn_layout.addWidget(self.btn_copy)

        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)

        layout.addWidget(self.card)
        layout.addStretch()

    def update_output(self, file_path: str):
        self._output_file = file_path
        if file_path:
            self.status_icon.setText("✅")
            self.file_label.setText(f"已生成: {Path(file_path).name}")
            self.btn_open_folder.setEnabled(True)

            is_html = file_path.endswith(".html")
            self.btn_preview.setEnabled(is_html)
            self.btn_copy.setEnabled(is_html)
        else:
            self.status_icon.setText("📭")
            self.file_label.setText("尚未生成日报")
            self.btn_open_folder.setEnabled(False)
            self.btn_preview.setEnabled(False)
            self.btn_copy.setEnabled(False)

    def _open_folder(self):
        if not self._output_file:
            return
        folder = Path(self._output_file).parent
        if sys.platform == "win32":
            os.startfile(str(folder))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(folder)])
        else:
            subprocess.run(["xdg-open", str(folder)])

    def _preview(self):
        if self._output_file:
            webbrowser.open(f"file://{Path(self._output_file).resolve()}")

    def _copy(self):
        if not self._output_file:
            return
        try:
            with open(self._output_file, "r", encoding="utf-8") as f:
                QApplication.clipboard().setText(f.read())
            QMessageBox.information(self, "成功", "内容已复制")
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))


class MainWindow(QMainWindow):
    """主窗口"""

    APP_NAME = "WeChat AI Daily"
    APP_VERSION = "1.1.0"

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self._worker: Optional[WorkflowWorker] = None
        self._output_file: Optional[str] = None

        # 记录最近一次采集的 Markdown 文件路径
        self._last_collected_md: Optional[str] = None

        self._setup_ui()
        self._setup_logging()
        self.setStyleSheet(get_main_stylesheet())

    def _setup_ui(self) -> None:
        self.setWindowTitle(f"{self.APP_NAME} v{self.APP_VERSION}")
        self.setMinimumSize(Sizes.WINDOW_MIN_WIDTH, Sizes.WINDOW_MIN_HEIGHT)
        self.resize(Sizes.WINDOW_DEFAULT_WIDTH, Sizes.WINDOW_DEFAULT_HEIGHT)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 使用 QSplitter 实现可拖拽的侧边栏
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)  # 禁止完全折叠

        # 1. 侧边栏
        sidebar = self._create_sidebar()
        self.splitter.addWidget(sidebar)

        # 2. 内容区
        content_area = QWidget()
        content_area.setObjectName("ContentArea")
        content_layout = QVBoxLayout(content_area)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 堆叠窗口 (Config, Logs, Output)
        self.stack = QStackedWidget()

        # 页面 0: 配置
        self.config_panel = ConfigPanel(self.config_manager)
        self.stack.addWidget(self.config_panel)

        # 页面 1: 日志
        self.log_panel = LogPanel()
        self.stack.addWidget(self.log_panel)

        # 页面 2: 输出
        self.output_panel = OutputPanel()
        self.stack.addWidget(self.output_panel)

        content_layout.addWidget(self.stack)

        # 底部进度条
        self.progress_panel = ProgressPanel()
        content_layout.addWidget(self.progress_panel)

        self.splitter.addWidget(content_area)

        # 设置默认宽度比例（侧边栏:内容区）
        self.splitter.setSizes(
            [Sizes.SIDEBAR_WIDTH, Sizes.WINDOW_DEFAULT_WIDTH - Sizes.SIDEBAR_WIDTH])

        main_layout.addWidget(self.splitter)

    def _create_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        # 设置可拖拽的宽度范围
        sidebar.setMinimumWidth(Sizes.SIDEBAR_MIN_WIDTH)
        sidebar.setMaximumWidth(Sizes.SIDEBAR_MAX_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setSpacing(Sizes.MARGIN_TINY)
        layout.setContentsMargins(0, 0, 0, Sizes.MARGIN_MEDIUM)

        # 标题
        title = QLabel(self.APP_NAME)
        title.setObjectName("AppTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(10)

        # 导航按钮组
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.nav_btns = []
        nav_items = [
            (0, "⚙️ 参数配置", True),
            (1, "📝 运行日志", False),
            (2, "📂 输出结果", False)
        ]

        for idx, text, checked in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(checked)
            btn.setProperty("class", "NavButton")
            btn.setProperty("nav", True)
            btn.clicked.connect(
                lambda checked, i=idx: self.stack.setCurrentIndex(i))
            self.nav_group.addButton(btn, idx)
            layout.addWidget(btn)
            self.nav_btns.append(btn)

        layout.addStretch()

        # ==================== 操作按钮区 ====================
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(
            f"background-color: {Colors.BORDER_LIGHT}; max-height: 1px; margin: 8px 16px;")
        layout.addWidget(line)

        # 容器
        action_container = QWidget()
        action_layout = QVBoxLayout(action_container)
        action_layout.setSpacing(12)  # 调整间距
        action_layout.setContentsMargins(
            Sizes.MARGIN_MEDIUM, Sizes.MARGIN_SMALL, Sizes.MARGIN_MEDIUM, Sizes.MARGIN_SMALL)

        # 一键全流程按钮
        self.btn_full = QPushButton("🚀 一键全流程")
        self.btn_full.setProperty("primary", True)
        self.btn_full.setMinimumHeight(40)
        self.btn_full.setToolTip("自动完成采集+生成+发布三个步骤")
        self.btn_full.clicked.connect(self._on_full_clicked)
        action_layout.addWidget(self.btn_full)

        # 分步执行标题
        step_title = QLabel("分步执行")
        step_title.setProperty("class", "SidebarSectionTitle")
        step_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        action_layout.addWidget(step_title)

        # ====== Step 1: 采集 ======
        step1_layout = QHBoxLayout()
        step1_label = QLabel("① 公众号文章采集")
        step1_label.setProperty("class", "SidebarStepLabel")
        step1_layout.addWidget(step1_label)

        self.btn_collect = QPushButton("开始采集")
        self.btn_collect.setMinimumWidth(90)  # 增加宽度并使用 minimumWidth
        self.btn_collect.clicked.connect(self._on_collect_clicked)
        step1_layout.addWidget(self.btn_collect)
        action_layout.addLayout(step1_layout)

        # ====== Step 2: 生成 ======
        step2_label = QLabel("② 公众号内容生成")
        step2_label.setProperty("class", "SidebarStepLabel")
        action_layout.addWidget(step2_label)

        step2_layout = QHBoxLayout()
        self.md_file_combo = QComboBox()
        self.md_file_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.md_file_combo.setToolTip("选择采集阶段生成的 Markdown 文件")
        step2_layout.addWidget(self.md_file_combo)

        self.btn_generate = QPushButton("生成")
        self.btn_generate.setMinimumWidth(70)
        self.btn_generate.clicked.connect(self._on_generate_clicked)
        step2_layout.addWidget(self.btn_generate)
        action_layout.addLayout(step2_layout)

        # ====== Step 3: 发布 ======
        step3_label = QLabel("③ 草稿发布")
        step3_label.setProperty("class", "SidebarStepLabel")
        action_layout.addWidget(step3_label)

        step3_layout = QHBoxLayout()
        self.html_file_combo = QComboBox()
        self.html_file_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.html_file_combo.setToolTip("选择生成阶段生成的 HTML 文件")
        step3_layout.addWidget(self.html_file_combo)

        self.btn_publish = QPushButton("发布")
        self.btn_publish.setMinimumWidth(70)
        self.btn_publish.clicked.connect(self._on_publish_clicked)
        step3_layout.addWidget(self.btn_publish)
        action_layout.addLayout(step3_layout)

        # 停止按钮（默认隐藏）
        self.btn_cancel = QPushButton("⏹ 停止任务")
        self.btn_cancel.setProperty("danger", True)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        action_layout.addWidget(self.btn_cancel)

        layout.addWidget(action_container)

        # 初始化加载可用的文件列表
        self._refresh_md_file_list()
        self._refresh_html_file_list()

        return sidebar

    def _refresh_md_file_list(self) -> None:
        """刷新可用的 Markdown 文件列表"""
        self.md_file_combo.clear()

        output_dir = self.config_manager.get_project_root() / "output"
        if not output_dir.exists():
            self.md_file_combo.addItem("(无可用文件)")
            self.btn_generate.setEnabled(False)
            return

        # 查找所有 articles_*.md 文件，按修改时间倒序
        md_files = list(output_dir.glob("articles_*.md"))
        md_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        if not md_files:
            self.md_file_combo.addItem("(无可用文件)")
            self.btn_generate.setEnabled(False)
            return

        for md_file in md_files:
            self.md_file_combo.addItem(md_file.name, str(md_file))

        self.btn_generate.setEnabled(True)

    def _refresh_html_file_list(self) -> None:
        """刷新可用的 HTML 文件列表"""
        self.html_file_combo.clear()

        output_dir = self.config_manager.get_project_root() / "output"
        if not output_dir.exists():
            self.html_file_combo.addItem("(无可用文件)")
            self.btn_publish.setEnabled(False)
            return

        # 查找所有 daily_rich_text_*.html 文件，按修改时间倒序
        html_files = list(output_dir.glob("daily_rich_text_*.html"))
        html_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        if not html_files:
            self.html_file_combo.addItem("(无可用文件)")
            self.btn_publish.setEnabled(False)
            return

        for html_file in html_files:
            self.html_file_combo.addItem(html_file.name, str(html_file))

        self.btn_publish.setEnabled(True)

    def _setup_logging(self) -> None:
        log_manager = LogManager()
        log_file = self.config_manager.get_project_root() / "logs" / "gui.log"
        qt_handler = log_manager.setup_logging(
            level=logging.INFO, log_file=str(log_file))
        qt_handler.log_signal.log_message.connect(self.log_panel.append_log)
        logging.info(f"{self.APP_NAME} v{self.APP_VERSION} 启动")

    # ==================== Actions ====================

    def _on_collect_clicked(self):
        if self._validate_and_save():
            self._start_workflow(WorkflowType.COLLECT)

    def _on_generate_clicked(self):
        # 从下拉框获取选中的文件路径
        file_path = self.md_file_combo.currentData()

        if not file_path or not Path(file_path).exists():
            QMessageBox.warning(self, "提示", "请先选择一个有效的文章链接文件（Markdown）")
            return

        if self._validate_and_save():
            self._start_workflow(WorkflowType.GENERATE,
                                 markdown_file=file_path)

    def _on_full_clicked(self):
        if self._validate_and_save():
            # 获取配置的默认标题
            title = self.config_manager.get_publish_title()
            self._start_workflow(WorkflowType.FULL, title=title)

    def _on_publish_clicked(self):
        """发布草稿按钮点击事件"""
        # 从下拉框获取选中的文件路径
        file_path = self.html_file_combo.currentData()

        if not file_path or not Path(file_path).exists():
            QMessageBox.warning(self, "提示", "请先选择一个有效的 HTML 日报文件")
            return

        # 检查微信凭证是否已配置
        if not self.config_manager.has_wechat_credentials():
            QMessageBox.warning(
                self, "配置缺失",
                "请先配置微信公众号 AppID 和 AppSecret\n\n"
                "可在「参数配置」→「发布配置」中设置，或配置环境变量"
            )
            self.stack.setCurrentIndex(0)  # 切到配置页
            return

        if self._validate_and_save():
            # 获取配置的默认标题
            title = self.config_manager.get_publish_title()
            self._start_workflow(WorkflowType.PUBLISH,
                                 html_file=file_path, title=title)

    def _on_cancel_clicked(self):
        if self._worker and self._worker.isRunning():
            if QMessageBox.question(self, "确认", "确定要停止当前任务吗？") == QMessageBox.StandardButton.Yes:
                self._worker.cancel()
                self.progress_panel.set_warning("正在停止...")

    def _validate_and_save(self) -> bool:
        valid, msg = self.config_panel.validate_config()
        if not valid:
            QMessageBox.warning(self, "配置错误", msg)
            self.stack.setCurrentIndex(0)  # 切回配置页
            return False
        if not self.config_panel.save_config():
            QMessageBox.warning(self, "错误", "保存配置失败")
            return False
        return True

    def _start_workflow(
        self,
        workflow_type: WorkflowType,
        markdown_file: str = None,
        html_file: str = None,
        title: str = None
    ):
        if self._worker and self._worker.isRunning():
            return

        self.stack.setCurrentIndex(1)  # 自动切到日志页

        target_date = self.config_panel.get_selected_date()
        collect_mode = self.config_panel.get_collect_mode()  # 获取采集模式

        self._worker = WorkflowWorker(
            config_path=str(self.config_manager.get_config_path()),
            workflow_type=workflow_type,
            target_date=target_date,
            collect_mode=collect_mode,  # 传递采集模式
            markdown_file=markdown_file,
            html_file=html_file,
            title=title,
            parent=self
        )

        self._worker.started_signal.connect(self._on_started)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.error.connect(self._on_error)

        self._worker.start()

    @pyqtSlot()
    def _on_started(self):
        self._update_buttons(False)
        self.progress_panel.reset()
        self.progress_panel.set_running()

    @pyqtSlot(int, str, str)
    def _on_progress(self, progress, status, detail):
        self.progress_panel.set_progress(progress)
        self.progress_panel.set_status(status, Colors.INFO)
        self.progress_panel.set_detail(detail)

    @pyqtSlot(bool, str, str)
    def _on_finished(self, success, message, output_file):
        self._update_buttons(True)
        if success:
            self.progress_panel.set_success(message)
            if output_file:
                # 判断输出类型
                if output_file.endswith(".md"):
                    # 采集阶段完成，刷新文件列表并自动选中
                    self._refresh_md_file_list()
                    for i in range(self.md_file_combo.count()):
                        if self.md_file_combo.itemData(i) == output_file:
                            self.md_file_combo.setCurrentIndex(i)
                            break

                    QMessageBox.information(
                        self, "采集完成",
                        f"{message}\n\n输出文件: {Path(output_file).name}\n\n可继续点击「生成日报」生成 HTML。"
                    )

                elif output_file.endswith(".html"):
                    # 生成阶段完成，更新输出面板并刷新 HTML 文件列表
                    self.output_panel.update_output(output_file)
                    self._refresh_html_file_list()
                    for i in range(self.html_file_combo.count()):
                        if self.html_file_combo.itemData(i) == output_file:
                            self.html_file_combo.setCurrentIndex(i)
                            break

                    QMessageBox.information(
                        self, "生成完成",
                        f"{message}\n\n输出文件: {Path(output_file).name}\n\n可继续点击「发布草稿」发布到公众号，或在「输出结果」页面查看详情。"
                    )

                elif output_file.startswith("draft:"):
                    # 发布阶段完成
                    draft_media_id = output_file[6:]  # 去掉 "draft:" 前缀
                    QMessageBox.information(
                        self, "发布完成",
                        f"{message}\n\n草稿 media_id:\n{draft_media_id}\n\n请前往微信公众号后台查看并发布草稿。"
                    )
                else:
                    self.output_panel.update_output(output_file)
                    QMessageBox.information(self, "完成", message)
        else:
            self.progress_panel.set_error(message)

    @pyqtSlot(str)
    def _on_error(self, msg):
        logging.error(msg)
        self.progress_panel.set_error("发生错误")
        QMessageBox.critical(self, "错误", msg)
        self._update_buttons(True)

    def _update_buttons(self, enabled: bool):
        self.btn_full.setVisible(enabled)
        self.btn_collect.setEnabled(enabled)
        self.btn_generate.setEnabled(
            enabled and self.md_file_combo.currentData() is not None)
        self.btn_publish.setEnabled(
            enabled and self.html_file_combo.currentData() is not None)
        self.btn_cancel.setVisible(not enabled)

    def closeEvent(self, event: QCloseEvent):
        if self._worker and self._worker.isRunning():
            if QMessageBox.question(self, "退出", "任务正在运行，确定要退出吗？") != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._worker.cancel()
            self._worker.wait(2000)
        event.accept()
