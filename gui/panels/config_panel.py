# -*- coding: utf-8 -*-
"""
配置面板

包含日期选择、文章链接管理、API Key 设置、模型配置、模板配置等功能。
重新设计的现代化 UI 界面。
"""

from datetime import datetime
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton,
    QListWidget, QComboBox, QCheckBox, QRadioButton,
    QDateEdit, QMessageBox, QInputDialog, QFrame,
    QSpinBox, QFileDialog, QButtonGroup, QSizePolicy,
    QScrollArea
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction

from ..utils.config_manager import ConfigManager
from ..styles import Colors, Sizes, apply_shadow_effect, Fonts


class ConfigPanel(QWidget):
    """配置面板
    
    提供应用配置的 UI 界面。
    """

    # 配置变化信号
    config_changed = pyqtSignal()

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._setup_ui()
        self._load_config()
        self._connect_signals()

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
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(Sizes.MARGIN_LARGE)
        content_layout.setContentsMargins(Sizes.MARGIN_LARGE, Sizes.MARGIN_LARGE, Sizes.MARGIN_LARGE, Sizes.MARGIN_LARGE)
        
        # 1. 顶部：日期设置 (横向卡片)
        date_card = self._create_date_card()
        apply_shadow_effect(date_card)
        content_layout.addWidget(date_card)
        
        # 2. 中部：文章链接 (大卡片)
        urls_card = self._create_urls_card()
        apply_shadow_effect(urls_card)
        content_layout.addWidget(urls_card)
        
        # 3. 底部：高级设置 (API & 模型)
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(Sizes.MARGIN_LARGE)
        
        # 左侧：API Key
        api_card = self._create_api_card()
        apply_shadow_effect(api_card)
        settings_layout.addWidget(api_card, 1)
        
        # 右侧：模型配置
        model_card = self._create_model_card()
        apply_shadow_effect(model_card, 1)
        settings_layout.addWidget(model_card, 1)
        
        content_layout.addLayout(settings_layout)
        
        # 4. 模板设置 (折叠或底部)
        template_card = self._create_template_card()
        apply_shadow_effect(template_card)
        content_layout.addWidget(template_card)
        
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _create_date_card(self) -> QGroupBox:
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

    def _create_urls_card(self) -> QGroupBox:
        group = QGroupBox("🔗 公众号文章链接")
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
        self.url_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.url_list.setMinimumHeight(120)
        self.url_list.setMaximumHeight(200)
        layout.addWidget(self.url_list)
        
        # 提示
        hint = QLabel("💡 每个公众号仅需提供一篇近期文章链接，系统将自动定位该公众号。")
        hint.setStyleSheet(f"color: {Colors.TEXT_HINT}; font-size: {Fonts.SIZE_SMALL}px;")
        layout.addWidget(hint)
        
        group.setLayout(layout)
        return group

    def _create_api_card(self) -> QGroupBox:
        group = QGroupBox("🔑 API Key")
        layout = QVBoxLayout()
        layout.setSpacing(Sizes.MARGIN_SMALL)
        
        # 输入框
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        layout.addWidget(self.api_key_input)
        
        # 显示切换
        hbox = QHBoxLayout()
        self.chk_show_key = QCheckBox("显示 Key")
        self.chk_show_key.stateChanged.connect(self._toggle_api_key_visibility)
        hbox.addWidget(self.chk_show_key)
        hbox.addStretch()
        layout.addLayout(hbox)
        
        # 来源选择
        self.api_key_source_group = QButtonGroup(self)
        
        self.radio_use_env = QRadioButton("使用环境变量 (推荐)")
        self.api_key_source_group.addButton(self.radio_use_env, 0)
        layout.addWidget(self.radio_use_env)
        
        self.radio_save_to_config = QRadioButton("保存到配置文件")
        self.api_key_source_group.addButton(self.radio_save_to_config, 1)
        layout.addWidget(self.radio_save_to_config)
        
        # 状态
        self.env_status_label = QLabel()
        self.env_status_label.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}px;")
        layout.addWidget(self.env_status_label)
        self._update_env_status()
        
        group.setLayout(layout)
        return group

    def _create_model_card(self) -> QGroupBox:
        group = QGroupBox("🤖 模型配置")
        layout = QGridLayout()
        layout.setVerticalSpacing(Sizes.MARGIN_SMALL)
        layout.setHorizontalSpacing(Sizes.MARGIN_MEDIUM)
        
        # LLM
        layout.addWidget(QLabel("文本模型:"), 0, 0)
        self.llm_model_combo = QComboBox()
        self.llm_model_combo.addItems(["qwen-plus", "qwen-turbo", "qwen-max", "qwen-long"])
        layout.addWidget(self.llm_model_combo, 0, 1)
        
        # VLM
        layout.addWidget(QLabel("视觉模型:"), 1, 0)
        self.vlm_model_combo = QComboBox()
        self.vlm_model_combo.addItems(["qwen3-vl-plus", "qwen-vl-max", "qwen-vl-plus"])
        layout.addWidget(self.vlm_model_combo, 1, 1)
        
        # Thinking
        layout.addWidget(QLabel("思考模式:"), 2, 0)
        self.chk_enable_thinking = QCheckBox("启用")
        layout.addWidget(self.chk_enable_thinking, 2, 1)
        
        layout.addWidget(QLabel("思考预算:"), 3, 0)
        self.thinking_budget_spin = QSpinBox()
        self.thinking_budget_spin.setRange(256, 8192)
        self.thinking_budget_spin.setSingleStep(256)
        self.thinking_budget_spin.setSuffix(" tokens")
        layout.addWidget(self.thinking_budget_spin, 3, 1)
        
        group.setLayout(layout)
        return group

    def _create_template_card(self) -> QGroupBox:
        group = QGroupBox("🖼️ 界面模板 (高级)")
        # 默认折叠或简化显示
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
            btn.clicked.connect(lambda checked, k=key: self._browse_template(k))
            layout.addWidget(btn, i, 2)

        group.setLayout(layout)
        return group

    def _update_env_status(self) -> None:
        if self.config_manager.has_env_api_key():
            self.env_status_label.setText("✓ 已检测到环境变量")
            self.env_status_label.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: {Fonts.SIZE_SMALL}px;")
        else:
            self.env_status_label.setText("✗ 未检测到环境变量")
            self.env_status_label.setStyleSheet(f"color: {Colors.WARNING}; font-size: {Fonts.SIZE_SMALL}px;")

    def _connect_signals(self) -> None:
        self.date_edit.dateChanged.connect(self._on_config_changed)
        self.url_list.itemChanged.connect(self._on_config_changed)
        self.api_key_input.textChanged.connect(self._on_config_changed)
        self.api_key_source_group.buttonClicked.connect(self._on_config_changed)
        self.llm_model_combo.currentTextChanged.connect(self._on_config_changed)
        self.vlm_model_combo.currentTextChanged.connect(self._on_config_changed)
        self.chk_enable_thinking.stateChanged.connect(self._on_thinking_state_changed)
        self.thinking_budget_spin.valueChanged.connect(self._on_config_changed)

    def _on_thinking_state_changed(self, state: int) -> None:
        enabled = state == Qt.CheckState.Checked.value
        self.thinking_budget_spin.setEnabled(enabled)
        self._on_config_changed()

    def _load_config(self) -> None:
        target_date = self.config_manager.get_target_date()
        self._set_date_from_config(target_date)

        urls = self.config_manager.get_article_urls()
        self.url_list.clear()
        for url in urls:
            self.url_list.addItem(url)

        config_api_key = self.config_manager.get_config_api_key()
        if config_api_key:
            self.api_key_input.setText(config_api_key)
            self.radio_save_to_config.setChecked(True)
        else:
            env_api_key = self.config_manager.get_env_api_key()
            if env_api_key:
                self.api_key_input.setText(env_api_key)
            self.radio_use_env.setChecked(True)

        llm_model = self.config_manager.get_llm_model()
        if index := self.llm_model_combo.findText(llm_model):
            self.llm_model_combo.setCurrentIndex(index)

        vlm_model = self.config_manager.get_vlm_model()
        if index := self.vlm_model_combo.findText(vlm_model):
            self.vlm_model_combo.setCurrentIndex(index)

        enable_thinking = self.config_manager.get_enable_thinking()
        self.chk_enable_thinking.setChecked(enable_thinking)
        self.thinking_budget_spin.setEnabled(enable_thinking)
        self.thinking_budget_spin.setValue(self.config_manager.get_thinking_budget())

        gui_config = self.config_manager.get_gui_config()
        for key, input_field in self.template_inputs.items():
            if key in gui_config:
                input_field.setText(gui_config[key])

    def _set_date_from_config(self, target_date: Optional[str]) -> None:
        if target_date is None or target_date == "today":
            self.date_edit.setDate(QDate.currentDate())
        elif target_date == "yesterday":
            self.date_edit.setDate(QDate.currentDate().addDays(-1))
        else:
            try:
                parsed_date = datetime.strptime(target_date, "%Y-%m-%d")
                self.date_edit.setDate(QDate(parsed_date.year, parsed_date.month, parsed_date.day))
            except ValueError:
                self.date_edit.setDate(QDate.currentDate())

    def save_config(self) -> bool:
        selected_date = self.get_selected_date()
        date_str = selected_date.strftime("%Y-%m-%d")
        self.config_manager.set_target_date(date_str)

        urls = []
        for i in range(self.url_list.count()):
            url = self.url_list.item(i).text().strip()
            if url:
                urls.append(url)
        self.config_manager.set_article_urls(urls)

        api_key = self.api_key_input.text().strip()
        if api_key:
            save_to_env = self.radio_use_env.isChecked()
            self.config_manager.set_api_key(api_key, save_to_env=save_to_env)

        self.config_manager.set_llm_model(self.llm_model_combo.currentText())
        self.config_manager.set_vlm_model(self.vlm_model_combo.currentText())
        self.config_manager.set_enable_thinking(self.chk_enable_thinking.isChecked())
        self.config_manager.set_thinking_budget(self.thinking_budget_spin.value())

        for key, input_field in self.template_inputs.items():
            path = input_field.text().strip()
            if path:
                self.config_manager.set_gui_template_path(key, path)

        return self.config_manager.save_config()

    def get_selected_date(self) -> datetime:
        qdate = self.date_edit.date()
        return datetime(qdate.year(), qdate.month(), qdate.day())

    def validate_config(self) -> tuple[bool, str]:
        if self.url_list.count() == 0:
            return False, "请至少添加一个文章链接"
        
        api_key = self.api_key_input.text().strip()
        env_api_key = self.config_manager.get_env_api_key()
        if not api_key and not env_api_key:
            return False, "请设置 API Key"
            
        return True, ""

    def _set_today(self) -> None:
        self.date_edit.setDate(QDate.currentDate())

    def _set_yesterday(self) -> None:
        self.date_edit.setDate(QDate.currentDate().addDays(-1))

    def _add_url(self) -> None:
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
        for item in self.url_list.selectedItems():
            self.url_list.takeItem(self.url_list.row(item))
        self._on_config_changed()

    def _reload_urls(self) -> None:
        self.config_manager.load_config()
        urls = self.config_manager.get_article_urls()
        self.url_list.clear()
        for url in urls:
            self.url_list.addItem(url)

    def _toggle_api_key_visibility(self, state: int) -> None:
        if state == Qt.CheckState.Checked.value:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _browse_template(self, key: str) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"选择模板 - {key}",
            str(self.config_manager.get_project_root() / "templates"),
            "图片 (*.png *.jpg)"
        )
        if file_path:
            self.template_inputs[key].setText(file_path)
            self._on_config_changed()

    def _on_config_changed(self) -> None:
        self.config_changed.emit()
