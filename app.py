# -*- coding: utf-8 -*-
"""
微信 AI 日报助手 - 桌面客户端入口

运行方式：
    uv run app.py
    
或者：
    uv run python app.py
"""

import logging
from wechat_ai_daily.utils.env_loader import load_env
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

# 强制切换到应用根目录，避免从非应用目录启动导致相对路径失效
# 这样 logs、configs、templates 等相对路径都以 APP_ROOT 为基准
os.chdir(APP_ROOT)

# 确保项目根目录在 Python 路径中
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

# 确保 src 目录在 Python 路径中（用于导入 wechat_ai_daily 模块）
# 注意：打包后 src 目录的内容已经包含在 exe 中，但开发时仍需要
src_path = os.path.join(APP_ROOT, "src")
if os.path.isdir(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)

# 加载 .env 环境变量（必须在其他模块导入前调用）
load_env()

# 导入 logging（用于记录法律声明）


def show_legal_notice(app):
    """显示法律声明对话框

    Args:
        app: QApplication 实例，用于获取系统主题

    Returns:
        bool: 用户是否同意条款（True=同意，False=不同意）
    """
    from PyQt6.QtWidgets import QMessageBox
    from PyQt6.QtCore import Qt

    # 记录法律声明到日志
    logging.warning("=" * 70)
    logging.warning("⚠️  GUI 启动 - 显示法律声明对话框")
    logging.warning("本工具仅供个人学习和研究使用，请勿用于商业目的。")
    logging.warning("用户必须同意法律声明才能继续使用。")
    logging.warning("=" * 70)

    msg_box = QMessageBox()
    msg_box.setWindowTitle("⚠️ 法律声明")
    msg_box.setIcon(QMessageBox.Icon.Warning)

    # 设置详细的法律声明文本
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

    # 添加"同意"和"不同意"按钮
    msg_box.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    msg_box.setDefaultButton(QMessageBox.StandardButton.No)

    # 自定义按钮文本
    yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
    no_button = msg_box.button(QMessageBox.StandardButton.No)
    yes_button.setText("我已阅读并同意")
    no_button.setText("不同意，退出")

    # 设置对话框最小宽度，确保内容显示完整
    msg_box.setMinimumWidth(500)

    # 移除自定义样式，使用系统默认样式以适配黑白主题
    # 不设置 styleSheet，让系统自动适配主题

    # 显示对话框并获取用户响应
    result = msg_box.exec()

    # 记录用户选择
    if result == QMessageBox.StandardButton.Yes:
        logging.info("用户已同意法律声明，继续启动应用")
    else:
        logging.warning("用户不同意法律声明，退出应用")

    return result == QMessageBox.StandardButton.Yes


def main():
    """应用主入口"""
    # 配置日志（在创建 GUI 前配置）
    from pathlib import Path
    # 使用应用根目录作为日志基准路径，避免依赖当前工作目录
    log_dir = Path(APP_ROOT) / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # 输出到控制台
            logging.FileHandler(str(log_dir / "app.log"),
                                encoding="utf-8")  # 输出到文件
        ]
    )

    logging.info("=" * 70)
    logging.info("微信 AI 日报助手 - 桌面客户端启动")
    logging.info("=" * 70)

    # 导入 PyQt6（延迟导入，避免在路径设置前导入）
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont

    # 导入主窗口（统一入口）
    from apps.desktop import MainWindow

    # 创建应用
    app = QApplication(sys.argv)

    # 设置应用属性
    app.setApplicationName("微信 AI 日报助手")
    app.setApplicationVersion("2.2.0")
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

    # 显示法律声明对话框（在创建 QApplication 之后调用，以确保正确获取系统主题）
    if not show_legal_notice(app):
        # 用户不同意条款，退出应用
        logging.info("应用退出")
        return 0

    # 创建并显示主窗口
    logging.info("创建主窗口")
    window = MainWindow()
    window.show()
    logging.info("主窗口已显示，进入事件循环")

    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
