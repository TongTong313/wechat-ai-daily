# -*- coding: utf-8 -*-
"""
GUI 样式定义

定义应用的主题颜色、字体、样式表等。
"""

from typing import Dict

# ==================== 字体定义 ====================

class Fonts:
    """字体常量"""

    # 字体族
    FAMILY = "Microsoft YaHei UI, PingFang SC, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica Neue, Arial, sans-serif"
    FAMILY_MONO = "JetBrains Mono, Cascadia Code, Consolas, Monaco, monospace"

    # 字体大小
    SIZE_TITLE = 18
    SIZE_SUBTITLE = 14
    SIZE_BODY = 13
    SIZE_SMALL = 12
    SIZE_TINY = 11
    
    # 侧边栏字体
    SIZE_SIDEBAR_TITLE = 16
    SIZE_SIDEBAR_ITEM = 14
    SIZE_SIDEBAR_SECTION = 12

# ==================== 尺寸定义 ====================

class Sizes:
    """尺寸常量"""

    # 窗口尺寸
    WINDOW_MIN_WIDTH = 1000
    WINDOW_MIN_HEIGHT = 720
    WINDOW_DEFAULT_WIDTH = 1100
    WINDOW_DEFAULT_HEIGHT = 800

    # 侧边栏宽度（可拖拽调整）
    SIDEBAR_WIDTH = 250         # 默认宽度稍微调小
    SIDEBAR_MIN_WIDTH = 220     # 最小宽度
    SIDEBAR_MAX_WIDTH = 320     # 最大宽度

    # 间距
    MARGIN_LARGE = 20           # 调小大间距
    MARGIN_MEDIUM = 12          # 调小中间距
    MARGIN_SMALL = 8            # 调小
    MARGIN_TINY = 4

    # 圆角
    RADIUS_LARGE = 12
    RADIUS_MEDIUM = 8
    RADIUS_SMALL = 6

    # 控件高度
    BUTTON_HEIGHT = 36
    INPUT_HEIGHT = 36
    
    # 侧边栏项高度
    SIDEBAR_ITEM_HEIGHT = 44


# ==================== 兼容性颜色定义 (Deprecated) ====================
# 保留此类以防其他模块直接引用报错，但在新逻辑中应优先使用 ThemeManager
class Colors:
    PRIMARY = "#07C160"
    INFO = "#3370FF"
    SUCCESS = "#07C160"
    WARNING = "#FF9500"
    ERROR = "#F54A45"
    TEXT_PRIMARY = "#1F2329"
    TEXT_SECONDARY = "#646A73"
    TEXT_HINT = "#8F959E"
    BORDER_LIGHT = "#E8EAED"
    BG_WINDOW = "#FFFFFF"
    BG_CARD = "#FFFFFF"
    BG_INPUT = "#F5F7FA"
    BG_DISABLED = "#F5F5F5"


# ==================== 样式表定义 ====================

def get_main_stylesheet(colors: Dict[str, str]) -> str:
    """获取主窗口样式表

    Args:
        colors: 主题颜色字典 (from ThemeManager)

    Returns:
        str: QSS 样式表字符串
    """
    return f"""
        /* ========== 全局样式 ========== */
        QWidget {{
            font-family: {Fonts.FAMILY};
            font-size: {Fonts.SIZE_BODY}px;
            color: {colors['text_primary']};
            outline: none;
        }}
        
        QMainWindow {{
            background-color: {colors['window_bg']};
        }}
        
        /* ========== 侧边栏 ========== */
        QWidget#Sidebar {{
            background-color: {colors['sidebar_bg']};
            border-right: 1px solid {colors['border_light']};
        }}
        
        QLabel#AppTitle {{
            font-size: {Fonts.SIZE_SIDEBAR_TITLE}px;
            font-weight: bold;
            color: {colors['text_sidebar']};
            padding: 20px;
        }}
        
        /* 侧边栏导航按钮 */
        QPushButton[class="NavButton"] {{
            text-align: left;
            padding-left: 20px;
            border: none;
            border-radius: {Sizes.RADIUS_MEDIUM}px;
            background-color: transparent;
            color: {colors['text_secondary']};
            font-size: {Fonts.SIZE_SIDEBAR_ITEM}px;
            height: {Sizes.SIDEBAR_ITEM_HEIGHT}px;
            margin: 2px 10px;
        }}
        
        QPushButton[class="NavButton"]:hover {{
            background-color: {colors['sidebar_item_hover']};
            color: {colors['text_primary']};
        }}
        
        QPushButton[class="NavButton"]:checked {{
            background-color: {colors['sidebar_item_selected']};
            color: {colors['text_sidebar_selected']};
            font-weight: 600;
        }}
        
        /* ========== 内容区 ========== */
        QWidget#ContentArea {{
            background-color: {colors['content_bg']};
        }}
        
        /* ========== 卡片样式 (QGroupBox) ========== */
        QGroupBox {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border_light']};
            border-radius: {Sizes.RADIUS_LARGE}px;
            margin-top: 12px;
            padding-top: 24px;
            padding-bottom: 20px;
            padding-left: 20px;
            padding-right: 20px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 20px;
            top: 0px;
            padding: 0px 8px;
            color: {colors['text_primary']};
            font-weight: 600;
            font-size: {Fonts.SIZE_SUBTITLE}px;
            background-color: {colors['card_bg']};
        }}
        
        /* ========== 按钮 ========== */
        QPushButton {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {Sizes.RADIUS_SMALL}px;
            padding: 6px 16px;
            min-height: {Sizes.BUTTON_HEIGHT - 8}px;
            color: {colors['text_primary']};
        }}
        
        QPushButton:hover {{
            border-color: {colors['primary']};
            color: {colors['primary']};
            background-color: {colors['button_hover_bg']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['primary_light']};
        }}
        
        /* 主要按钮 (Primary) */
        QPushButton[primary="true"] {{
            background-color: {colors['primary']};
            border: none;
            color: {colors['text_white']};
            font-weight: 600;
        }}
        
        QPushButton[primary="true"]:hover {{
            background-color: {colors['primary_hover']};
        }}
        
        QPushButton[primary="true"]:pressed {{
            background-color: {colors['primary_pressed']};
        }}
        
        QPushButton[primary="true"]:disabled {{
            background-color: {colors['border_light']};
            color: {colors['text_hint']};
        }}
        
        /* 危险按钮 (Danger) */
        QPushButton[danger="true"] {{
            color: {colors['error']};
            border-color: {colors['border']};
        }}
        
        QPushButton[danger="true"]:hover {{
            background-color: {colors['error']};
            color: {colors['text_white']};
            border-color: {colors['error']};
        }}
        
        /* 幽灵按钮 (Ghost/Transparent) */
        QPushButton[ghost="true"] {{
            background-color: transparent;
            border: none;
        }}
        
        QPushButton[ghost="true"]:hover {{
            background-color: {colors['sidebar_item_hover']};
        }}

        /* ========== 输入框 ========== */
        QLineEdit, QDateEdit, QSpinBox, QComboBox {{
            background-color: {colors['input_bg']};
            border: 1px solid transparent;
            border-radius: {Sizes.RADIUS_SMALL}px;
            padding: 6px 12px;
            min-height: {Sizes.INPUT_HEIGHT - 12}px;
            color: {colors['text_primary']};
        }}
        
        QLineEdit:focus, QDateEdit:focus, QSpinBox:focus, QComboBox:focus {{
            background-color: {colors['input_bg']};
            border: 1px solid {colors['primary']};
        }}
        
        QLineEdit:hover, QDateEdit:hover, QSpinBox:hover, QComboBox:hover {{
            background-color: {colors['input_bg_hover']};
        }}
        
        /* ========== 列表 (QListWidget) ========== */
        QListWidget {{
            background-color: {colors['input_bg']};
            border: 1px solid transparent;
            border-radius: {Sizes.RADIUS_MEDIUM}px;
            padding: 4px;
            color: {colors['text_primary']};
        }}
        
        QListWidget::item {{
            padding: 8px;
            border-radius: {Sizes.RADIUS_SMALL}px;
        }}
        
        QListWidget::item:selected {{
            background-color: {colors['card_bg']};
            color: {colors['primary']};
            border: 1px solid {colors['primary_light']};
        }}
        
        QListWidget::item:hover:!selected {{
            background-color: {colors['input_bg_hover']};
        }}
        
        /* ========== 日志区域 ========== */
        QTextEdit {{
            background-color: {colors['log_bg']};
            color: {colors['log_text']};
            border: 1px solid {colors['log_border']};
            border-radius: {Sizes.RADIUS_MEDIUM}px;
            padding: 12px;
            font-family: {Fonts.FAMILY_MONO};
            font-size: {Fonts.SIZE_SMALL}px;
        }}
        
        /* ========== 滚动条 ========== */
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {colors['border']};
            min-height: 30px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {colors['text_hint']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        /* ========== 状态栏 ========== */
        QStatusBar {{
            background-color: {colors['window_bg']};
            border-top: 1px solid {colors['border_light']};
            color: {colors['text_secondary']};
        }}

        /* ========== 分隔条 (QSplitter) ========== */
        QSplitter::handle:horizontal {{
            background-color: {colors['splitter_handle']};
            width: 3px;
        }}
        QSplitter::handle:horizontal:hover {{
            background-color: {colors['primary']};
        }}
    """


def get_log_level_color(level: int, is_dark: bool = False) -> str:
    """根据日志级别获取颜色 (用于 Rich Text)

    Args:
        level: 日志级别
        is_dark: 是否为深色模式

    Returns:
        str: 颜色代码
    """
    import logging

    if level >= logging.CRITICAL:
        return "#FF6B6B" if is_dark else "#FF4D4F" # Red
    elif level >= logging.ERROR:
        return "#FF6B6B" if is_dark else "#FF4D4F" # Red
    elif level >= logging.WARNING:
        return "#FFC069" if is_dark else "#FAAD14" # Orange
    elif level >= logging.INFO:
        return "#52C41A" if is_dark else "#52C41A" # Green
    else:
        return "#AAAAAA" if is_dark else "#8C8C8C" # Grey


def apply_shadow_effect(widget, blur_radius: int = 15, offset: tuple = (0, 4),
                        color: str = "rgba(0, 0, 0, 0.05)") -> None:
    """为控件应用阴影效果"""
    from PyQt6.QtWidgets import QGraphicsDropShadowEffect
    from PyQt6.QtGui import QColor

    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setOffset(offset[0], offset[1])
    shadow.setColor(QColor(color))
    widget.setGraphicsEffect(shadow)
