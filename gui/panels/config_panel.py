# -*- coding: utf-8 -*-
"""
配置面板

包含日期选择、采集模式切换、API/RPA 配置、模型配置、发布配置等功能。
支持根据采集模式动态显示/隐藏对应的配置区域。
"""

from datetime import datetime, date
from typing import Optional, Dict
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
        self._current_colors = {} # 存储当前主题颜色
        
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
        self.date_card = self._create_date_card()
        apply_shadow_effect(self.date_card)
        content_layout.addWidget(self.date_card)

        # 2. 敏感数据保存方式卡片（新增）
        self.sensitive_data_mode_card = self._create_sensitive_data_mode_card()
        apply_shadow_effect(self.sensitive_data_mode_card)
        content_layout.addWidget(self.sensitive_data_mode_card)

        # 3. 采集模式选择卡片
        self.mode_card = self._create_mode_card()
        apply_shadow_effect(self.mode_card)
        content_layout.addWidget(self.mode_card)

        # 4. API 模式配置卡片
        self.api_config_card = self._create_api_config_card()
        apply_shadow_effect(self.api_config_card)
        content_layout.addWidget(self.api_config_card)

        # 5. RPA 模式配置卡片（原 urls_card 改造）
        self.rpa_config_card = self._create_rpa_config_card()
        apply_shadow_effect(self.rpa_config_card)
        content_layout.addWidget(self.rpa_config_card)

        # 6. 文本模型配置卡片（通用，从原 model_config_card 拆分）
        self.llm_config_card = self._create_llm_config_card()
        apply_shadow_effect(self.llm_config_card)
        content_layout.addWidget(self.llm_config_card)

        # 7. 视觉模型配置卡片（RPA 模式专用）
        self.vlm_config_card = self._create_vlm_config_card()
        apply_shadow_effect(self.vlm_config_card)
        content_layout.addWidget(self.vlm_config_card)

        # 8. GUI 模板配置卡片（RPA 模式专用）
        self.template_card = self._create_template_card()
        apply_shadow_effect(self.template_card)
        content_layout.addWidget(self.template_card)

        # 9. 发布配置卡片（通用）
        self.publish_card = self._create_publish_card()
        apply_shadow_effect(self.publish_card)
        content_layout.addWidget(self.publish_card)

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def update_theme(self, colors: Dict[str, str]):
        """更新主题样式"""
        self._current_colors = colors
        
        # 更新敏感数据保存方式卡片的样式
        sensitive_mode_style = f"""
            QFrame {{
                background-color: {colors['input_bg']};
                border: 1px solid {colors['border_light']};
                border-radius: {Sizes.RADIUS_MEDIUM}px;
            }}
            QFrame:hover {{
                background-color: {colors['input_bg_hover']};
                border-color: {colors['primary']};
            }}
            QRadioButton {{
                font-weight: bold;
                font-size: {Fonts.SIZE_BODY}px;
                background-color: transparent;
                border: none;
                color: {colors['text_primary']};
            }}
            QLabel {{
                color: {colors['text_secondary']};
                font-size: {Fonts.SIZE_SMALL}px;
                background-color: transparent;
                border: none;
            }}
        """
        self.env_mode_container.setStyleSheet(sensitive_mode_style)
        self.config_mode_container.setStyleSheet(sensitive_mode_style)
        
        # 更新模式选择卡片的样式
        option_style = f"""
            QFrame {{
                background-color: {colors['input_bg']};
                border: 1px solid {colors['border_light']};
                border-radius: {Sizes.RADIUS_MEDIUM}px;
            }}
            QFrame:hover {{
                background-color: {colors['input_bg_hover']};
                border-color: {colors['primary']};
            }}
            QRadioButton {{
                font-weight: bold;
                font-size: {Fonts.SIZE_BODY}px;
                background-color: transparent;
                border: none;
                color: {colors['text_primary']};
            }}
            QLabel {{
                color: {colors['text_secondary']};
                font-size: {Fonts.SIZE_SMALL}px;
                background-color: transparent;
                border: none;
            }}
        """
        self.api_container.setStyleSheet(option_style)
        self.rpa_container.setStyleSheet(option_style)
        
        # 更新其他可能需要手动更新颜色的控件
        # 例如提示文字颜色
        hint_style = f"color: {colors['text_hint']}; font-size: {Fonts.SIZE_SMALL}px;"
        self.date_hint.setStyleSheet(hint_style)
        self.priority_hint.setStyleSheet(hint_style)
        self.token_hint.setStyleSheet(f"color: {colors['warning']}; font-size: {Fonts.SIZE_SMALL}px;")
        self.url_hint.setStyleSheet(hint_style)
        self.vlm_hint.setStyleSheet(hint_style)
        self.publish_hint.setStyleSheet(hint_style)
        
        label_bold_style = f"font-weight: bold; color: {colors['text_secondary']};"
        self.name_label.setStyleSheet(label_bold_style)
        self.cookie_label.setStyleSheet(f"{label_bold_style} margin-top: 8px;")
        self.api_title.setStyleSheet(label_bold_style)
        self.model_title.setStyleSheet(label_bold_style)
        
        # 刷新状态颜色
        self._update_env_status()
        self._update_wechat_credentials_status()
        self._update_api_credentials_status()

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
        self.date_hint = QLabel("选择要采集文章的发布日期")
        # 样式将在 update_theme 中设置
        layout.addWidget(self.date_hint)

        group.setLayout(layout)
        return group

    def _create_sensitive_data_mode_card(self) -> QGroupBox:
        """创建敏感数据保存方式卡片"""
        group = QGroupBox("🔒 敏感数据保存方式")
        layout = QVBoxLayout()
        layout.setSpacing(Sizes.MARGIN_MEDIUM)

        # 说明文字
        desc_label = QLabel(
            "选择敏感数据（API Key、Token、Cookie、AppID、AppSecret）的保存方式："
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # 选项容器
        options_layout = QHBoxLayout()
        options_layout.setSpacing(Sizes.MARGIN_LARGE)

        # 模式选择按钮组
        self.sensitive_data_mode_group = QButtonGroup(self)

        # --- 环境变量模式选项 ---
        self.env_mode_container = QFrame()
        env_mode_layout = QVBoxLayout(self.env_mode_container)
        env_mode_layout.setSpacing(6)
        env_mode_layout.setContentsMargins(16, 16, 16, 16)

        self.radio_save_to_env = QRadioButton("保存到 .env 文件 (推荐)")
        self.radio_save_to_env.setChecked(True)  # 默认选中
        self.sensitive_data_mode_group.addButton(self.radio_save_to_env, 0)
        env_mode_layout.addWidget(self.radio_save_to_env)

        env_mode_desc = QLabel(
            "💾 保存行为：点击保存后会执行以下操作\n"
            "   1️⃣ 将下方输入框填写的敏感信息写入 .env 文件\n"
            "   2️⃣ 清空 config.yaml 中对应的敏感数据（设为 null）\n"
            "✅ 优点：更安全，不会提交到版本控制\n"
            "📋 适用于：个人使用，本地开发"
        )
        env_mode_desc.setWordWrap(True)
        env_mode_layout.addWidget(env_mode_desc)

        options_layout.addWidget(self.env_mode_container, 1)

        # --- 配置文件模式选项 ---
        self.config_mode_container = QFrame()
        config_mode_layout = QVBoxLayout(self.config_mode_container)
        config_mode_layout.setSpacing(6)
        config_mode_layout.setContentsMargins(16, 16, 16, 16)

        self.radio_save_to_config = QRadioButton("保存到 config.yaml")
        self.sensitive_data_mode_group.addButton(self.radio_save_to_config, 1)
        config_mode_layout.addWidget(self.radio_save_to_config)

        config_mode_desc = QLabel(
            "💾 保存行为：点击保存后会执行以下操作\n"
            "   1️⃣ 将下方输入框填写的敏感信息写入 config.yaml 文件\n"
            "   2️⃣ 不会修改 .env 文件（如果存在）\n"
            "📁 优点：方便管理，一个文件包含所有配置\n"
            "⚠️ 注意：请勿将配置文件提交到公开仓库"
        )
        config_mode_desc.setWordWrap(True)
        config_mode_layout.addWidget(config_mode_desc)

        options_layout.addWidget(self.config_mode_container, 1)

        layout.addLayout(options_layout)

        # 优先级说明
        priority_hint = QLabel(
            "💡 配置优先级（从高到低）：config.yaml > .env 文件 > 系统环境变量"
        )
        priority_hint.setWordWrap(True)
        # 样式将在 update_theme 中设置
        layout.addWidget(priority_hint)
        self.priority_hint = priority_hint

        # 打开 .env 文件按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_open_env_file = QPushButton("📝 打开 .env 文件")
        self.btn_open_env_file.setProperty("ghost", True)
        self.btn_open_env_file.clicked.connect(self._open_env_file)
        self.btn_open_env_file.setToolTip("在系统默认编辑器中打开 .env 文件")
        btn_layout.addWidget(self.btn_open_env_file)
        
        layout.addLayout(btn_layout)

        group.setLayout(layout)
        return group

    def _create_mode_card(self) -> QGroupBox:
        """创建采集模式选择卡片"""
        group = QGroupBox("📡 采集模式")
        layout = QHBoxLayout()
        layout.setSpacing(Sizes.MARGIN_LARGE)
        layout.setContentsMargins(
            Sizes.MARGIN_MEDIUM, Sizes.MARGIN_LARGE, Sizes.MARGIN_MEDIUM, Sizes.MARGIN_MEDIUM)

        # 模式选择按钮组
        self.mode_group = QButtonGroup(self)

        # --- API 模式选项 ---
        self.api_container = QFrame()
        # 样式将在 update_theme 中设置
        api_layout = QVBoxLayout(self.api_container)
        api_layout.setSpacing(6)
        api_layout.setContentsMargins(16, 16, 16, 16)

        self.radio_api_mode = QRadioButton("API 模式 (推荐)")
        self.radio_api_mode.setChecked(True)
        self.mode_group.addButton(self.radio_api_mode, 0)
        api_layout.addWidget(self.radio_api_mode)

        api_desc = QLabel(
            "优点：速度快、稳定性高，无需微信客户端，文章采集更全面，支持按日期精确筛选\n"
            "缺点：需要公众号账号，Cookie/Token 会过期需定期更新"
        )
        api_desc.setWordWrap(True)
        api_layout.addWidget(api_desc)

        layout.addWidget(self.api_container, 1)  # stretch factor 1

        # --- RPA 模式选项 ---
        self.rpa_container = QFrame()
        # 样式将在 update_theme 中设置
        rpa_layout = QVBoxLayout(self.rpa_container)
        rpa_layout.setSpacing(6)
        rpa_layout.setContentsMargins(16, 16, 16, 16)

        self.radio_rpa_mode = QRadioButton("RPA 模式")
        self.mode_group.addButton(self.radio_rpa_mode, 1)
        rpa_layout.addWidget(self.radio_rpa_mode)

        rpa_desc = QLabel(
            "优点：无需公众号账号，无需配置 Cookie/Token\n"
            "缺点：需要微信客户端运行，速度较慢，文章可能不全，采集时不能操作电脑"
        )
        rpa_desc.setWordWrap(True)
        rpa_layout.addWidget(rpa_desc)

        layout.addWidget(self.rpa_container, 1)  # stretch factor 1

        group.setLayout(layout)
        return group

    def _create_api_config_card(self) -> QGroupBox:
        """创建 API 模式配置卡片"""
        group = QGroupBox("🔗 公众号配置 (API 模式)")
        layout = QVBoxLayout()
        layout.setSpacing(Sizes.MARGIN_SMALL)

        # ==================== 公众号名称列表 ====================
        self.name_label = QLabel("公众号名称列表：")
        # 样式将在 update_theme 中设置
        layout.addWidget(self.name_label)

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

        # Token 状态标签
        self.token_status_label = QLabel()
        self.token_status_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SMALL}px;")
        self.token_status_label.setFixedWidth(100)
        token_layout.addWidget(self.token_status_label)

        layout.addLayout(token_layout)

        # ==================== Cookie ====================
        cookie_header_layout = QHBoxLayout()
        self.cookie_label = QLabel("Cookie:")
        # 样式将在 update_theme 中设置
        cookie_header_layout.addWidget(self.cookie_label)

        cookie_header_layout.addStretch()

        # Cookie 状态标签
        self.cookie_status_label = QLabel()
        self.cookie_status_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SMALL}px;")
        cookie_header_layout.addWidget(self.cookie_status_label)

        layout.addLayout(cookie_header_layout)

        self.cookie_input = QTextEdit()
        self.cookie_input.setPlaceholderText("从公众平台后台获取（多行粘贴）")
        self.cookie_input.setMinimumHeight(60)
        self.cookie_input.setMaximumHeight(100)
        layout.addWidget(self.cookie_input)

        # 提示
        self.token_hint = QLabel(
            "⚠️ Cookie 和 Token 会过期，需定期从公众平台后台 (mp.weixin.qq.com) 获取更新\n"
            "💡 配置优先级：界面输入 > config.yaml > 环境变量 (WECHAT_API_TOKEN/WECHAT_API_COOKIE)")
        self.token_hint.setWordWrap(True)
        # 样式将在 update_theme 中设置
        layout.addWidget(self.token_hint)

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
        self.url_hint = QLabel("💡 每个公众号仅需提供一篇近期文章链接，系统将自动定位该公众号。")
        # 样式将在 update_theme 中设置
        layout.addWidget(self.url_hint)

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

        self.api_title = QLabel("API Key 设置")
        # 样式将在 update_theme 中设置
        api_layout.addWidget(self.api_title)

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

        # 来源状态显示（只读，由全局敏感数据保存方式统一控制）
        self.env_status_label = QLabel()
        self.env_status_label.setStyleSheet(
            f"font-size: {Fonts.SIZE_SMALL}px;")
        api_layout.addWidget(self.env_status_label)
        self._update_env_status()

        # 提示信息
        hint = QLabel("💡 保存方式由上方「敏感数据保存方式」统一控制")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: gray; font-size: {Fonts.SIZE_SMALL}px;")
        api_layout.addWidget(hint)

        api_layout.addStretch()

        main_layout.addLayout(api_layout, 1)

        # ==================== 分割线 ====================
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        # 样式由全局控制
        main_layout.addWidget(line)

        # ==================== 右侧：LLM 参数 ====================
        model_layout = QGridLayout()
        model_layout.setVerticalSpacing(Sizes.MARGIN_SMALL)
        model_layout.setHorizontalSpacing(Sizes.MARGIN_MEDIUM)

        # 标题
        self.model_title = QLabel("LLM 参数设置")
        # 样式将在 update_theme 中设置
        model_layout.addWidget(self.model_title, 0, 0, 1, 2)

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
        self.vlm_hint = QLabel("💡 视觉模型用于识别公众号页面中的文章日期位置")
        # 样式将在 update_theme 中设置
        layout.addWidget(self.vlm_hint, 1, 0, 1, 2)

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
        self.publish_hint = QLabel("💡 凭证优先读取配置文件，为空时从环境变量读取")
        # 样式将在 update_theme 中设置
        layout.addWidget(self.publish_hint, row, 0, 1, 3)

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
        """更新 API Key 状态显示"""
        colors = self._current_colors
        if not colors: # 尚未初始化
            return

        # 使用 get_api_key_with_source() 检测所有来源
        _, api_key_source = self.config_manager.get_api_key_with_source()

        if api_key_source == 'config':
            self.env_status_label.setText("✓ 来自 config.yaml")
            self.env_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        elif api_key_source == 'env_file':
            self.env_status_label.setText("✓ 来自 .env 文件")
            self.env_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        elif api_key_source == 'system':
            self.env_status_label.setText("✓ 来自系统环境变量")
            self.env_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        else:
            self.env_status_label.setText("⚠️ 未配置")
            self.env_status_label.setStyleSheet(
                f"color: {colors['warning']}; font-size: {Fonts.SIZE_SMALL}px;")

    def _update_wechat_credentials_status(self) -> None:
        """更新微信凭证状态显示"""
        colors = self._current_colors
        if not colors: # 尚未初始化
            return
            
        # 更新 AppID 状态
        _, appid_source = self.config_manager.get_wechat_appid()
        if appid_source == 'config':
            self.appid_status_label.setText("✓ 来自 config.yaml")
            self.appid_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        elif appid_source == 'env_file':
            self.appid_status_label.setText("✓ 来自 .env 文件")
            self.appid_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        elif appid_source == 'system':
            self.appid_status_label.setText("✓ 来自系统环境变量")
            self.appid_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        else:
            self.appid_status_label.setText("⚠️ 未配置")
            self.appid_status_label.setStyleSheet(
                f"color: {colors['warning']}; font-size: {Fonts.SIZE_SMALL}px;")

        # 更新 AppSecret 状态
        _, appsecret_source = self.config_manager.get_wechat_appsecret()
        if appsecret_source == 'config':
            self.appsecret_status_label.setText("✓ 来自 config.yaml")
            self.appsecret_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        elif appsecret_source == 'env_file':
            self.appsecret_status_label.setText("✓ 来自 .env 文件")
            self.appsecret_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        elif appsecret_source == 'system':
            self.appsecret_status_label.setText("✓ 来自系统环境变量")
            self.appsecret_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        else:
            self.appsecret_status_label.setText("⚠️ 未配置")
            self.appsecret_status_label.setStyleSheet(
                f"color: {colors['warning']}; font-size: {Fonts.SIZE_SMALL}px;")

    def _update_api_credentials_status(self) -> None:
        """更新 API 模式凭证状态显示（Token/Cookie）"""
        colors = self._current_colors
        if not colors:  # 尚未初始化
            return

        # 更新 Token 状态
        _, token_source = self.config_manager.get_api_token_with_source()
        if token_source == 'config':
            self.token_status_label.setText("✓ 来自 config.yaml")
            self.token_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        elif token_source == 'env_file':
            self.token_status_label.setText("✓ 来自 .env 文件")
            self.token_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        elif token_source == 'system':
            self.token_status_label.setText("✓ 来自系统环境变量")
            self.token_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        else:
            self.token_status_label.setText("⚠️ 未配置")
            self.token_status_label.setStyleSheet(
                f"color: {colors['warning']}; font-size: {Fonts.SIZE_SMALL}px;")

        # 更新 Cookie 状态
        _, cookie_source = self.config_manager.get_api_cookie_with_source()
        if cookie_source == 'config':
            self.cookie_status_label.setText("✓ 来自 config.yaml")
            self.cookie_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        elif cookie_source == 'env_file':
            self.cookie_status_label.setText("✓ 来自 .env 文件")
            self.cookie_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        elif cookie_source == 'system':
            self.cookie_status_label.setText("✓ 来自系统环境变量")
            self.cookie_status_label.setStyleSheet(
                f"color: {colors['success']}; font-size: {Fonts.SIZE_SMALL}px;")
        else:
            self.cookie_status_label.setText("⚠️ 未配置")
            self.cookie_status_label.setStyleSheet(
                f"color: {colors['warning']}; font-size: {Fonts.SIZE_SMALL}px;")

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

        # Token - 自动从各来源读取（包括系统环境变量）
        token, token_source = self.config_manager.get_api_token_with_source()
        self.token_input.setText(token or "")

        # Cookie - 自动从各来源读取（包括系统环境变量）
        cookie, cookie_source = self.config_manager.get_api_cookie_with_source()
        self.cookie_input.setPlainText(cookie or "")

        # RPA 模式配置
        urls = self.config_manager.get_article_urls()
        self.url_list.clear()
        for url in urls:
            self.url_list.addItem(url)

        # API Key - 自动从各来源读取（包括系统环境变量）
        api_key, api_key_source = self.config_manager.get_api_key_with_source()
        self.api_key_input.setText(api_key or "")

        # 根据任一敏感数据的来源，推断用户上次使用的保存方式
        # 如果有任何敏感数据来自 config，则默认选择 config 模式
        if token_source == 'config' or cookie_source == 'config' or api_key_source == 'config':
            self.radio_save_to_config.setChecked(True)
        else:
            # 否则默认选择 .env 模式（推荐）
            self.radio_save_to_env.setChecked(True)

        # 模型配置
        # 注意：findText() 找不到时返回 -1，需要判断 >= 0
        llm_model = self.config_manager.get_llm_model()
        if (index := self.llm_model_combo.findText(llm_model)) >= 0:
            self.llm_model_combo.setCurrentIndex(index)

        vlm_model = self.config_manager.get_vlm_model()
        if (index := self.vlm_model_combo.findText(vlm_model)) >= 0:
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

        # 发布配置 - 敏感数据（自动从各来源读取，包括系统环境变量）
        appid, appid_source = self.config_manager.get_wechat_appid()
        self.appid_input.setText(appid or "")
            
        appsecret, appsecret_source = self.config_manager.get_wechat_appsecret()
        self.appsecret_input.setText(appsecret or "")

        # 非敏感配置直接从 config.yaml 读取
        publish_config = self.config_manager.get_publish_config()
        if publish_config.get("author"):
            self.author_input.setText(publish_config.get("author"))
        if publish_config.get("cover_path"):
            self.cover_path_input.setText(publish_config.get("cover_path"))
        self.publish_title_input.setText(
            self.config_manager.get_publish_title())

        # 更新状态显示
        self._update_wechat_credentials_status()
        self._update_api_credentials_status()

    def _set_date_from_config(self, target_date) -> None:
        """从配置设置日期

        Args:
            target_date: 目标日期，可以是以下类型：
                - None 或 "today": 使用当天日期
                - "yesterday": 使用昨天日期
                - str (格式 "YYYY-MM-DD"): 解析字符串为日期
                - datetime.date 或 datetime.datetime: 直接使用（YAML 自动解析的结果）
        """
        if target_date is None or target_date == "today":
            self.date_edit.setDate(QDate.currentDate())
        elif target_date == "yesterday":
            self.date_edit.setDate(QDate.currentDate().addDays(-1))
        elif isinstance(target_date, datetime):
            # YAML 解析器可能返回 datetime 对象
            self.date_edit.setDate(
                QDate(target_date.year, target_date.month, target_date.day))
        elif isinstance(target_date, date):
            # YAML 解析器可能返回 date 对象
            self.date_edit.setDate(
                QDate(target_date.year, target_date.month, target_date.day))
        elif isinstance(target_date, str):
            try:
                parsed_date = datetime.strptime(target_date, "%Y-%m-%d")
                self.date_edit.setDate(
                    QDate(parsed_date.year, parsed_date.month, parsed_date.day))
            except ValueError:
                self.date_edit.setDate(QDate.currentDate())
        else:
            # 未知类型，使用当天日期
            self.date_edit.setDate(QDate.currentDate())

    def save_config(self) -> bool:
        """保存配置到配置管理器
        
        根据用户选择的保存方式（.env 文件或 config.yaml）统一处理所有敏感数据。
        """
        # 获取用户选择的敏感数据保存方式
        save_to_env = self.radio_save_to_env.isChecked()
        
        # 日期
        selected_date = self.get_selected_date()
        date_str = selected_date.strftime("%Y-%m-%d")
        self.config_manager.set_target_date(date_str)

        # API 模式配置 - 公众号名称列表（非敏感数据）
        account_names = []
        for i in range(self.account_list.count()):
            name = self.account_list.item(i).text().strip()
            if name:
                account_names.append(name)
        self.config_manager.set_account_names(account_names)

        # ==================== 敏感数据保存 ====================
        
        # Token
        current_token = self.token_input.text().strip()
        self.config_manager.set_api_token(current_token, save_to_env=save_to_env)

        # Cookie
        current_cookie = self.cookie_input.toPlainText().strip()
        self.config_manager.set_api_cookie(current_cookie, save_to_env=save_to_env)

        # API Key
        current_api_key = self.api_key_input.text().strip()
        self.config_manager.set_api_key(current_api_key, save_to_env=save_to_env)

        # AppID
        current_appid = self.appid_input.text().strip()
        self.config_manager.set_wechat_appid(current_appid, save_to_config=not save_to_env)

        # AppSecret
        current_appsecret = self.appsecret_input.text().strip()
        self.config_manager.set_wechat_appsecret(current_appsecret, save_to_config=not save_to_env)

        # ==================== RPA 模式配置（非敏感数据） ====================
        
        urls = []
        for i in range(self.url_list.count()):
            url = self.url_list.item(i).text().strip()
            if url:
                urls.append(url)
        self.config_manager.set_article_urls(urls)

        # ==================== 模型配置（非敏感数据） ====================
        
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

        # ==================== 发布配置（非敏感数据） ====================
        
        # 作者名
        author = self.author_input.text().strip()
        if author:
            self.config_manager.set_publish_author(author)
            
        # 封面路径
        cover_path = self.cover_path_input.text().strip()
        if cover_path:
            self.config_manager.set_publish_cover_path(cover_path)
            
        # 发布标题
        publish_title = self.publish_title_input.text().strip()
        if publish_title:
            self.config_manager.set_publish_title(publish_title)

        # 保存 config.yaml
        success = self.config_manager.save_config()
        
        if success and save_to_env:
            # 如果选择保存到 .env，显示提示信息
            from ..utils import EnvFileManager
            env_manager = EnvFileManager(self.config_manager.get_project_root())
            QMessageBox.information(
                self, "保存成功",
                f"配置已保存！\n\n敏感数据已保存到：\n{env_manager.get_file_path()}\n\n"
                f"💡 .env 文件已自动添加到 .gitignore，不会提交到版本控制。"
            )
        
        return success

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

    def _open_env_file(self) -> None:
        """打开 .env 文件"""
        from ..utils import EnvFileManager
        import subprocess
        import sys
        
        env_manager = EnvFileManager(self.config_manager.get_project_root())
        env_file = env_manager.get_file_path()
        
        if not env_manager.exists():
            # 文件不存在，询问是否创建
            reply = QMessageBox.question(
                self, "创建 .env 文件",
                ".env 文件不存在。是否创建？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # 创建空的 .env 文件
                env_manager.create({}, with_header=True)
                QMessageBox.information(self, "成功", f"已创建 .env 文件：\n{env_file}")
            else:
                return
        
        # 打开文件
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(env_file)])
            elif sys.platform == "win32":  # Windows
                os.startfile(str(env_file))
            else:  # Linux
                subprocess.run(["xdg-open", str(env_file)])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开文件：\n{e}")
