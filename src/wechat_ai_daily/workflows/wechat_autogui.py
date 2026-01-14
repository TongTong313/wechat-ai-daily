import subprocess
import sys
import time
import logging
import yaml
import pyautogui
import pyperclip
import os
from typing import List

from ..utils.wechat import is_wechat_running, activate_wechat_window
from ..utils.extractors import extract_biz_from_wechat_article_url
from ..utils.autogui import press_keys
from openai import AsyncOpenAI


class OfficialAccountArticleCollector:
    """获取微信公众号文章
    
    Args:
        config (str): 配置文件的路径地址，默认为 "configs/config.yaml"
    """

    def __init__(self, config: str = "configs/config.yaml") -> None:
        """初始化公众号文章收集器"""
        # 获取操作系统的名称
        self.os_name = sys.platform
        self.config = config
        self.vlm_client = AsyncOpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.LOAD_DELAY = 3.0  # 加载延迟时间
        self.PRESS_DELAY = 0.5  # 按键间隔时间
        self.CLICK_DELAY = 0.5  # 点击后延迟时间

    def _open_wechat(self) -> None:
        """打开微信应用程序"""
        try:
            # 先检查微信是否已经运行
            if is_wechat_running(self.os_name):
                logging.info("微信已在运行，正在激活窗口...")
                activate_wechat_window(self.os_name)
                time.sleep(1)
                return

            # 微信未运行，启动它
            logging.info("正在启动微信...")
            if self.os_name == "win32":
                # Windows: 使用协议启动
                protocol_success = False

                # 先尝试国内版协议 weixin://
                try:
                    logging.info("尝试使用 weixin:// 协议启动微信...")
                    subprocess.Popen(
                        ["cmd", "/c", "start", "", "weixin://"],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                    # 等待一小段时间，检查是否启动成功
                    time.sleep(self.LOAD_DELAY)
                    if is_wechat_running(self.os_name):
                        logging.info("使用 weixin:// 协议启动成功")
                        protocol_success = True
                except Exception as e:
                    logging.debug(f"weixin:// 协议启动失败: {e}")

                # 如果 weixin:// 失败，尝试国际版协议 wechat://
                if not protocol_success:
                    try:
                        logging.info("尝试使用 wechat:// 协议启动微信...")
                        subprocess.Popen(
                            ["cmd", "/c", "start", "", "wechat://"],
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                        # 等待一小段时间，检查是否启动成功
                        time.sleep(self.LOAD_DELAY)
                        if is_wechat_running(self.os_name):
                            logging.info("使用 wechat:// 协议启动成功")
                            protocol_success = True
                    except Exception as e:
                        logging.debug(f"wechat:// 协议启动失败: {e}")

                # 如果协议启动都失败，抛出错误
                if not protocol_success:
                    raise RuntimeError(
                        "无法使用协议启动微信。\n"
                        "请确保微信已正确安装，并且系统已注册 weixin:// 或 wechat:// 协议。")

            elif self.os_name == "darwin":
                # Mac: 使用 open 命令
                subprocess.Popen(["open", "-a", "WeChat"])
            else:
                raise OSError(f"不支持的操作系统: {self.os_name}")

            # 等待微信启动
            logging.info("等待微信启动...")
            time.sleep(self.LOAD_DELAY)

            # 启动后激活窗口
            activate_wechat_window(self.os_name)
            logging.info("微信已启动并激活")

        except Exception as e:
            logging.exception("打开微信失败")
            raise

    def _build_official_account_url(self) -> List[str]:
        """
        构建公众号文章URL列表，因为配置的可能是多个URL，对应多个不同的公众号，这里要有一个去重

        Returns:
            List[str]: 构建后的公众号文章URL列表
        """
        # 读取配置文件，获取文章的url
        try:
            with open(self.config, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except Exception as e:
            logging.exception(f"读取配置文件失败: {e}")
            raise

        article_urls = config_data.get("article_urls", [])

        biz_list = []

        # 分别生成对应的biz
        for url in article_urls:
            biz = extract_biz_from_wechat_article_url(url)
            if biz:
                logging.info(f"从URL {url} 提取到biz: {biz}")
                biz_list.append(biz)
            else:
                logging.warning(f"从URL {url} 无法提取到biz")

        # 对biz去重
        biz_list = list(set(biz_list))

        if not biz_list:
            logging.error("没有找到有效的biz，无法生成公众号URL，无法进行后续操作")
            raise ValueError("没有找到有效的biz，无法生成公众号URL，无法进行后续操作")

        # 对于biz生成对应公众号的url
        base_url = "https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz={}&scene=124"
        official_account_urls = [base_url.format(biz) for biz in biz_list]

        return official_account_urls

    def _open_wechat_search(self) -> None:
        """
        打开微信搜索功能并点击"搜索网络结果"

        步骤：
        1. 使用快捷键打开微信搜索（Mac: cmd+f, Windows: ctrl+f）
        2. 等待搜索框出现
        3. 按向下键选中"搜索网络结果"选项
        4. 按 Enter 键确认打开搜索界面
        """
        try:
            # 步骤1: 根据操作系统使用不同的快捷键打开搜索
            logging.info("正在打开微信搜索...")
            if self.os_name == "darwin":
                # Mac: 使用 cmd+f
                press_keys("cmd", "f")
                logging.info("已发送 cmd+f 快捷键")
            elif self.os_name == "win32":
                # Windows: 使用 ctrl+f
                press_keys("ctrl", "f")
                logging.info("已发送 ctrl+f 快捷键")
            else:
                raise OSError(f"不支持的操作系统: {self.os_name}")

            # 步骤2: 等待搜索框出现
            logging.info("等待搜索框出现...")
            time.sleep(self.LOAD_DELAY)

            # 步骤3: 按向下键选中"搜索网络结果"选项
            logging.info("按向下键选中'搜索网络结果'选项...")
            press_keys("down")
            logging.info("已选中'搜索网络结果'选项")
            time.sleep(self.PRESS_DELAY)

            # 步骤4: 按 Enter 键确认
            logging.info("按 Enter 键确认...")
            press_keys("enter")
            logging.info("已按 Enter 键")

            # 等待搜索界面打开
            time.sleep(self.LOAD_DELAY)
            logging.info("微信搜索界面已打开")

        except Exception as e:
            logging.exception("打开微信搜索失败")
            raise

    def _search_official_account_url(self, url: str) -> None:
        """在微信搜索界面当中输入公众号的url，然后点击下方的网页打开公众号主页

        Args:
            url (str): 公众号的url
        """
        try:
            # 步骤1: 将公众号URL复制到剪贴板
            logging.info(f"正在复制公众号URL到剪贴板: {url}")
            pyperclip.copy(url)

            # 步骤2: 粘贴URL到搜索框（假设焦点已在搜索框中）
            logging.info("正在粘贴URL到搜索框...")
            if self.os_name == "darwin":
                # Mac: 使用 cmd+v
                press_keys("cmd", "v")
            elif self.os_name == "win32":
                # Windows: 使用 ctrl+v
                press_keys("ctrl", "v")
            else:
                raise OSError(f"不支持的操作系统: {self.os_name}")

            time.sleep(self.PRESS_DELAY)
            logging.info("URL已粘贴到搜索框")

            # 步骤3: 按回车键触发搜索
            logging.info("正在按回车键触发搜索...")
            press_keys("enter")
            logging.info("已按回车键")

            # 步骤4: 等待搜索结果出现
            logging.info("等待搜索结果出现...")
            time.sleep(self.LOAD_DELAY)

            # 步骤5: 查找并点击"访问网页"按钮
            logging.info("正在查找'访问网页'按钮...")
            template_path = "templates/search_website.png"

            # 尝试在屏幕上定位按钮（设置置信度为0.8，使用灰度匹配提高速度）
            button_location = pyautogui.locateOnScreen(str(template_path),
                                                       confidence=0.8,
                                                       grayscale=True)
            logging.info(f"图像识别结果: {button_location}")

            if button_location is None:
                logging.error(f"无法在屏幕上找到'访问网页'按钮")
                raise RuntimeError(f"无法在屏幕上找到'访问网页'按钮。\n"
                                   f"请确保：\n"
                                   f"1. 微信搜索结果已显示\n"
                                   f"2. 模板图片 {template_path} 存在\n"
                                   f"3. 屏幕分辨率与模板图片匹配\n"
                                   f"4. 可以尝试调整 confidence 参数（当前为 0.8）")

            # 获取按钮中心点的物理像素坐标
            center_x, center_y = pyautogui.center(button_location)
            logging.info(f"找到'访问网页'按钮，物理像素坐标: ({center_x}, {center_y})")

            # ============================================================
            # 显示屏坐标转换（处理 Retina 等高分辨率显示屏）
            # ============================================================
            # 问题背景：
            #   - macOS Retina 显示屏使用 2x 缩放（或更高）
            #   - pyautogui.screenshot() 返回的是物理像素（如 3840x2160）
            #   - pyautogui.locateOnScreen() 基于截图，返回物理像素坐标
            #   - pyautogui.click() 使用的是逻辑坐标（如 1920x1080）
            #
            # 如果不做转换：
            #   - 识别到物理像素坐标 (1765, 938)
            #   - 直接点击会被系统理解为逻辑坐标 (1765, 938)
            #   - 实际点击到物理像素 (3530, 1876)，位置完全错误！
            #
            # 解决方案：
            #   - 计算缩放比例 = 截图尺寸 / 逻辑屏幕尺寸
            #   - 将物理像素坐标除以缩放比例，得到正确的逻辑坐标
            # ============================================================

            # 获取逻辑屏幕尺寸和截图尺寸，计算缩放比例
            screen_width, screen_height = pyautogui.size()
            screenshot = pyautogui.screenshot()
            scale_x = screenshot.width / screen_width
            scale_y = screenshot.height / screen_height
            logging.info(f"屏幕缩放比例: x={scale_x}, y={scale_y}")

            # 将物理像素坐标转换为逻辑坐标
            click_x = int(center_x / scale_x)
            click_y = int(center_y / scale_y)
            logging.info(f"转换后的逻辑坐标: ({click_x}, {click_y})")

            # 使用逻辑坐标点击按钮
            pyautogui.click(click_x, click_y)
            time.sleep(self.CLICK_DELAY)
            logging.info("已点击'访问网页'按钮")

            # 步骤6: 等待公众号主页加载完成
            logging.info("等待公众号主页加载...")
            time.sleep(self.LOAD_DELAY)
            logging.info("公众号主页已加载完成")

        except Exception as e:
            logging.exception("搜索公众号失败")
            raise

    def build_workflow(self) -> None:
        pass

    def run(self) -> None:
        pass
