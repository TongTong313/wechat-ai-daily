import subprocess
import logging
import pygetwindow as gw


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
            # Windows: 使用 pygetwindow（更可靠）
            try:

                # 查找微信窗口（支持中英文标题）
                logging.debug("正在查找微信窗口...")
                wechat_windows = (
                    gw.getWindowsWithTitle("微信") or
                    gw.getWindowsWithTitle("WeChat")
                )

                if not wechat_windows:
                    logging.error("未找到微信窗口")
                    raise RuntimeError("未找到微信窗口，请确保微信已打开")

                # 激活第一个找到的微信窗口
                win = wechat_windows[0]
                logging.info(f"找到微信窗口: {win.title}")

                # 如果窗口最小化，先恢复
                if win.isMinimized:
                    logging.info("微信窗口已最小化，正在恢复...")
                    win.restore()

                # 激活窗口
                win.activate()
                logging.info("微信窗口已激活到前台")
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
