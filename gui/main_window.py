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
from typing import Optional, Dict
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
from .theme_manager import ThemeManager


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
        self.title = QLabel("输出结果")
        self.title.setStyleSheet(
            f"font-size: {Fonts.SIZE_TITLE}px; font-weight: bold;")
        layout.addWidget(self.title)

        # 状态卡片
        self.card = QFrame()
        # 样式将在 update_theme 中设置
        card_layout = QVBoxLayout(self.card)
        card_layout.setSpacing(Sizes.MARGIN_MEDIUM)
        card_layout.setContentsMargins(24, 24, 24, 24)

        self.status_icon = QLabel("📭")
        self.status_icon.setStyleSheet("font-size: 48px; background: transparent;")
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.status_icon)

        self.file_label = QLabel("尚未生成日报")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

    def update_theme(self, colors: Dict[str, str]):
        """更新主题样式"""
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border_light']};
                border-radius: {Sizes.RADIUS_LARGE}px;
            }}
        """)
        self.file_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SUBTITLE}px; color: {colors['text_secondary']}; background: transparent;")
        self.title.setStyleSheet(
            f"font-size: {Fonts.SIZE_TITLE}px; font-weight: bold; color: {colors['text_primary']};")

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
    APP_VERSION = "2.0.0"

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.theme_manager = ThemeManager(self)
        
        self._worker: Optional[WorkflowWorker] = None
        self._output_file: Optional[str] = None

        # 记录最近一次采集的 Markdown 文件路径
        self._last_collected_md: Optional[str] = None

        self._setup_ui()
        self._setup_logging()
        
        # 初始化主题
        self._update_theme(self.theme_manager.get_current_theme())
        self.theme_manager.theme_changed.connect(self._update_theme)

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

    def _create_legal_notice_card(self) -> QWidget:
        """创建法律声明警告卡片"""
        card = QFrame()
        card.setObjectName("LegalNoticeCard")
        card.setProperty("warning", True)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(2)
        card_layout.setContentsMargins(8, 6, 8, 6)
        
        # 顶部行：警告图标 + 标题 + 伸缩 + 详情按钮
        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        warning_icon = QLabel("⚠️")
        warning_icon.setStyleSheet("font-size: 12px; background: transparent; margin-top: 1px;")
        header_layout.addWidget(warning_icon)
        
        title = QLabel("仅供学习研究")
        title.setStyleSheet("font-weight: bold; font-size: 11px; background: transparent;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 查看详情按钮（移至右上角）
        view_detail_btn = QPushButton("详情 ›")
        view_detail_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_detail_btn.clicked.connect(self._show_legal_detail)
        # 样式将在 update_theme 中统一设置，这里只设置基础属性
        header_layout.addWidget(view_detail_btn)
        
        card_layout.addLayout(header_layout)
        
        # 提示文本（使用 HTML 控制行高，更紧凑）
        notice_text = QLabel()
        notice_text.setText(
            "<div style='line-height: 120%; font-size: 10px;'>"
            "• API 模式可能违反平台协议<br>"
            "• 请勿用于商业用途<br>"
            "• 使用风险由使用者承担"
            "</div>"
        )
        notice_text.setStyleSheet("background: transparent;")
        notice_text.setWordWrap(True)
        card_layout.addWidget(notice_text)
        
        return card
    
    def _show_legal_detail(self):
        """显示详细的法律声明"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("⚠️ 法律声明详情")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        
        msg_box.setText(
            "<h3>⚠️ 重要法律声明</h3>"
            "<p><b>本工具仅供个人学习和研究使用，请勿用于商业目的。</b></p>"
        )
        
        msg_box.setInformativeText(
            "<p><b>【风险提示】</b></p>"
            "<ul>"
            "<li><b>API 模式风险：</b>使用了微信公众平台的非公开后台接口，可能违反平台服务协议</li>"
            "<li><b>RPA 模式风险：</b>GUI 自动化操作可能违反微信用户协议，可能导致账号限制</li>"
            "<li><b>使用责任：</b>使用本工具产生的一切后果由使用者自行承担</li>"
            "<li><b>数据使用：</b>采集的数据仅限个人使用，不得转售或用于商业目的</li>"
            "</ul>"
            "<p><b>继续使用即表示您已阅读、理解并同意遵守上述条款。</b></p>"
            "<p>详细条款请查看项目根目录的 LICENSE 文件和 README.md。</p>"
        )
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # 设置对话框最小宽度，确保内容显示完整
        msg_box.setMinimumWidth(500)
        
        # 不设置 styleSheet，使用系统默认样式以适配黑白主题
        
        msg_box.exec()
        
        # 记录用户查看了详情
        logging.info("用户查看了法律声明详情")

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

        layout.addSpacing(8)
        
        # 法律声明警告卡片
        self.legal_notice_card = self._create_legal_notice_card()
        layout.addWidget(self.legal_notice_card)

        layout.addSpacing(8)

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
        self.sidebar_line = QFrame()
        self.sidebar_line.setFrameShape(QFrame.Shape.HLine)
        # 样式将在 update_theme 中设置
        layout.addWidget(self.sidebar_line)

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
        self.step_title = QLabel("分步执行")
        self.step_title.setProperty("class", "SidebarSectionTitle")
        self.step_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        action_layout.addWidget(self.step_title)

        # ====== Step 1: 采集 ======
        step1_layout = QHBoxLayout()
        self.step1_label = QLabel("① 公众号文章采集")
        self.step1_label.setProperty("class", "SidebarStepLabel")
        step1_layout.addWidget(self.step1_label)

        self.btn_collect = QPushButton("开始采集")
        self.btn_collect.setMinimumWidth(90)  # 增加宽度并使用 minimumWidth
        self.btn_collect.clicked.connect(self._on_collect_clicked)
        step1_layout.addWidget(self.btn_collect)
        action_layout.addLayout(step1_layout)

        # ====== Step 2: 生成 ======
        self.step2_label = QLabel("② 公众号内容生成")
        self.step2_label.setProperty("class", "SidebarStepLabel")
        action_layout.addWidget(self.step2_label)

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
        self.step3_label = QLabel("③ 草稿发布")
        self.step3_label.setProperty("class", "SidebarStepLabel")
        action_layout.addWidget(self.step3_label)

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

    def _update_theme(self, theme_name: str):
        """更新主题"""
        colors = self.theme_manager.get_colors()
        is_dark = self.theme_manager.is_dark()
        
        # 1. 更新全局样式表
        self.setStyleSheet(get_main_stylesheet(colors))
        
        # 2. 更新法律声明卡片样式
        warning_bg = "#fff3cd" if not is_dark else "#4a3800"
        warning_border = "#ffc107" if not is_dark else "#856404"
        warning_text = "#856404" if not is_dark else "#ffc107"
        
        self.legal_notice_card.setStyleSheet(f"""
            QFrame#LegalNoticeCard {{
                background-color: {warning_bg};
                border: 1px solid {warning_border};
                border-radius: 6px;
                padding: 0px;
            }}
            QFrame#LegalNoticeCard QLabel {{
                color: {warning_text};
            }}
            QFrame#LegalNoticeCard QPushButton {{
                color: {warning_text};
                border: none;
                background: transparent;
                font-size: 10px;
                text-align: right;
                padding: 0;
                margin: 0;
                opacity: 0.8;
            }}
            QFrame#LegalNoticeCard QPushButton:hover {{
                font-weight: bold;
                opacity: 1.0;
            }}
        """)
        
        # 3. 更新侧边栏局部样式
        self.sidebar_line.setStyleSheet(
            f"background-color: {colors['border_light']}; max-height: 1px; margin: 8px 16px;")
        
        step_label_style = f"color: {colors['text_secondary']}; font-size: {Fonts.SIZE_SIDEBAR_SECTION}px; font-weight: bold;"
        self.step_title.setStyleSheet(step_label_style)
        
        step_item_style = f"color: {colors['text_secondary']}; font-size: {Fonts.SIZE_SMALL}px;"
        self.step1_label.setStyleSheet(step_item_style)
        self.step2_label.setStyleSheet(step_item_style)
        self.step3_label.setStyleSheet(step_item_style)
        
        # 3. 更新子面板主题
        if hasattr(self.config_panel, 'update_theme'):
            self.config_panel.update_theme(colors)
            
        if hasattr(self.log_panel, 'update_theme'):
            self.log_panel.update_theme(colors, is_dark)
            
        if hasattr(self.output_panel, 'update_theme'):
            self.output_panel.update_theme(colors)
            
        if hasattr(self.progress_panel, 'update_theme'):
            self.progress_panel.update_theme(colors)

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
        self.progress_panel.set_status(status, "info")
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
