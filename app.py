# -*- coding: utf-8 -*-
"""
微信 AI 日报助手 - 桌面客户端入口

运行方式：
    uv run app.py
    
或者：
    uv run python app.py
"""

import sys
import os


def get_application_path() -> str:
    """获取应用程序根目录路径
    
    兼容 PyInstaller 打包后的环境：
    - 打包后：返回 exe 文件所在目录
    - 开发时：返回 app.py 所在目录
    
    Returns:
        str: 应用程序根目录的绝对路径
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的环境
        # sys.executable 是 exe 文件的完整路径
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))


# 获取应用根目录（必须在导入其他模块之前）
APP_ROOT = get_application_path()

# 设置环境变量，供其他模块使用
os.environ['WECHAT_AI_DAILY_ROOT'] = APP_ROOT

# 确保项目根目录在 Python 路径中
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

# 确保 src 目录在 Python 路径中（用于导入 wechat_ai_daily 模块）
# 注意：打包后 src 目录的内容已经包含在 exe 中，但开发时仍需要
src_path = os.path.join(APP_ROOT, "src")
if os.path.isdir(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)


def main():
    """应用主入口"""
    # 导入 PyQt6（延迟导入，避免在路径设置前导入）
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont

    # 导入主窗口
    from gui import MainWindow

    # 创建应用
    app = QApplication(sys.argv)

    # 设置应用属性
    app.setApplicationName("微信 AI 日报助手")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("WechatAIDaily")

    # 设置默认字体
    # 注意：setFamily() 只接受单个字体名称，不支持 CSS 风格的 fallback 列表
    # 使用 setFamilies() 来设置多个备选字体
    font = QFont()
    font.setFamilies(["Microsoft YaHei", "PingFang SC",
                     "Helvetica Neue", "Arial", "sans-serif"])
    font.setPointSize(10)
    app.setFont(font)

    # 启用高 DPI 缩放（PyQt6 默认已启用）
    # 如果需要进一步调整，可以设置环境变量
    # os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
