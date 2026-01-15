import subprocess
import logging
import sys
import pygetwindow as gw

# 使用 Windows API 激活窗口（更可靠）
import ctypes
import ctypes.wintypes
import pyautogui


def is_wechat_running(os_name: str) -> bool:
    """检查微信是否正在运行

    支持国内版（Weixin.exe）和国际版（WeChat.exe）

    Args:
        os_name (str): 操作系统名称

    Returns:
        bool: 如果微信正在运行，返回 True，否则返回 False
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
                logging.debug("检测到国内版微信正在运行")
                return True

            # 检查国际版微信
            result_wechat = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq WeChat.exe"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if "WeChat.exe" in result_wechat.stdout:
                logging.debug("检测到国际版微信正在运行")
                return True

            return False

        elif os_name == "darwin":
            # Mac: 使用 pgrep 命令
            result = subprocess.run(["pgrep", "-x", "WeChat"],
                                    capture_output=True)
            return result.returncode == 0
    except Exception as e:
        logging.error(f"检查微信进程失败: {e}")
        return False


def activate_wechat_window(os_name: str):
    """激活微信窗口到前台

    支持国内版（Weixin）和国际版（WeChat）

    Args:
        os_name (str): 操作系统名称
    """
    try:
        if os_name == "win32":
            # Windows: 通过进程名精确匹配微信窗口
            try:
                import psutil

                logging.debug("正在查找微信窗口...")

                # 获取所有窗口
                all_windows = gw.getAllWindows()
                wechat_window = None

                # 遍历所有窗口，通过进程名精确匹配
                for win in all_windows:
                    if not win.visible or not win.title:
                        continue

                    try:
                        # 通过窗口句柄获取进程ID
                        # pygetwindow 的 _hWnd 属性存储了窗口句柄
                        if hasattr(win, '_hWnd'):
                            import ctypes
                            import ctypes.wintypes

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
                                    logging.info(
                                        f"找到微信窗口: {win.title} (进程: {process_name})")
                                    break
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                    except Exception as e:
                        logging.debug(f"检查窗口 {win.title} 时出错: {e}")
                        continue

                if not wechat_window:
                    logging.error("未找到微信窗口")
                    raise RuntimeError("未找到微信窗口，请确保微信已打开")

                hwnd = wechat_window._hWnd

                # 定义 Windows 常量
                SW_RESTORE = 9  # 恢复窗口
                SW_SHOW = 5     # 显示窗口

                # 如果窗口最小化，先恢复
                if wechat_window.isMinimized:
                    logging.info("微信窗口已最小化，正在恢复...")
                    ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
                    import time
                    time.sleep(0.2)  # 等待窗口恢复

                # 确保窗口可见
                ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW)

                # 在激活窗口前，模拟鼠标移动，让 Windows 认为当前有用户交互
                # 这样可以绕过 SetForegroundWindow 的限制
                logging.debug("模拟鼠标移动以获取前台权限...")
                current_pos = pyautogui.position()
                pyautogui.moveTo(current_pos.x + 1,
                                 current_pos.y, duration=0.01)
                pyautogui.moveTo(current_pos.x, current_pos.y, duration=0.01)

                # 激活窗口到前台
                try:
                    # 先尝试使用 pygetwindow 的 activate()
                    wechat_window.activate()
                    logging.info("微信窗口已激活到前台")
                except Exception as e:
                    # 如果失败，使用更强制的方法
                    error_msg = str(e)
                    logging.debug(
                        f"pygetwindow.activate() 失败: {error_msg}，尝试使用备用方法...")

                    # 使用 SetForegroundWindow 强制激活
                    result = ctypes.windll.user32.SetForegroundWindow(hwnd)
                    if result:
                        logging.info("微信窗口已激活到前台（使用备用方法）")
                    else:
                        error_msg = "无法激活微信窗口，可能是 Windows 前台窗口限制导致"
                        logging.error(error_msg)
                        raise RuntimeError(error_msg)

            except ImportError:
                logging.error("需要安装 psutil 库: uv add psutil")
                raise RuntimeError("需要安装 psutil 库来精确识别微信窗口")
            except Exception as e:
                logging.exception("激活微信窗口失败")
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
            logging.info("微信窗口已激活")
    except Exception as e:
        logging.exception("激活微信窗口失败")
        raise
