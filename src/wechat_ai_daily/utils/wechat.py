import subprocess
import logging


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
            # Windows: 使用 PowerShell 激活窗口
            # 同时支持国内版（Weixin）和国际版（WeChat）
            ps_script = """
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class WinAPI {
                    [DllImport("user32.dll")]
                    public static extern bool SetForegroundWindow(IntPtr hWnd);
                    [DllImport("user32.dll")]
                    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                }
"@
            # 先尝试查找国内版微信（Weixin）
            $process = Get-Process -Name Weixin -ErrorAction SilentlyContinue | Select-Object -First 1

            # 如果找不到，尝试查找国际版微信（WeChat）
            if (-not $process) {
                $process = Get-Process -Name WeChat -ErrorAction SilentlyContinue | Select-Object -First 1
            }

            # 激活窗口
            if ($process) {
                [WinAPI]::ShowWindow($process.MainWindowHandle, 9)
                [WinAPI]::SetForegroundWindow($process.MainWindowHandle)
            }
            """
            subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            logging.info("微信窗口已激活")
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
