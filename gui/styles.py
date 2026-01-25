# -*- coding: utf-8 -*-
"""
GUI 样式定义

定义应用的主题颜色、字体、样式表等。
"""

# ==================== 颜色定义 ====================


class Colors:
    """颜色常量"""

    # 主色调（微信绿 - 调整为更现代的色调）
    PRIMARY = "#07C160"
    PRIMARY_HOVER = "#06AD56"
    PRIMARY_PRESSED = "#059B4C"
    PRIMARY_LIGHT = "rgba(7, 193, 96, 0.1)"  # 浅绿色背景
    
    # 侧边栏颜色
    SIDEBAR_BG = "#F7F8FA"
    SIDEBAR_ITEM_HOVER = "#EAECEF"
    SIDEBAR_ITEM_SELECTED = "#FFFFFF"
    SIDEBAR_TEXT = "#1F2329"
    SIDEBAR_TEXT_SELECTED = "#07C160"

    # 背景色
    BG_WINDOW = "#FFFFFF"  # 整体背景
    BG_CONTENT = "#FFFFFF" # 内容区背景
    BG_CARD = "#FFFFFF"    # 卡片背景
    BG_INPUT = "#F5F7FA"   # 输入框背景
    BG_DISABLED = "#F5F5F5"
    
    # 文字颜色
    TEXT_PRIMARY = "#1F2329"  # 主要文字
    TEXT_SECONDARY = "#646A73" # 次要文字
    TEXT_HINT = "#8F959E"     # 提示文字
    TEXT_WHITE = "#FFFFFF"
    
    # 边框颜色
    BORDER = "#DEE0E3"
    BORDER_LIGHT = "#E8EAED"
    BORDER_FOCUS = "#07C160"
    
    # 阴影颜色
    SHADOW = "rgba(0, 0, 0, 0.05)"

    # 状态颜色
    SUCCESS = "#07C160"
    WARNING = "#FF9500"
    ERROR = "#F54A45"
    INFO = "#3370FF"

    # 日志级别颜色
    LOG_DEBUG = "#8F959E"
    LOG_INFO = "#1F2329"
    LOG_WARNING = "#FF9500"
    LOG_ERROR = "#F54A45"
    LOG_CRITICAL = "#D32F2F"


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


# ==================== 尺寸定义 ====================

class Sizes:
    """尺寸常量"""

    # 窗口尺寸
    WINDOW_MIN_WIDTH = 1000
    WINDOW_MIN_HEIGHT = 720
    WINDOW_DEFAULT_WIDTH = 1100
    WINDOW_DEFAULT_HEIGHT = 800

    # 侧边栏宽度（可拖拽调整）
    SIDEBAR_WIDTH = 260         # 默认宽度
    SIDEBAR_MIN_WIDTH = 220     # 最小宽度
    SIDEBAR_MAX_WIDTH = 350     # 最大宽度

    # 间距
    MARGIN_LARGE = 24
    MARGIN_MEDIUM = 16
    MARGIN_SMALL = 12
    MARGIN_TINY = 6

    # 圆角
    RADIUS_LARGE = 12
    RADIUS_MEDIUM = 8
    RADIUS_SMALL = 6

    # 控件高度
    BUTTON_HEIGHT = 36
    INPUT_HEIGHT = 36
    
    # 侧边栏项高度
    SIDEBAR_ITEM_HEIGHT = 44


# ==================== 样式表定义 ====================

def get_main_stylesheet() -> str:
    """获取主窗口样式表

    Returns:
        str: QSS 样式表字符串
    """
    return f"""
        /* ========== 全局样式 ========== */
        QWidget {{
            font-family: {Fonts.FAMILY};
            font-size: {Fonts.SIZE_BODY}px;
            color: {Colors.TEXT_PRIMARY};
            outline: none;
        }}
        
        QMainWindow {{
            background-color: {Colors.BG_WINDOW};
        }}
        
        /* ========== 侧边栏 ========== */
        QWidget#Sidebar {{
            background-color: {Colors.SIDEBAR_BG};
            border-right: 1px solid {Colors.BORDER_LIGHT};
        }}
        
        QLabel#AppTitle {{
            font-size: {Fonts.SIZE_SIDEBAR_TITLE}px;
            font-weight: bold;
            color: {Colors.TEXT_PRIMARY};
            padding: 20px;
        }}
        
        /* 侧边栏导航按钮 */
        QPushButton[class="NavButton"] {{
            text-align: left;
            padding-left: 20px;
            border: none;
            border-radius: {Sizes.RADIUS_MEDIUM}px;
            background-color: transparent;
            color: {Colors.TEXT_SECONDARY};
            font-size: {Fonts.SIZE_SIDEBAR_ITEM}px;
            height: {Sizes.SIDEBAR_ITEM_HEIGHT}px;
            margin: 2px 10px;
        }}
        
        QPushButton[class="NavButton"]:hover {{
            background-color: {Colors.SIDEBAR_ITEM_HOVER};
            color: {Colors.TEXT_PRIMARY};
        }}
        
        QPushButton[class="NavButton"]:checked {{
            background-color: {Colors.SIDEBAR_ITEM_SELECTED};
            color: {Colors.SIDEBAR_TEXT_SELECTED};
            font-weight: 600;
            /* 选中时的阴影效果由代码添加，这里只处理背景 */
        }}
        
        /* ========== 内容区 ========== */
        QWidget#ContentArea {{
            background-color: {Colors.BG_CONTENT};
        }}
        
        /* ========== 卡片样式 (QGroupBox) ========== */
        QGroupBox {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER_LIGHT};
            border-radius: {Sizes.RADIUS_LARGE}px;
            margin-top: 0px; /* 取消顶部 margin，因为标题移到内部了 */
            padding-top: 40px; /* 为内部标题留出空间 */
            padding-bottom: 16px;
            padding-left: 16px;
            padding-right: 16px;
        }}

        QGroupBox::title {{
            subcontrol-origin: padding; /* 关键：标题在 padding 区域，即边框内部 */
            subcontrol-position: top left;
            left: 16px;
            top: 12px; /* 距离顶部边框的距离 */
            padding: 0px;
            color: {Colors.TEXT_PRIMARY};
            font-weight: 600;
            font-size: {Fonts.SIZE_SUBTITLE}px;
            background-color: transparent; 
        }}
        
        /* ========== 按钮 ========== */
        QPushButton {{
            background-color: {Colors.BG_WINDOW};
            border: 1px solid {Colors.BORDER};
            border-radius: {Sizes.RADIUS_SMALL}px;
            padding: 6px 16px;
            min-height: {Sizes.BUTTON_HEIGHT - 8}px;
            color: {Colors.TEXT_PRIMARY};
        }}
        
        QPushButton:hover {{
            border-color: {Colors.PRIMARY};
            color: {Colors.PRIMARY};
            background-color: {Colors.BG_INPUT};
        }}
        
        QPushButton:pressed {{
            background-color: {Colors.PRIMARY_LIGHT};
        }}
        
        /* 主要按钮 (Primary) */
        QPushButton[primary="true"] {{
            background-color: {Colors.PRIMARY};
            border: none;
            color: {Colors.TEXT_WHITE};
            font-weight: 600;
        }}
        
        QPushButton[primary="true"]:hover {{
            background-color: {Colors.PRIMARY_HOVER};
        }}
        
        QPushButton[primary="true"]:pressed {{
            background-color: {Colors.PRIMARY_PRESSED};
        }}
        
        QPushButton[primary="true"]:disabled {{
            background-color: {Colors.BG_DISABLED};
            color: {Colors.TEXT_HINT};
        }}
        
        /* 危险按钮 (Danger) */
        QPushButton[danger="true"] {{
            color: {Colors.ERROR};
            border-color: {Colors.BORDER};
        }}
        
        QPushButton[danger="true"]:hover {{
            background-color: {Colors.ERROR};
            color: {Colors.TEXT_WHITE};
            border-color: {Colors.ERROR};
        }}
        
        /* 幽灵按钮 (Ghost/Transparent) */
        QPushButton[ghost="true"] {{
            background-color: transparent;
            border: none;
        }}
        
        QPushButton[ghost="true"]:hover {{
            background-color: {Colors.SIDEBAR_ITEM_HOVER};
        }}

        /* ========== 输入框 ========== */
        QLineEdit, QDateEdit, QSpinBox, QComboBox {{
            background-color: {Colors.BG_INPUT};
            border: 1px solid transparent;
            border-radius: {Sizes.RADIUS_SMALL}px;
            padding: 6px 12px;
            min-height: {Sizes.INPUT_HEIGHT - 12}px;
            color: {Colors.TEXT_PRIMARY};
        }}
        
        QLineEdit:focus, QDateEdit:focus, QSpinBox:focus, QComboBox:focus {{
            background-color: {Colors.BG_WINDOW};
            border: 1px solid {Colors.PRIMARY};
        }}
        
        QLineEdit:hover, QDateEdit:hover, QSpinBox:hover, QComboBox:hover {{
            background-color: {Colors.BG_WINDOW};
        }}
        
        /* ========== 列表 (QListWidget) ========== */
        QListWidget {{
            background-color: {Colors.BG_INPUT};
            border: 1px solid transparent;
            border-radius: {Sizes.RADIUS_MEDIUM}px;
            padding: 4px;
        }}
        
        QListWidget::item {{
            padding: 8px;
            border-radius: {Sizes.RADIUS_SMALL}px;
        }}
        
        QListWidget::item:selected {{
            background-color: {Colors.BG_WINDOW};
            color: {Colors.PRIMARY};
            border: 1px solid {Colors.PRIMARY_LIGHT};
        }}
        
        QListWidget::item:hover:!selected {{
            background-color: {Colors.BG_WINDOW};
        }}
        
        /* ========== 日志区域 ========== */
        QTextEdit {{
            background-color: #1E1E1E;
            color: #D4D4D4;
            border: 1px solid {Colors.BORDER};
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
            background: #D0D0D0;
            min-height: 30px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #A0A0A0;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        /* ========== 状态栏 ========== */
        QStatusBar {{
            background-color: {Colors.BG_WINDOW};
            border-top: 1px solid {Colors.BORDER_LIGHT};
            color: {Colors.TEXT_SECONDARY};
        }}

        /* ========== 分隔条 (QSplitter) ========== */
        QSplitter::handle:horizontal {{
            background-color: {Colors.BORDER_LIGHT};
            width: 3px;
        }}
        QSplitter::handle:horizontal:hover {{
            background-color: {Colors.PRIMARY};
        }}
    """


def get_log_level_color(level: int) -> str:
    """根据日志级别获取颜色 (用于 Rich Text)

    Args:
        level: 日志级别

    Returns:
        str: 颜色代码
    """
    import logging

    if level >= logging.CRITICAL:
        return "#FF4D4F" # Red
    elif level >= logging.ERROR:
        return "#FF4D4F" # Red
    elif level >= logging.WARNING:
        return "#FAAD14" # Orange
    elif level >= logging.INFO:
        return "#52C41A" # Green (Success/Info)
    else:
        return "#8C8C8C" # Grey


def apply_shadow_effect(widget, blur_radius: int = 15, offset: tuple = (0, 4),
                        color: str = "rgba(0, 0, 0, 0.04)") -> None:
    """为控件应用阴影效果"""
    from PyQt6.QtWidgets import QGraphicsDropShadowEffect
    from PyQt6.QtGui import QColor

    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setOffset(offset[0], offset[1])
    shadow.setColor(QColor(color))
    widget.setGraphicsEffect(shadow)
