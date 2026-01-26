"""微信进程管理和窗口控制"""

import subprocess
import logging
import time
import ctypes
import ctypes.wintypes
import pygetwindow as gw


logger = logging.getLogger(__name__)


def is_wechat_running(os_name: str) -> bool:
    """检查微信是否正在运行

    支持国内版（Weixin.exe）和国际版（WeChat.exe）

    Args:
        os_name: 操作系统名称（win32 或 darwin）

    Returns:
        如果微信正在运行，返回 True，否则返回 False
    """
    try:
        if os_name == "win32":
            # Windows: 使用 tasklist 命令
            # 同时检查国内版（Weixin.exe）和国际版（WeChat.exe）

            # 检查国内版微信
            result_weixin = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Weixin.exe"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if "Weixin.exe" in result_weixin.stdout:
                logger.debug("检测到国内版微信正在运行")
                return True

            # 检查国际版微信
            result_wechat = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq WeChat.exe"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if "WeChat.exe" in result_wechat.stdout:
                logger.debug("检测到国际版微信正在运行")
                return True

            return False

        elif os_name == "darwin":
            # Mac: 使用 pgrep 命令
            result = subprocess.run(["pgrep", "-x", "WeChat"],
                                    capture_output=True)
            return result.returncode == 0
    except Exception as e:
        logger.error(f"检查微信进程失败: {e}")
        return False


def activate_wechat_window(os_name: str) -> None:
    """激活微信窗口到前台

    支持国内版（Weixin）和国际版（WeChat）

    Args:
        os_name: 操作系统名称（win32 或 darwin）
        
    Raises:
        RuntimeError: 激活窗口失败时抛出
    """
    try:
        if os_name == "win32":
            # Windows: 通过进程名精确匹配微信窗口
            try:
                import psutil

                logger.debug("正在查找微信窗口...")

                # 获取所有窗口
                all_windows = gw.getAllWindows()
                wechat_window = None

                # 遍历所有窗口，通过进程名精确匹配
                for win in all_windows:
                    if not win.visible or not win.title:
                        continue

                    try:
                        # 通过窗口句柄获取进程ID
                        if hasattr(win, '_hWnd'):
                            # 获取窗口对应的进程ID
                            process_id = ctypes.wintypes.DWORD()
                            ctypes.windll.user32.GetWindowThreadProcessId(
                                win._hWnd,
                                ctypes.byref(process_id)
                            )

                            # 获取进程名
                            try:
                                process = psutil.Process(process_id.value)
                                process_name = process.name().lower()

                                # 检查是否为微信进程
                                if process_name in ['weixin.exe', 'wechat.exe']:
                                    wechat_window = win
                                    logger.info(
                                        f"找到微信窗口: {win.title} (进程: {process_name})")
                                    break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                    except Exception as e:
                        logger.debug(f"检查窗口 {win.title} 时出错: {e}")
                        continue

                if not wechat_window:
                    logger.error("未找到微信窗口")
                    raise RuntimeError("未找到微信窗口，请确保微信已打开")

                hwnd = wechat_window._hWnd

                # 定义 Windows 常量
                SW_RESTORE = 9  # 恢复窗口
                SW_SHOW = 5     # 显示窗口

                # 如果窗口最小化，先恢复
                if wechat_window.isMinimized:
                    logger.info("微信窗口已最小化，正在恢复...")
                    ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
                    time.sleep(0.2)

                # 确保窗口可见
                ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW)

                # 模拟 Alt 键按下释放，获取前台激活权限
                # Windows 在检测到 Alt 键事件后，会短暂允许 SetForegroundWindow
                VK_MENU = 0x12  # Alt 键虚拟键码
                KEYEVENTF_EXTENDEDKEY = 0x0001
                KEYEVENTF_KEYUP = 0x0002
                ctypes.windll.user32.keybd_event(
                    VK_MENU, 0, KEYEVENTF_EXTENDEDKEY, 0)
                ctypes.windll.user32.keybd_event(
                    VK_MENU, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)

                # 激活窗口到前台
                result = ctypes.windll.user32.SetForegroundWindow(hwnd)
                if result:
                    logger.info("微信窗口已激活到前台")
                else:
                    error_msg = "无法激活微信窗口"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

            except ImportError:
                logger.error("需要安装 psutil 库: uv add psutil")
                raise RuntimeError("需要安装 psutil 库来精确识别微信窗口")
            except Exception as e:
                logger.exception("激活微信窗口失败")
                raise

        elif os_name == "darwin":
            # Mac: 使用 osascript 激活应用
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "WeChat" to activate',
                ],
                capture_output=True,
            )
            logger.info("微信窗口已激活")
    except Exception as e:
        logger.exception("激活微信窗口失败")
        raise
