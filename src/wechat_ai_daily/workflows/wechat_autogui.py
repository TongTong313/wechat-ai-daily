import subprocess
import sys
import time
import logging
import yaml
import pyautogui
from typing import List

from ..utils.wechat import is_wechat_running, activate_wechat_window
from ..utils.extractors import extract_biz_from_wechat_article_url
from ..utils.autogui import press_keys


class OfficialAccountArticleCollector:
    """获取微信公众号文章
    
    Args:
        config (str): 配置文件的路径地址，默认为 "configs/config.yaml"
    """

    def __init__(self, config: str = "configs/config.yaml"):
        """初始化公众号文章收集器"""
        # 获取操作系统的名称
        self.os_name = sys.platform
        self.config = config
        self.LOAD_DELAY = 3.0  # 加载延迟时间
        self.PRESS_DELAY = 0.5  # 按键间隔时间

    def _open_wechat(self):
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

    def _open_wechat_search(self):
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

    def build_workflow(self):
        pass

    def run(self):
        pass
