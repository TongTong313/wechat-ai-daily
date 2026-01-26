# -*- coding: utf-8 -*-
"""
配置面板

包含日期选择、采集模式切换、API/RPA 配置、模型配置、发布配置等功能。
支持根据采集模式动态显示/隐藏对应的配置区域。
"""

from datetime import datetime
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton,
    QListWidget, QComboBox, QCheckBox, QRadioButton,
    QDateEdit, QMessageBox, QInputDialog, QFrame,
    QSpinBox, QFileDialog, QButtonGroup, QSizePolicy,
    QScrollArea, QTextEdit
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction

from ..utils.config_manager import ConfigManager
from ..styles import Colors, Sizes, apply_shadow_effect, Fonts


class ConfigPanel(QWidget):
    """配置面板

    提供应用配置的 UI 界面，支持 API 和 RPA 两种采集模式的动态切换。
    """

    # 配置变化信号
    config_changed = pyqtSignal()

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._collect_mode = "api"  # 默认使用 API 模式
        self._setup_ui()
        self._load_config()
        self._connect_signals()
        # 初始化时根据默认模式更新界面显隐
        self._on_mode_changed()

    def _setup_ui(self) -> None:
        """设置 UI 布局"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(Sizes.MARGIN_LARGE)
        content_layout.setContentsMargins(
            Sizes.MARGIN_LARGE, Sizes.MARGIN_LARGE, Sizes.MARGIN_LARGE, Sizes.MARGIN_LARGE)

        # 1. 日期设置卡片
        date_card = self._create_date_card()
        apply_shadow_effect(date_card)
        content_layout.addWidget(date_card)

        # 2. 采集模式选择卡片（新增）
        mode_card = self._create_mode_card()
        apply_shadow_effect(mode_card)
        content_layout.addWidget(mode_card)

        # 3. API 模式配置卡片（新增）
        self.api_config_card = self._create_api_config_card()
        apply_shadow_effect(self.api_config_card)
        content_layout.addWidget(self.api_config_card)

        # 4. RPA 模式配置卡片（原 urls_card 改造）
        self.rpa_config_card = self._create_rpa_config_card()
        apply_shadow_effect(self.rpa_config_card)
        content_layout.addWidget(self.rpa_config_card)

        # 5. 文本模型配置卡片（通用，从原 model_config_card 拆分）
        llm_config_card = self._create_llm_config_card()
        apply_shadow_effect(llm_config_card)
        content_layout.addWidget(llm_config_card)

        # 6. 视觉模型配置卡片（RPA 模式专用）
        self.vlm_config_card = self._create_vlm_config_card()
        apply_shadow_effect(self.vlm_config_card)
        content_layout.addWidget(self.vlm_config_card)

        # 7. GUI 模板配置卡片（RPA 模式专用）
        self.template_card = self._create_template_card()
        apply_shadow_effect(self.template_card)
        content_layout.addWidget(self.template_card)

        # 8. 发布配置卡片（通用）
        publish_card = self._create_publish_card()
        apply_shadow_effect(publish_card)
        content_layout.addWidget(publish_card)

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _create_date_card(self) -> QGroupBox:
        """创建日期选择卡片"""
        group = QGroupBox("📅 采集日期")
        layout = QHBoxLayout()
        layout.setSpacing(Sizes.MARGIN_MEDIUM)

        # 日期选择器
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setFixedWidth(140)
        layout.addWidget(self.date_edit)

        # 快捷按钮
        self.btn_today = QPushButton("今天")
        self.btn_today.setFixedWidth(80)
        self.btn_today.clicked.connect(self._set_today)
        layout.addWidget(self.btn_today)

        self.btn_yesterday = QPushButton("昨天")
        self.btn_yesterday.setFixedWidth(80)
        self.btn_yesterday.clicked.connect(self._set_yesterday)
        layout.addWidget(self.btn_yesterday)

        layout.addStretch()

        # 提示
        hint = QLabel("选择要采集文章的发布日期")
        hint.setStyleSheet(f"color: {Colors.TEXT_HINT};")
        layout.addWidget(hint)

        group.setLayout(layout)
        return group

    def _create_mode_card(self) -> QGroupBox:
        """创建采集模式选择卡片"""
        group = QGroupBox("📡 采集模式")
        layout = QHBoxLayout()
        layout.setSpacing(Sizes.MARGIN_LARGE)
        layout.setContentsMargins(Sizes.MARGIN_MEDIUM, Sizes.MARGIN_LARGE, Sizes.MARGIN_MEDIUM, Sizes.MARGIN_MEDIUM)

        # 模式选择按钮组
        self.mode_group = QButtonGroup(self)

        # 定义通用样式
        option_style = f"""
            QFrame {{
                background-color: {Colors.BG_INPUT};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {Sizes.RADIUS_MEDIUM}px;
            }}
            QFrame:hover {{
                background-color: {Colors.BG_WINDOW};
                border-color: {Colors.PRIMARY};
            }}
            QRadioButton {{
                font-weight: bold;
                font-size: {Fonts.SIZE_BODY}px;
                background-color: transparent;
                border: none;
            }}
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Fonts.SIZE_SMALL}px;
                background-color: transparent;
                border: none;
            }}
        """

        # --- API 模式选项 ---
        api_container = QFrame()
        api_container.setStyleSheet(option_style)
        api_layout = QVBoxLayout(api_container)
        api_layout.setSpacing(6)
        api_layout.setContentsMargins(16, 16, 16, 16)

        self.radio_api_mode = QRadioButton("API 模式 (推荐)")
        self.radio_api_mode.setChecked(True)
        self.mode_group.addButton(self.radio_api_mode, 0)
        api_layout.addWidget(self.radio_api_mode)

        api_desc = QLabel("通过公众平台后台接口采集，速度快、稳定性高，支持按日期精确筛选。")
        api_desc.setWordWrap(True)
        api_layout.addWidget(api_desc)
        
        layout.addWidget(api_container, 1) # stretch factor 1

        # --- RPA 模式选项 ---
        rpa_container = QFrame()
        rpa_container.setStyleSheet(option_style)
        rpa_layout = QVBoxLayout(rpa_container)
        rpa_layout.setSpacing(6)
        rpa_layout.setContentsMargins(16, 16, 16, 16)

        self.radio_rpa_mode = QRadioButton("RPA 模式")
        self.mode_group.addButton(self.radio_rpa_mode, 1)
        rpa_layout.addWidget(self.radio_rpa_mode)

        rpa_desc = QLabel("通过模拟人工操作采集，无需后台 Token，但依赖本地微信客户端，速度较慢。")
        rpa_desc.setWordWrap(True)
        rpa_layout.addWidget(rpa_desc)

        layout.addWidget(rpa_container, 1) # stretch factor 1

        group.setLayout(layout)
        return group

    def _create_api_config_card(self) -> QGroupBox:
        """创建 API 模式配置卡片"""
        group = QGroupBox("🔗 公众号配置 (API 模式)")
        layout = QVBoxLayout()
        layout.setSpacing(Sizes.MARGIN_SMALL)

        # ==================== 公众号名称列表 ====================
        name_label = QLabel("公众号名称列表：")
        name_label.setStyleSheet(
            f"font-weight: bold; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(name_label)

        # 工具栏
        toolbar = QHBoxLayout()
        self.btn_add_account = QPushButton("＋ 添加")
        self.btn_add_account.setProperty("primary", True)
        self.btn_add_account.clicked.connect(self._add_account_name)
        toolbar.addWidget(self.btn_add_account)

        self.btn_remove_account = QPushButton("删除选中")
        self.btn_remove_account.clicked.connect(self._remove_selected_accounts)
        toolbar.addWidget(self.btn_remove_account)

        toolbar.addStretch()

        self.btn_reload_accounts = QPushButton("↻ 重置")
        self.btn_reload_accounts.setProperty("ghost", True)
        self.btn_reload_accounts.clicked.connect(self._reload_accounts)
        toolbar.addWidget(self.btn_reload_accounts)

        layout.addLayout(toolbar)

        # 列表
        self.account_list = QListWidget()
        self.account_list.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection)
        self.account_list.setMinimumHeight(80)
        self.account_list.setMaximumHeight(120)
        layout.addWidget(self.account_list)

        # ==================== Token ====================
        token_layout = QHBoxLayout()
        token_label = QLabel("Token:")
        token_label.setFixedWidth(60)
        token_layout.addWidget(token_label)

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("从公众平台后台获取")
        token_layout.addWidget(self.token_input)
        layout.addLayout(token_layout)

        # ==================== Cookie ====================
        cookie_label = QLabel("Cookie:")
        cookie_label.setStyleSheet(
            f"font-weight: bold; color: {Colors.TEXT_SECONDARY}; margin-top: 8px;")
        layout.addWidget(cookie_label)

        self.cookie_input = QTextEdit()
        self.cookie_input.setPlaceholderText("从公众平台后台获取（多行粘贴）")
        self.cookie_input.setMinimumHeight(60)
        self.cookie_input.setMaximumHeight(100)
        layout.addWidget(self.cookie_input)

        # 提示
        hint = QLabel(
            "⚠️ Cookie 和 Token 会过期，需定期从公众平台后台 (mp.weixin.qq.com) 获取更新")
        hint.setStyleSheet(
            f"color: {Colors.WARNING}; font-size: {Fonts.SIZE_SMALL}px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        group.setLayout(layout)
        return group

    def _create_rpa_config_card(self) -> QGroupBox:
        """创建 RPA 模式配置卡片"""
        group = QGroupBox("🔗 公众号配置 (RPA 模式)")
        layout = QVBoxLayout()
        layout.setSpacing(Sizes.MARGIN_SMALL)

        # 工具栏
        toolbar = QHBoxLayout()
        self.btn_add_url = QPushButton("＋ 添加链接")
        self.btn_add_url.setProperty("primary", True)
        self.btn_add_url.clicked.connect(self._add_url)
        toolbar.addWidget(self.btn_add_url)

        self.btn_remove_url = QPushButton("删除选中")
        self.btn_remove_url.clicked.connect(self._remove_selected_urls)
        toolbar.addWidget(self.btn_remove_url)

        toolbar.addStretch()

        self.btn_reload_urls = QPushButton("↻ 重置")
        self.btn_reload_urls.setProperty("ghost", True)
        self.btn_reload_urls.clicked.connect(self._reload_urls)
        toolbar.addWidget(self.btn_reload_urls)

        layout.addLayout(toolbar)

        # 列表
        self.url_list = QListWidget()
        self.url_list.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection)
        self.url_list.setMinimumHeight(120)
        self.url_list.setMaximumHeight(200)
        layout.addWidget(self.url_list)

        # 提示
        hint = QLabel("💡 每个公众号仅需提供一篇近期文章链接，系统将自动定位该公众号。")
        hint.setStyleSheet(
            f"color: {Colors.TEXT_HINT}; font-size: {Fonts.SIZE_SMALL}px;")
        layout.addWidget(hint)

        group.setLayout(layout)
        return group

    def _create_llm_config_card(self) -> QGroupBox:
        """创建文本模型配置卡片（通用）"""
        group = QGroupBox("🤖 文本模型配置")
        main_layout = QHBoxLayout()
        main_layout.setSpacing(Sizes.MARGIN_LARGE * 2)

        # ==================== 左侧：API Key ====================
        api_layout = QVBoxLayout()
        api_layout.setSpacing(Sizes.MARGIN_SMALL)

        api_title = QLabel("API Key 设置")
        api_title.setStyleSheet(
            f"font-weight: bold; color: {Colors.TEXT_SECONDARY};")
        api_layout.addWidget(api_title)

        # 输入框
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        api_layout.addWidget(self.api_key_input)

        # 显示切换
        hbox = QHBoxLayout()
        self.chk_show_key = QCheckBox("显示 Key")
        self.chk_show_key.stateChanged.connect(self._toggle_api_key_visibility)
        hbox.addWidget(self.chk_show_key)
        hbox.addStretch()
        api_layout.addLayout(hbox)

        # 来源选择
        self.api_key_source_group = QButtonGroup(self)

        self.radio_use_env = QRadioButton("使用环境变量 (推荐)")
        self.api_key_source_group.addButton(self.radio_use_env, 0)
        api_layout.addWidget(self.radio_use_env)

        self.radio_save_to_config = QRadioButton("保存到配置文件")
        self.api_key_source_group.addButton(self.radio_save_to_config, 1)
        api_layout.addWidget(self.radio_save_to_config)

        # 状态
        self.env_status_label = QLabel()
        self.env_status_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SMALL}px;")
        api_layout.addWidget(self.env_status_label)
        self._update_env_status()

        api_layout.addStretch()

        main_layout.addLayout(api_layout, 1)

        # ==================== 分割线 ====================
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setStyleSheet(
            f"background-color: {Colors.BORDER_LIGHT}; width: 1px;")
        main_layout.addWidget(line)

        # ==================== 右侧：LLM 参数 ====================
        model_layout = QGridLayout()
        model_layout.setVerticalSpacing(Sizes.MARGIN_SMALL)
        model_layout.setHorizontalSpacing(Sizes.MARGIN_MEDIUM)

        # 标题
        model_title = QLabel("LLM 参数设置")
        model_title.setStyleSheet(
            f"font-weight: bold; color: {Colors.TEXT_SECONDARY};")
        model_layout.addWidget(model_title, 0, 0, 1, 2)

        # LLM 模型
        model_layout.addWidget(QLabel("文本模型:"), 1, 0)
        self.llm_model_combo = QComboBox()
        self.llm_model_combo.addItems(
            ["qwen-plus", "qwen-turbo", "qwen-max", "qwen-long"])
        model_layout.addWidget(self.llm_model_combo, 1, 1)

        # Thinking
        model_layout.addWidget(QLabel("思考模式:"), 2, 0)
        self.chk_enable_thinking = QCheckBox("启用")
        model_layout.addWidget(self.chk_enable_thinking, 2, 1)

        model_layout.addWidget(QLabel("思考预算:"), 3, 0)
        self.thinking_budget_spin = QSpinBox()
        self.thinking_budget_spin.setRange(256, 8192)
        self.thinking_budget_spin.setSingleStep(256)
        self.thinking_budget_spin.setSuffix(" tokens")
        model_layout.addWidget(self.thinking_budget_spin, 3, 1)

        # 底部填充
        model_layout.setRowStretch(4, 1)

        main_layout.addLayout(model_layout, 1)

        group.setLayout(main_layout)
        return group

    def _create_vlm_config_card(self) -> QGroupBox:
        """创建视觉模型配置卡片（RPA 模式专用）"""
        group = QGroupBox("👁️ 视觉模型配置 (RPA 模式专用)")
        layout = QGridLayout()
        layout.setVerticalSpacing(Sizes.MARGIN_SMALL)
        layout.setHorizontalSpacing(Sizes.MARGIN_MEDIUM)

        # VLM 模型
        layout.addWidget(QLabel("视觉模型:"), 0, 0)
        self.vlm_model_combo = QComboBox()
        self.vlm_model_combo.addItems(
            ["qwen3-vl-plus", "qwen-vl-max", "qwen-vl-plus"])
        layout.addWidget(self.vlm_model_combo, 0, 1)

        # 提示
        hint = QLabel("💡 视觉模型用于识别公众号页面中的文章日期位置")
        hint.setStyleSheet(
            f"color: {Colors.TEXT_HINT}; font-size: {Fonts.SIZE_SMALL}px;")
        layout.addWidget(hint, 1, 0, 1, 2)

        group.setLayout(layout)
        return group

    def _create_template_card(self) -> QGroupBox:
        """创建 GUI 模板配置卡片（RPA 模式专用）"""
        group = QGroupBox("🖼️ GUI 模板配置 (RPA 模式专用)")
        layout = QGridLayout()
        layout.setVerticalSpacing(Sizes.MARGIN_SMALL)

        templates = [
            ("search_website", "访问网页按钮"),
            ("three_dots", "菜单按钮"),
            ("turnback", "返回按钮")
        ]

        self.template_inputs = {}

        for i, (key, label_text) in enumerate(templates):
            layout.addWidget(QLabel(label_text + ":"), i, 0)

            input_field = QLineEdit()
            input_field.setReadOnly(True)
            input_field.setPlaceholderText("默认路径")
            self.template_inputs[key] = input_field
            layout.addWidget(input_field, i, 1)

            btn = QPushButton("浏览")
            btn.setFixedWidth(60)
            btn.setProperty("ghost", True)
            btn.clicked.connect(
                lambda checked, k=key: self._browse_template(k))
            layout.addWidget(btn, i, 2)

        group.setLayout(layout)
        return group

    def _create_publish_card(self) -> QGroupBox:
        """创建发布配置卡片"""
        group = QGroupBox("📤 发布配置")
        layout = QGridLayout()
        layout.setVerticalSpacing(Sizes.MARGIN_SMALL)
        layout.setHorizontalSpacing(Sizes.MARGIN_MEDIUM)

        row = 0

        # AppID
        layout.addWidget(QLabel("AppID:"), row, 0)
        self.appid_input = QLineEdit()
        self.appid_input.setPlaceholderText("留空则从环境变量读取")
        layout.addWidget(self.appid_input, row, 1)
        self.appid_status_label = QLabel()
        self.appid_status_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SMALL}px;")
        layout.addWidget(self.appid_status_label, row, 2)
        row += 1

        # AppSecret
        layout.addWidget(QLabel("AppSecret:"), row, 0)
        secret_layout = QHBoxLayout()
        secret_layout.setSpacing(Sizes.MARGIN_SMALL)
        self.appsecret_input = QLineEdit()
        self.appsecret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.appsecret_input.setPlaceholderText("留空则从环境变量读取")
        secret_layout.addWidget(self.appsecret_input)
        self.chk_show_secret = QCheckBox("显示")
        self.chk_show_secret.stateChanged.connect(
            self._toggle_appsecret_visibility)
        secret_layout.addWidget(self.chk_show_secret)
        layout.addLayout(secret_layout, row, 1)
        self.appsecret_status_label = QLabel()
        self.appsecret_status_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SMALL}px;")
        layout.addWidget(self.appsecret_status_label, row, 2)
        row += 1

        # 作者名
        layout.addWidget(QLabel("作者名:"), row, 0)
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("公众号文章作者名")
        layout.addWidget(self.author_input, row, 1)
        row += 1

        # 封面图片
        layout.addWidget(QLabel("封面图片:"), row, 0)
        cover_layout = QHBoxLayout()
        cover_layout.setSpacing(Sizes.MARGIN_SMALL)
        self.cover_path_input = QLineEdit()
        self.cover_path_input.setPlaceholderText("默认封面路径")
        self.cover_path_input.setReadOnly(True)
        cover_layout.addWidget(self.cover_path_input)
        self.btn_browse_cover = QPushButton("浏览")
        self.btn_browse_cover.setFixedWidth(60)
        self.btn_browse_cover.setProperty("ghost", True)
        self.btn_browse_cover.clicked.connect(self._browse_cover_image)
        cover_layout.addWidget(self.btn_browse_cover)
        layout.addLayout(cover_layout, row, 1, 1, 2)
        row += 1

        # 默认标题
        layout.addWidget(QLabel("默认标题:"), row, 0)
        self.publish_title_input = QLineEdit()
        self.publish_title_input.setPlaceholderText("留空则自动生成")
        layout.addWidget(self.publish_title_input, row, 1, 1, 2)
        row += 1

        # 提示信息
        hint = QLabel("💡 凭证优先读取配置文件，为空时从环境变量读取")
        hint.setStyleSheet(
            f"color: {Colors.TEXT_HINT}; font-size: {Fonts.SIZE_SMALL}px;")
        layout.addWidget(hint, row, 0, 1, 3)

        group.setLayout(layout)
        return group

    # ==================== 模式切换逻辑 ====================

    def _on_mode_changed(self) -> None:
        """模式切换时更新界面显隐"""
        if self.radio_api_mode.isChecked():
            self._collect_mode = "api"
            # 显示 API 配置，隐藏 RPA 配置
            self.api_config_card.setVisible(True)
            self.rpa_config_card.setVisible(False)
            self.vlm_config_card.setVisible(False)
            self.template_card.setVisible(False)
        else:
            self._collect_mode = "rpa"
            # 显示 RPA 配置，隐藏 API 配置
            self.api_config_card.setVisible(False)
            self.rpa_config_card.setVisible(True)
            self.vlm_config_card.setVisible(True)
            self.template_card.setVisible(True)

        self._on_config_changed()

    def get_collect_mode(self) -> str:
        """获取当前选择的采集模式

        Returns:
            str: 'api' 或 'rpa'
        """
        return self._collect_mode

    # ==================== 状态更新方法 ====================

    def _update_env_status(self) -> None:
        """更新环境变量状态显示"""
        if self.config_manager.has_env_api_key():
            self.env_status_label.setText("✓ 已检测到环境变量")
            self.env_status_label.setStyleSheet(
                f"color: {Colors.SUCCESS}; font-size: {Fonts.SIZE_SMALL}px;")
        else:
            self.env_status_label.setText("✗ 未检测到环境变量")
            self.env_status_label.setStyleSheet(
                f"color: {Colors.WARNING}; font-size: {Fonts.SIZE_SMALL}px;")

    def _update_wechat_credentials_status(self) -> None:
        """更新微信凭证状态显示"""
        # 更新 AppID 状态
        _, appid_source = self.config_manager.get_wechat_appid()
        if appid_source == 'config':
            self.appid_status_label.setText("✓ 来自配置文件")
            self.appid_status_label.setStyleSheet(
                f"color: {Colors.SUCCESS}; font-size: {Fonts.SIZE_SMALL}px;")
        elif appid_source == 'env':
            self.appid_status_label.setText("✓ 来自环境变量")
            self.appid_status_label.setStyleSheet(
                f"color: {Colors.SUCCESS}; font-size: {Fonts.SIZE_SMALL}px;")
        else:
            self.appid_status_label.setText("⚠️ 未配置")
            self.appid_status_label.setStyleSheet(
                f"color: {Colors.WARNING}; font-size: {Fonts.SIZE_SMALL}px;")

        # 更新 AppSecret 状态
        _, appsecret_source = self.config_manager.get_wechat_appsecret()
        if appsecret_source == 'config':
            self.appsecret_status_label.setText("✓ 来自配置文件")
            self.appsecret_status_label.setStyleSheet(
                f"color: {Colors.SUCCESS}; font-size: {Fonts.SIZE_SMALL}px;")
        elif appsecret_source == 'env':
            self.appsecret_status_label.setText("✓ 来自环境变量")
            self.appsecret_status_label.setStyleSheet(
                f"color: {Colors.SUCCESS}; font-size: {Fonts.SIZE_SMALL}px;")
        else:
            self.appsecret_status_label.setText("⚠️ 未配置")
            self.appsecret_status_label.setStyleSheet(
                f"color: {Colors.WARNING}; font-size: {Fonts.SIZE_SMALL}px;")

    # ==================== 信号连接 ====================

    def _connect_signals(self) -> None:
        """连接所有信号"""
        # 模式切换
        self.mode_group.buttonClicked.connect(lambda: self._on_mode_changed())

        # 日期
        self.date_edit.dateChanged.connect(self._on_config_changed)

        # API 模式配置
        self.account_list.itemChanged.connect(self._on_config_changed)
        self.token_input.textChanged.connect(self._on_config_changed)
        self.cookie_input.textChanged.connect(self._on_config_changed)

        # RPA 模式配置
        self.url_list.itemChanged.connect(self._on_config_changed)

        # 模型配置
        self.api_key_input.textChanged.connect(self._on_config_changed)
        self.api_key_source_group.buttonClicked.connect(
            self._on_config_changed)
        self.llm_model_combo.currentTextChanged.connect(
            self._on_config_changed)
        self.vlm_model_combo.currentTextChanged.connect(
            self._on_config_changed)
        self.chk_enable_thinking.stateChanged.connect(
            self._on_thinking_state_changed)
        self.thinking_budget_spin.valueChanged.connect(self._on_config_changed)

        # 发布配置
        self.appid_input.textChanged.connect(self._on_config_changed)
        self.appsecret_input.textChanged.connect(self._on_config_changed)
        self.author_input.textChanged.connect(self._on_config_changed)
        self.publish_title_input.textChanged.connect(self._on_config_changed)

    def _on_thinking_state_changed(self, state: int) -> None:
        """思考模式状态变化"""
        enabled = state == Qt.CheckState.Checked.value
        self.thinking_budget_spin.setEnabled(enabled)
        self._on_config_changed()

    def _on_config_changed(self) -> None:
        """配置变化时发出信号"""
        self.config_changed.emit()

    # ==================== 配置加载与保存 ====================

    def _load_config(self) -> None:
        """从配置管理器加载配置"""
        # 日期
        target_date = self.config_manager.get_target_date()
        self._set_date_from_config(target_date)

        # API 模式配置
        account_names = self.config_manager.get_account_names()
        self.account_list.clear()
        for name in account_names:
            self.account_list.addItem(name)

        token = self.config_manager.get_api_token()
        if token:
            self.token_input.setText(token)

        cookie = self.config_manager.get_api_cookie()
        if cookie:
            self.cookie_input.setPlainText(cookie)

        # RPA 模式配置
        urls = self.config_manager.get_article_urls()
        self.url_list.clear()
        for url in urls:
            self.url_list.addItem(url)

        # API Key
        config_api_key = self.config_manager.get_config_api_key()
        if config_api_key:
            self.api_key_input.setText(config_api_key)
            self.radio_save_to_config.setChecked(True)
        else:
            env_api_key = self.config_manager.get_env_api_key()
            if env_api_key:
                self.api_key_input.setText(env_api_key)
            self.radio_use_env.setChecked(True)

        # 模型配置
        llm_model = self.config_manager.get_llm_model()
        if index := self.llm_model_combo.findText(llm_model):
            self.llm_model_combo.setCurrentIndex(index)

        vlm_model = self.config_manager.get_vlm_model()
        if index := self.vlm_model_combo.findText(vlm_model):
            self.vlm_model_combo.setCurrentIndex(index)

        enable_thinking = self.config_manager.get_enable_thinking()
        self.chk_enable_thinking.setChecked(enable_thinking)
        self.thinking_budget_spin.setEnabled(enable_thinking)
        self.thinking_budget_spin.setValue(
            self.config_manager.get_thinking_budget())

        # GUI 模板配置
        gui_config = self.config_manager.get_gui_config()
        for key, input_field in self.template_inputs.items():
            if key in gui_config:
                input_field.setText(gui_config[key])

        # 发布配置
        publish_config = self.config_manager.get_publish_config()
        if publish_config.get("appid"):
            self.appid_input.setText(publish_config.get("appid"))
        if publish_config.get("appsecret"):
            self.appsecret_input.setText(publish_config.get("appsecret"))
        if publish_config.get("author"):
            self.author_input.setText(publish_config.get("author"))
        if publish_config.get("cover_path"):
            self.cover_path_input.setText(publish_config.get("cover_path"))
        self.publish_title_input.setText(
            self.config_manager.get_publish_title())

        # 更新状态显示
        self._update_wechat_credentials_status()

    def _set_date_from_config(self, target_date: Optional[str]) -> None:
        """从配置设置日期"""
        if target_date is None or target_date == "today":
            self.date_edit.setDate(QDate.currentDate())
        elif target_date == "yesterday":
            self.date_edit.setDate(QDate.currentDate().addDays(-1))
        else:
            try:
                parsed_date = datetime.strptime(target_date, "%Y-%m-%d")
                self.date_edit.setDate(
                    QDate(parsed_date.year, parsed_date.month, parsed_date.day))
            except ValueError:
                self.date_edit.setDate(QDate.currentDate())

    def save_config(self) -> bool:
        """保存配置到配置管理器"""
        # 日期
        selected_date = self.get_selected_date()
        date_str = selected_date.strftime("%Y-%m-%d")
        self.config_manager.set_target_date(date_str)

        # API 模式配置
        account_names = []
        for i in range(self.account_list.count()):
            name = self.account_list.item(i).text().strip()
            if name:
                account_names.append(name)
        self.config_manager.set_account_names(account_names)

        token = self.token_input.text().strip()
        if token:
            self.config_manager.set_api_token(token)

        cookie = self.cookie_input.toPlainText().strip()
        if cookie:
            self.config_manager.set_api_cookie(cookie)

        # RPA 模式配置
        urls = []
        for i in range(self.url_list.count()):
            url = self.url_list.item(i).text().strip()
            if url:
                urls.append(url)
        self.config_manager.set_article_urls(urls)

        # API Key
        api_key = self.api_key_input.text().strip()
        if api_key:
            save_to_env = self.radio_use_env.isChecked()
            self.config_manager.set_api_key(api_key, save_to_env=save_to_env)

        # 模型配置
        self.config_manager.set_llm_model(self.llm_model_combo.currentText())
        self.config_manager.set_vlm_model(self.vlm_model_combo.currentText())
        self.config_manager.set_enable_thinking(
            self.chk_enable_thinking.isChecked())
        self.config_manager.set_thinking_budget(
            self.thinking_budget_spin.value())

        # GUI 模板配置
        for key, input_field in self.template_inputs.items():
            path = input_field.text().strip()
            if path:
                self.config_manager.set_gui_template_path(key, path)

        # 发布配置
        appid = self.appid_input.text().strip()
        if appid:
            self.config_manager.set_wechat_appid(appid, save_to_config=True)
        appsecret = self.appsecret_input.text().strip()
        if appsecret:
            self.config_manager.set_wechat_appsecret(
                appsecret, save_to_config=True)
        author = self.author_input.text().strip()
        if author:
            self.config_manager.set_publish_author(author)
        cover_path = self.cover_path_input.text().strip()
        if cover_path:
            self.config_manager.set_publish_cover_path(cover_path)
        publish_title = self.publish_title_input.text().strip()
        if publish_title:
            self.config_manager.set_publish_title(publish_title)

        return self.config_manager.save_config()

    def get_selected_date(self) -> datetime:
        """获取选择的日期"""
        qdate = self.date_edit.date()
        return datetime(qdate.year(), qdate.month(), qdate.day())

    def validate_config(self) -> tuple[bool, str]:
        """验证配置（根据模式验证不同字段）"""
        if self._collect_mode == "api":
            # API 模式验证
            if self.account_list.count() == 0:
                return False, "请至少添加一个公众号名称"
            if not self.token_input.text().strip():
                return False, "请填写 Token"
            if not self.cookie_input.toPlainText().strip():
                return False, "请填写 Cookie"
        else:
            # RPA 模式验证
            if self.url_list.count() == 0:
                return False, "请至少添加一个文章链接"

        # 通用验证：API Key
        api_key = self.api_key_input.text().strip()
        env_api_key = self.config_manager.get_env_api_key()
        if not api_key and not env_api_key:
            return False, "请设置 API Key"

        return True, ""

    # ==================== UI 操作方法 ====================

    def _set_today(self) -> None:
        """设置为今天"""
        self.date_edit.setDate(QDate.currentDate())

    def _set_yesterday(self) -> None:
        """设置为昨天"""
        self.date_edit.setDate(QDate.currentDate().addDays(-1))

    # API 模式操作
    def _add_account_name(self) -> None:
        """添加公众号名称"""
        name, ok = QInputDialog.getText(self, "添加公众号", "请输入公众号名称:")
        if ok and name.strip():
            name = name.strip()
            # 查重
            for i in range(self.account_list.count()):
                if self.account_list.item(i).text() == name:
                    QMessageBox.warning(self, "重复", "该公众号名称已存在")
                    return
            self.account_list.addItem(name)
            self._on_config_changed()

    def _remove_selected_accounts(self) -> None:
        """删除选中的公众号名称"""
        for item in self.account_list.selectedItems():
            self.account_list.takeItem(self.account_list.row(item))
        self._on_config_changed()

    def _reload_accounts(self) -> None:
        """重新加载公众号名称列表"""
        self.config_manager.load_config()
        account_names = self.config_manager.get_account_names()
        self.account_list.clear()
        for name in account_names:
            self.account_list.addItem(name)

    # RPA 模式操作
    def _add_url(self) -> None:
        """添加文章链接"""
        url, ok = QInputDialog.getText(self, "添加链接", "请输入微信公众号文章链接:")
        if ok and url.strip():
            url = url.strip()
            if "mp.weixin.qq.com" not in url:
                QMessageBox.warning(self, "无效链接", "请输入有效的微信公众号文章链接")
                return
            # 查重
            for i in range(self.url_list.count()):
                if self.url_list.item(i).text() == url:
                    return
            self.url_list.addItem(url)
            self._on_config_changed()

    def _remove_selected_urls(self) -> None:
        """删除选中的链接"""
        for item in self.url_list.selectedItems():
            self.url_list.takeItem(self.url_list.row(item))
        self._on_config_changed()

    def _reload_urls(self) -> None:
        """重新加载链接列表"""
        self.config_manager.load_config()
        urls = self.config_manager.get_article_urls()
        self.url_list.clear()
        for url in urls:
            self.url_list.addItem(url)

    # 通用操作
    def _toggle_api_key_visibility(self, state: int) -> None:
        """切换 API Key 显示/隐藏"""
        if state == Qt.CheckState.Checked.value:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _toggle_appsecret_visibility(self, state: int) -> None:
        """切换 AppSecret 显示/隐藏"""
        if state == Qt.CheckState.Checked.value:
            self.appsecret_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.appsecret_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _browse_cover_image(self) -> None:
        """浏览选择封面图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择封面图片",
            str(self.config_manager.get_project_root() / "templates"),
            "图片 (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.cover_path_input.setText(file_path)
            self._on_config_changed()

    def _browse_template(self, key: str) -> None:
        """浏览选择模板图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"选择模板 - {key}",
            str(self.config_manager.get_project_root() / "templates"),
            "图片 (*.png *.jpg)"
        )
        if file_path:
            self.template_inputs[key].setText(file_path)
            self._on_config_changed()
