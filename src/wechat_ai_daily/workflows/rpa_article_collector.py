"""
公众号文章列表获取工作流（RPA 版本）

通过 GUI 自动化 + VLM 视觉识别技术获取微信公众号文章列表，相比 API 方案：
优势：无需微信公众号账号，无需登录后台，开箱即用
缺点：依赖 GUI 界面，速度较慢，稳定性受系统环境影响

使用前提：
1. 已安装微信客户端（Windows 或 macOS）
2. 微信客户端保持登录状态
3. 在 config.yaml 完成相关配置

使用示例：
    >>> from wechat_ai_daily.workflows.rpa_article_collector import RPAArticleCollector
    >>>
    >>> # 初始化工作流（从 config.yaml 读取所有配置）
    >>> collector = RPAArticleCollector(config="configs/config.yaml")
    >>>
    >>> # 运行工作流（异步，使用配置文件中的所有参数）
    >>> import asyncio
    >>> output_file = asyncio.run(collector.run())
"""

import subprocess
import sys
import time
import logging
from ruamel.yaml import YAML
import pyperclip
import os
import shutil
import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from openai import AsyncOpenAI

from .base import BaseWorkflow
from ..utils.wechat import is_wechat_running, activate_wechat_window
from ..utils.autogui import (
    press_keys,
    scroll_down,
    screenshot_current_window,
    click_relative_position,
    click_button_based_on_img,
)
from ..utils.vlm import chat_with_vlm, encode_img_to_base64
from ..utils.paths import get_project_root, get_output_dir, get_temp_dir


class RPAArticleCollector(BaseWorkflow):
    """获取微信公众号文章

    Args:
        config (str): 配置文件的路径地址，默认为 "configs/config.yaml"
        vlm_client (AsyncOpenAI, optional): VLM 客户端，如果不提供则使用默认配置创建
        model (str): VLM 模型名称，默认为 "qwen3-vl-plus"
        enable_thinking (bool): 是否启用思考模式，默认为 True
        thinking_budget (int): 思考预算（token数），默认为 1024
    """

    def __init__(self,
                 config: str = "configs/config.yaml",
                 vlm_client: Optional[AsyncOpenAI] = None,
                 model: str = "qwen3-vl-plus",
                 enable_thinking: bool = True,
                 thinking_budget: int = 1024) -> None:
        """初始化公众号文章收集器
        """
        # 获取操作系统的名称
        self.os_name = sys.platform
        yaml = YAML()
        with open(config, "r", encoding="utf-8") as f:
            self.config = yaml.load(f)

        # 从配置读取 RPA 模式专属参数
        self.article_urls = self.config.get("article_urls", [])
        if not self.article_urls:
            raise ValueError("配置文件中缺少 article_urls 参数")

        # 读取目标日期配置
        self.target_date_config = self.config.get("target_date")

        # 初始化 VLM 客户端
        # 优先级：参数传入 > config.yaml > 环境变量
        if vlm_client is None:
            # 读取 VLM api_key
            # 优先级：config.yaml > .env 文件 > 系统环境变量
            config_api_key = self.config.get("model_config", {}).get("VLM", {}).get("api_key")
            # 注意：os.getenv 会读取环境变量（已在 env_loader 中加载 .env 文件，.env 优先于系统环境变量）
            api_key = config_api_key if config_api_key else os.getenv("DASHSCOPE_API_KEY")
            
            self.vlm_client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        else:
            self.vlm_client = vlm_client

        # # ==================== VLM 模型配置 ====================
        # self.model = model                        # VLM 模型名称
        # self.enable_thinking = enable_thinking    # 是否启用思考模式
        # self.thinking_budget = thinking_budget    # 思考预算（token数）

        # ==================== 延迟时间配置 ====================
        self.LOAD_DELAY = 3.0       # 页面加载延迟时间（秒）
        self.PRESS_DELAY = 0.5      # 按键间隔时间（秒）
        self.CLICK_DELAY = 0.5      # 点击后延迟时间（秒）

        # ==================== 滚动配置 ====================
        self.SCROLL_AMOUNT = -800   # 向下滚动量（负数向下，约大半屏）
        self.MAX_SCROLL_TIMES = 5   # 最大滚动次数（防止无限循环）

        # ==================== 临时文件路径（兼容 PyInstaller 打包）====================
        self.TEMP_SCREENSHOT_PATH = str(get_temp_dir() / "screenshot.png")

    def _extract_biz_from_wechat_article_url(self, article_url: str) -> Optional[str]:
        """
        从微信公众号文章页面中提取 biz 参数

        使用 requests 库发送 HTTP GET 请求获取页面内容，然后使用正则表达式从 HTML 中提取 biz 参数。

        Args:
            article_url (str): 微信公众号文章的 URL 地址

        Returns:
            Optional[str]: 公众号的 biz 标识符（字符串），如果提取失败则返回 None
        """
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

        try:
            # 发送 HTTP GET 请求获取页面内容
            logging.info(f"正在访问页面: {article_url}")
            response = requests.get(article_url, headers=headers, timeout=10)

            if response.status_code != 200:
                logging.error(f"请求失败，状态码: {response.status_code}")
                return None

            html_content = response.text
            logging.info(f"成功获取页面内容，长度: {len(html_content)} 字符")

        except requests.exceptions.RequestException as e:
            logging.exception(f"网络请求出错: {e}")
            return None

        # 使用正则表达式从 HTML 中提取 biz 参数
        # 匹配 biz: "xxx" 或 biz: 'xxx' 格式
        pattern = r'biz:\s*["\']([^"\']+)["\']'
        match = re.search(pattern, html_content)

        if match:
            biz = match.group(1)
            logging.info(f"成功提取 biz: {biz}")
            return biz
        else:
            logging.error("未能在页面中找到 biz 参数")
            return None

    def _cleanup_temp_folder(self) -> None:
        """
        清理 temp 临时文件夹，防止用户隐私信息泄露

        在工作流执行完成后调用，删除截图等临时文件。
        无论工作流执行成功还是失败，都应该调用此方法清理敏感数据。

        Returns:
            None
        """
        # 从截图路径获取临时文件夹路径
        temp_dir = os.path.dirname(self.TEMP_SCREENSHOT_PATH)

        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logging.info(f"已清理临时文件夹: {temp_dir}")
            except Exception as e:
                logging.warning(f"清理临时文件夹失败: {e}")
        else:
            logging.debug(f"临时文件夹不存在，无需清理: {temp_dir}")

    def _open_wechat(self) -> None:
        """
        打开微信应用程序

        Returns:
            None
        """
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
        # 从实例属性读取文章URL列表
        article_urls = self.article_urls

        biz_list = []

        # 分别生成对应的biz
        for url in article_urls:
            biz = self._extract_biz_from_wechat_article_url(url)
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
        # 注意：URL末尾使用 #wechat_redirect 而不是 &scene=124
        base_url = "https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz={}#wechat_redirect"
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
        """
        在微信搜索界面当中输入公众号的url，然后点击下方的网页打开公众号主页

        Args:
            url (str): 公众号的url

        Returns:
            None
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

            # 根据操作系统选择对应的模板图片
            template_path = self.config.get(
                "GUI_config", {}).get("search_website", "")
            if not template_path:
                raise ValueError("没有找到访问网页按钮模板图片")

            # 使用通用函数点击按钮
            click_button_based_on_img(template_path, self.CLICK_DELAY)
            logging.info("已点击'访问网页'按钮")

            # 步骤6: 等待公众号主页加载完成
            logging.info("等待公众号主页加载...")
            time.sleep(self.LOAD_DELAY)
            logging.info("公众号主页已加载完成")

        except Exception as e:
            logging.exception("搜索公众号失败")
            raise

    # ==================== 文章列表采集辅助方法 ====================

    def _copy_article_link(self) -> str:
        """复制当前文章链接

        步骤：
        1. 截图当前页面
        2. 使用图像识别找到右上角三个点 (three_dots.png)
        3. 点击三个点打开菜单
        4. 等待菜单出现
        5. 按6次向下箭头选中"复制链接"选项
        6. 按 Enter 确认复制
        7. 从剪贴板读取链接并返回

        根据操作系统选择不同的模板图片：
        - macOS: three_dots_mac.png (更精确的点击位置)
        - Windows: three_dots.png

        Returns:
            str: 文章链接
        """
        try:
            # 查找并点击三个点按钮
            logging.info("正在查找'三个点'按钮...")

            # 根据操作系统选择模板图片
            template_path = self.config.get(
                "GUI_config", {}).get("three_dots", "")
            if not template_path:
                raise ValueError("没有找到三个点按钮模板图片")

            # 使用通用函数点击按钮
            click_button_based_on_img(template_path, self.CLICK_DELAY)
            logging.info("已点击'三个点'按钮")

            # 等待菜单出现
            logging.info("等待菜单出现...")
            time.sleep(self.LOAD_DELAY)

            # 按6次向下箭头选中"复制链接"选项
            logging.info("按6次向下箭头选中'复制链接'选项...")
            for i in range(6):
                press_keys("down")
                time.sleep(0.05)  # 这里按键次数多，所以降低sleep时间

            # 按 Enter 确认复制
            logging.info("按 Enter 复制链接...")
            press_keys("enter")
            time.sleep(self.PRESS_DELAY)

            # 从剪贴板读取链接
            link = pyperclip.paste()
            logging.info(f"已复制文章链接: {link}")

            return link

        except Exception as e:
            logging.exception("复制文章链接失败")
            raise

    def _go_back_to_homepage(self) -> None:
        """点击返回按钮回到公众号主页

        使用图像识别定位 turnback.png 并点击，
        然后等待主页加载完成。

        根据操作系统选择不同的模板图片：
        - macOS: turnback_mac.png (更精确的点击位置)
        - Windows: turnback.png
        """
        try:
            logging.info("正在查找'返回'按钮...")

            # 根据操作系统选择模板图片
            template_path = self.config.get(
                "GUI_config", {}).get("turnback", "")
            if not template_path:
                raise ValueError("没有找到返回按钮模板图片")

            # 使用通用函数点击按钮
            click_button_based_on_img(template_path, click_delay=0)  # 不需要额外延迟
            logging.info("已点击'返回'按钮")

            # 等待主页加载完成
            logging.info("等待公众号主页加载...")
            time.sleep(self.LOAD_DELAY)
            logging.info("已返回公众号主页")

        except Exception as e:
            logging.exception("返回公众号主页失败")
            raise

    def _save_article_to_file(
        self,
        link: str,
        article_index: int,
        output_path: str
    ) -> None:
        """将文章链接追加保存到 Markdown 文件

        Args:
            link: 文章链接
            article_index: 文章序号（从1开始）
            output_path: 输出文件路径
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 构建文章内容块（只包含链接）
            article_block = f"{article_index}. {link}\n"

            # 追加写入文件
            with open(output_path, "a", encoding="utf-8") as f:
                f.write(article_block)

            logging.info(f"文章 {article_index} 链接已保存到: {output_path}")

        except Exception as e:
            logging.exception(f"保存文章 {article_index} 链接失败")
            raise

    def _init_output_file(self, output_path: str, target_date: Optional[datetime] = None) -> None:
        """
        初始化输出文件，写入文件头

        Args:
            output_path (str): 输出文件路径
            target_date (datetime, optional): 目标日期，默认为当天

        Returns:
            None
        """
        try:
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # 获取当前时间用于采集时间
            now = datetime.now()
            collection_time_str = now.strftime('%Y年%m月%d日 %H:%M:%S')

            # 获取目标日期
            if target_date is None:
                target_date = now
            target_date_str = target_date.strftime('%Y-%m-%d')

            # 写入文件头（与 APIArticleCollector 格式保持一致）
            header = f"""# 公众号文章链接采集结果
采集时间：{collection_time_str}
目标日期：{target_date_str}
采集方式：GUI自动化 + VLM视觉识别
---

"""
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(header)

            logging.info(f"输出文件已初始化: {output_path}")

        except Exception as e:
            logging.exception("初始化输出文件失败")
            raise

    def _append_account_separator(
        self,
        output_path: str,
        account_index: int,
        account_url: str
    ) -> None:
        """在文件中添加公众号分隔标记

        Args:
            output_path: 输出文件路径
            account_index: 公众号序号
            account_url: 公众号URL（用于显示）
        """
        try:
            # 构建公众号分隔块
            separator = f"\n## 公众号 {account_index}\n"
            separator += f"URL: {account_url}\n\n"

            # 追加写入文件
            with open(output_path, "a", encoding="utf-8") as f:
                f.write(separator)

            logging.info(f"已添加公众号 {account_index} 分隔标记")

        except Exception as e:
            logging.exception(f"添加公众号 {account_index} 分隔标记失败")
            raise

    async def _get_dates_location_from_img(
            self,
            img_path: str,
            dates: List[str],
            max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        调用 VLM 模型识别图片中指定日期的位置

        根据configs/config.yaml 文件中的 model_config 配置，配置VLM模型调用参数。

        Args:
            img_path (str): 图片路径
            dates (List[str]): 要查找的日期列表
            max_retries (int): 最大重试次数，默认为 3

        Returns:
            List[Dict[str, Any]]: 包含位置信息的列表，每个元素为 {'date': str, 'x': float, 'y': float, 'width': float, 'height': float}
                - date: 找到的日期
                - x: 中心点相对 x 坐标 (0-1)
                - y: 中心点相对 y 坐标 (0-1)
                - width: 相对宽度 (0-1)
                - height: 相对高度 (0-1)

            注意：
                - 如果图片中不存在任何匹配的日期，返回空列表 []
                - 如果只找到部分日期，只返回找到的日期位置信息
                - 返回结果数量可能少于输入的 dates 数量

        Raises:
            ValueError: 当达到最大重试次数仍无法成功解析时抛出（仅在格式错误时，不会因为未找到文本而抛出）
        """

        # 获取VLM模型配置
        model = self.config.get("model_config", {}).get(
            "VLM", {}).get("model", "qwen3-vl-plus")
        enable_thinking = self.config.get("model_config", {}).get(
            "VLM", {}).get("enable_thinking", True)
        thinking_budget = self.config.get("model_config", {}).get(
            "VLM", {}).get("thinking_budget", 1024)

        def _parse_xml_locations(
                response: str) -> tuple[bool, List[Dict[str, Any]]]:
            """
            解析模型返回的 XML 格式位置信息（相对坐标），并进行校验

            根据提示词要求，解析格式为（一个 location 块内包含多个日期位置）：
            <location>
                <date>要查找的日期1</date>
                <x>0.5</x>
                <y>0.5</y>
                <width>0.2</width>
                <height>0.125</height>
                <date>要查找的日期2</date>
                <x>0.3</x>
                <y>0.3</y>
                <width>0.25</width>
                <height>0.25</height>
            </location>

            Args:
                response: 模型返回的原始文本

            Returns:
                tuple[bool, List[Dict[str, Any]]]:
                    - 第一个值：是否解析成功（True/False）
                    - 第二个值：解析后的位置列表，每个位置包含 date, x, y, width, height 五个键

            校验规则：
                - 如果没有找到任何 location，返回 (True, [])（表示成功解析但未找到日期）
                - 如果某个日期位置缺少 date/x/y/width/height 任一字段，返回 (False, [])
                - 如果坐标值不在 0-1 范围内，返回 (False, [])
                - 解析到任意数量的完整且有效的日期位置，都返回 (True, locations)
            """
            locations = []

            # 使用正则表达式匹配 <location>...</location> 块
            location_pattern = r'<location>(.*?)</location>'
            location_match = re.search(location_pattern, response, re.DOTALL)

            if not location_match:
                logging.info("未找到任何 <location> 标签，返回空结果")
                return (True, [])  # 未找到日期不是错误，返回成功+空列表

            location_content = location_match.group(1)

            # 在单个 location 块内，找到所有的 <date> 标签位置，以此来分割多组日期位置
            # 使用 finditer 获取所有 <date> 标签的位置
            date_matches = list(re.finditer(
                r'<date>(.*?)</date>', location_content))

            if not date_matches:
                logging.info("location 块内未找到任何 <date> 标签，返回空结果")
                return (True, [])

            # 获取所有坐标值（按顺序）
            x_matches = list(re.finditer(r'<x>(.*?)</x>', location_content))
            y_matches = list(re.finditer(r'<y>(.*?)</y>', location_content))
            width_matches = list(re.finditer(
                r'<width>(.*?)</width>', location_content))
            height_matches = list(re.finditer(
                r'<height>(.*?)</height>', location_content))

            # 检查数量是否匹配
            num_dates = len(date_matches)
            if not (len(x_matches) == len(y_matches) == len(width_matches) == len(height_matches) == num_dates):
                logging.error(
                    f"解析失败：字段数量不匹配 - date:{num_dates}, x:{len(x_matches)}, "
                    f"y:{len(y_matches)}, width:{len(width_matches)}, height:{len(height_matches)}")
                return (False, [])

            # 按顺序解析每组日期位置
            for i in range(num_dates):
                try:
                    # 提取日期内容
                    date_text = date_matches[i].group(1).strip()

                    # 提取并转换为浮点数
                    x = float(x_matches[i].group(1).strip())
                    y = float(y_matches[i].group(1).strip())
                    width = float(width_matches[i].group(1).strip())
                    height = float(height_matches[i].group(1).strip())

                    # 校验范围 0-1
                    values = {'x': x, 'y': y, 'width': width, 'height': height}
                    for name, value in values.items():
                        if not (0 <= value <= 1):
                            logging.error(
                                f"解析失败：第 {i + 1} 个日期位置的 {name}={value} 超出 0-1 范围"
                            )
                            return (False, [])

                    # 添加到结果列表（使用 date 字段存储日期内容）
                    locations.append({
                        'date': date_text,
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height
                    })

                except (ValueError, AttributeError) as e:
                    logging.exception(f"解析失败：第 {i + 1} 个日期位置的坐标值无法转换为数字")
                    return (False, [])

            # 所有日期位置都解析成功且校验通过
            logging.info(f"解析成功：找到 {len(locations)} 个有效日期位置")
            return (True, locations)

        # 构建提示词，要求模型返回相对坐标（0-1之间的比例）
        system_prompt = """
# 角色定位
你是一个文本定位助手，你的任务是：
1. 在图片中找到**完全匹配用户需求**的日期，并返回每个匹配日期的位置信息。
2. 返回的日期位置信息包含日期内容、日期文本内容的中心点相对坐标和日期文本内容的相对宽度和高度。

# 输出格式要求
所有找到的日期位置统一放在一个 <location> 块内，每个日期依次输出：
<location>
    <date>找到的日期1</date>
    <x>中心点x相对坐标1</x>
    <y>中心点y相对坐标1</y>
    <width>相对宽度1</width>
    <height>相对高度1</height>
    <date>找到的日期2</date>
    <x>中心点x相对坐标2</x>
    <y>中心点y相对坐标2</y>
    <width>相对宽度2</width>
    <height>相对高度2</height>
    ...
</location>

# 要求
1. **必须完全匹配**用户指定的日期，不能有任何偏差
2. <date> 标签内的内容必须与用户输入的日期完全一致
3. 如果图片中不存在完全匹配的日期，不输出对应的 <location> 块
4. 所有坐标和尺寸都使用相对值（0-1之间的小数）
   - x: 中心点x坐标 / 图片宽度
   - y: 中心点y坐标 / 图片高度
   - width: 日期文本宽度 / 图片宽度
   - height: 日期文本高度 / 图片高度
5. <x>、<y>、<width>、<height> 标签内的值**有且只能**有一个小数值（0-1之间）
6. 特别注意: 必须对数字特别敏感，不能有任何偏差
7. 用户输入的 query 会进行预处理，请你完整识别在 <date>...</date> 标签内的日期，不能有任何偏差
8. 如果有多个日期，请分别输出每个日期的位置信息
9. 如果日期不存在，不输出对应格式即可

# 举例：
假设图片尺寸为 1000x800，用户查询 2026年1月15日 和 2026年1月14日
- 2026年1月15日 文本中心点在 (500, 400)，宽度200，高度100
- 2026年1月14日 文本中心点在 (300, 300)，宽度100，高度200

user prompt: <date>2026年1月15日</date><date>2026年1月14日</date>
model response:
<location>
    <date>2026年1月15日</date>
    <x>0.5</x>
    <y>0.5</y>
    <width>0.2</width>
    <height>0.125</height>
    <date>2026年1月14日</date>
    <x>0.3</x>
    <y>0.3</y>
    <width>0.25</width>
    <height>0.25</height>
</location>
        """.strip()

        # 将图片编码为 base64
        img_base64 = encode_img_to_base64(img_path)

        # 构建 messages
        messages: List[Dict[str, Any]] = []
        messages.append({"role": "system", "content": system_prompt})
        user_prompt = ""
        for date in dates:
            user_prompt += f"<date>{date}</date>"

        messages.append({
            "role": "user",
            "content": [{
                "type": "image_url",
                "image_url": {
                    "url": img_base64
                },
            }, {
                "type": "text",
                "text": user_prompt
            }]
        })

        # 重试循环
        for attempt in range(1, max_retries + 1):
            logging.info(f"正在尝试 VLM 文本定位（第 {attempt}/{max_retries} 次）...")

            try:
                # 调用 VLM 模型（使用通用 chat_with_vlm 函数，参数来自实例配置）
                full_response = await chat_with_vlm(
                    vlm_client=self.vlm_client,
                    messages=messages,
                    model=model,
                    enable_thinking=enable_thinking,
                    thinking_budget=thinking_budget
                )

                # 解析 XML 格式的位置信息，获取解析状态和结果
                # 从 ChatCompletion 对象中提取文本内容
                response_text = full_response.choices[0].message.content
                success, locations = _parse_xml_locations(response_text)

                if success:
                    # 成功解析（无论找到几个结果，包括0个）
                    if len(locations) == 0:
                        logging.warning("VLM 模型未找到任何匹配的文本")
                    else:
                        logging.info(f"VLM 模型找到了 {len(locations)} 个匹配位置")
                    return locations
                else:
                    # 解析失败（格式错误），需要重试
                    logging.warning(f"第 {attempt} 次尝试解析失败，模型返回的格式不符合要求")
                    if attempt < max_retries:
                        logging.info("准备重试...")

            except Exception as e:
                logging.error(f"第 {attempt} 次尝试时发生异常: {e}")
                if attempt < max_retries:
                    logging.info("准备重试...")
                else:
                    raise ValueError(f"VLM 模型解析失败：在 {max_retries} 次尝试后仍无法成功解析。"
                                     f"请检查图像质量是否清晰，或尝试调整要查找的文本内容。"
                                     f"原始错误: {e}") from e

        # 如果所有重试都失败（解析失败但没有抛出异常）
        raise ValueError(f"VLM 日期定位失败：在 {max_retries} 次尝试后仍无法成功解析位置信息。"
                         f"模型返回的内容不符合预期格式，请检查图像是否包含目标日期 '{dates}'，"
                         f"或尝试使用更清晰的图像。")

    async def _find_articles_positions(
        self,
        screenshot_path: str,
        target_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """使用 VLM 模型识别截图中从某天开始的连续3天的文章位置

        调用 vlm.py 中的 get_dates_location_from_img 函数，
        传入从目标日期开始往前两天的日期文本，返回所有匹配位置的相对坐标列表。

        Args:
            screenshot_path (str): 截图文件路径
            target_date (datetime, optional): 目标日期，默认为当天
                - 如果为None，则使用当天日期
                - 如果为datetime对象，则使用传入的日期
                这个函数会获得从目标日期开始往前两天的日期所有公众号文章的位置

        Returns:
            List[Dict[str, Any]]: 位置列表，每个元素包含:
                - date: 日期内容（近3天日期字符串）
                - x: 中心点相对 x 坐标 (0-1)
                - y: 中心点相对 y 坐标 (0-1)
                - width: 相对宽度 (0-1)
                - height: 相对高度 (0-1)
        """
        # 正确计算近3天日期（使用 timedelta 处理跨月份情况）
        target_date = target_date if target_date else datetime.now()
        second_date = target_date - timedelta(days=1)
        third_date = target_date - timedelta(days=2)

        dates = [
            f"{target_date.year}年{target_date.month}月{target_date.day}日",
            f"{second_date.year}年{second_date.month}月{second_date.day}日",
            f"{third_date.year}年{third_date.month}月{third_date.day}日"
        ]
        logging.info(f"正在识别近3天日期文章位置，日期: {dates}")

        try:
            # 调用类内部方法识别日期位置
            locations = await self._get_dates_location_from_img(
                img_path=screenshot_path,
                dates=dates
            )
            logging.info(f"识别到 {len(locations)} 个近3天日期位置")
            return locations

        except Exception as e:
            logging.warning(f"识别近3天日期位置失败: {e}")
            return []

    async def _check_has_earlier_date(self, locations: List[Dict[str, Any]], target_date: datetime) -> bool:
        """检查从_find_articles_positions方法中识别到的位置中是否存在比目标日期更早的日期，如果存在则返回True，否则返回False

        如果存在比目标日期更早的日期，说明目标日期文章已全部显示。

        Args:
            locations (List[Dict[str, Any]]): 识别到的文章位置列表
            target_date (datetime): 目标日期
        """
        if len(locations) == 0:
            return False

        # 计算比目标日期更早的日期（目标日期的前一天）
        earlier_date = target_date - timedelta(days=1)
        earlier_date_text = f"{earlier_date.year}年{earlier_date.month}月{earlier_date.day}日"

        # 遍历locations，看是否存在比目标日期更早的文章
        for location in locations:
            if location['date'] == earlier_date_text:
                logging.info(
                    f"识别到比目标日期({target_date.strftime('%Y年%m月%d日')})更早的日期: {location['date']}")
                return True

        logging.info(f"未识别到比目标日期({target_date.strftime('%Y年%m月%d日')})更早的日期")
        return False

    # ==================== 文章列表采集主流程方法 ====================

    async def _get_official_account_article_list(
        self,
        output_path: str = "output/articles.md",
        start_index: int = 0,
        target_date: Optional[datetime] = None
    ) -> tuple[List[Dict[str, str]], int]:
        """获取公众号当天文章链接列表（主流程）

        完整流程：
        1. 初始化：获取目标日期文本，创建已采集链接集合
        2. 主循环：
           a. 截取当前页面截图
           b. 使用 VLM 识别目标日期往前（包含当天）的连续3天的文章位置
           c. 遍历每个位置，采集文章链接
           d. 判断是否需要滚动：检查是否有更早日期
           e. 如果达到最大滚动次数或发现更早日期，结束循环
        3. 返回采集结果

        Args:
            output_path (str): 输出文件路径，默认为 "output/articles.md"
            start_index (int): 文章起始序号（默认为0，表示从1开始编号）
            target_date (datetime, optional): 目标日期，默认为当天
                - 如果为None，则使用当天日期
                - 如果为datetime对象，则使用传入的日期
                这个函数会获得从目标日期开始往前（包含当天）的连续3天的所有公众号文章的位置
        Returns:
            tuple[List[Dict[str, str]], int]: 
                - 采集到的文章列表，每个元素包含 {'link': '文章链接'}
                - 更新后的文章序号
        """
        # ==================== 初始化 ====================
        collected_links = set()         # 已采集的文章链接集合（用于去重）
        article_index = start_index     # 文章序号计数器（从传入的起始序号开始）
        scroll_count = 0                # 滚动次数计数器

        target_date = target_date if target_date else datetime.now()

        try:
            # 注意：不再初始化输出文件，因为文件已在外部初始化
            logging.info("=" * 50)
            logging.info("开始采集公众号文章")
            # 获取当天日期（格式示例：2026年1月14日）
            today = datetime.now()
            logging.info(f"当天日期: {today.year}年{today.month}月{today.day}日")
            logging.info(f"输出文件: {output_path}")
            logging.info(f"起始序号: {start_index + 1}")
            logging.info("=" * 50)

            # ==================== 主循环 ====================
            while scroll_count <= self.MAX_SCROLL_TIMES:
                logging.info(f"\n--- 第 {scroll_count + 1} 轮采集 ---")

                # 步骤1: 截取当前页面截图
                screenshot_path = screenshot_current_window(
                    self.TEMP_SCREENSHOT_PATH)

                # 步骤2: 使用 VLM 识别近3天日期的文章位置
                all_positions = await self._find_articles_positions(
                    screenshot_path,
                    target_date=target_date
                )

                # 步骤3: 从所有识别结果中筛选出目标日期的文章位置
                target_date_text = f"{target_date.year}年{target_date.month}月{target_date.day}日"
                target_date_positions = [
                    pos for pos in all_positions if pos['date'] == target_date_text]

                if not target_date_positions:
                    logging.info(
                        f"未识别到 {target_date.year}年{target_date.month}月{target_date.day} 日期的文章")
                    break

                # 步骤4: 只遍历目标日期当天的文章位置，采集文章
                for i, position in enumerate(target_date_positions):
                    logging.info(
                        f"\n处理第 {i + 1}/{len(target_date_positions)} 个文章位置")
                    logging.info(
                        f"VLM识别位置: x={position['x']:.4f}, y={position['y']:.4f}, "
                        f"width={position['width']:.4f}, height={position['height']:.4f}")

                    try:
                        # 4.1 计算更精确的点击位置
                        # VLM返回的x,y是中心点，但有时候识别的边界框不够精确
                        # 我们可以基于边界框的尺寸进行微调，点击更靠近文本实际中心的位置

                        # 策略：如果width和height较大，说明识别区域可能包含了周边元素
                        # 这时可以稍微向右偏移，点击文本本身而不是周边区域
                        click_x = position['x']
                        click_y = position['y']

                        # 如果识别区域的宽度比较大（>0.15），向右偏移一点点
                        # 因为日期文本通常在左侧，可能包含了左侧的空白
                        if position['width'] > 0.15:
                            # 向右偏移 10% 的宽度
                            click_x = position['x'] + position['width'] * 0.1
                            logging.info(
                                f"检测到宽边界框，向右微调: +{position['width']*0.1:.4f}")

                        logging.info(
                            f"最终点击位置: x={click_x:.4f}, y={click_y:.4f}")
                        logging.info("点击进入文章...")
                        click_relative_position(
                            click_x, click_y, self.CLICK_DELAY)

                        # 4.2 等待文章页面加载
                        time.sleep(self.LOAD_DELAY)

                        # 4.3 复制文章链接
                        link = self._copy_article_link()

                        # 4.4 去重检查（利用 set 自动去重）
                        if link in collected_links:
                            logging.info(f"文章链接已存在，跳过: {link[:50]}...")
                        else:
                            # 保存文章链接
                            article_index += 1
                            self._save_article_to_file(
                                link=link,
                                article_index=article_index,
                                output_path=output_path
                            )
                            # 添加到已采集集合
                            collected_links.add(link)
                            logging.info(f"文章 {article_index} 链接采集成功")

                        # 4.5 返回公众号主页
                        self._go_back_to_homepage()

                    except Exception as e:
                        logging.error(f"处理文章时出错: {e}")
                        # 尝试返回主页继续处理下一篇
                        try:
                            self._go_back_to_homepage()
                        except:
                            logging.error("返回主页失败，可能需要手动干预")
                        continue

                # 步骤5: 检查是否需要继续滚动
                # 重新截图并识别是否有更早日期
                if await self._check_has_earlier_date(all_positions, target_date):
                    logging.info(
                        f"已发现比目标日期({target_date.strftime('%Y年%m月%d日')})更早的日期，文章采集完毕")
                    break

                # 步骤6: 向下滚动页面
                scroll_count += 1
                if scroll_count <= self.MAX_SCROLL_TIMES:
                    logging.info(
                        f"向下滚动页面 ({scroll_count}/{self.MAX_SCROLL_TIMES})...")
                    logging.info(f"向下滚动页面，滚动量: {self.SCROLL_AMOUNT}")
                    scroll_down(self.SCROLL_AMOUNT)
                    time.sleep(self.LOAD_DELAY)
                    logging.info("页面滚动完成")
                else:
                    logging.info(f"已达到最大滚动次数 ({self.MAX_SCROLL_TIMES})，停止采集")

            # ==================== 采集完成 ====================
            logging.info("\n" + "=" * 50)
            logging.info("文章链接采集完成")
            logging.info(f"本公众号采集 {len(collected_links)} 篇文章链接")
            logging.info(f"当前累计序号: {article_index}")
            logging.info(f"输出文件: {output_path}")
            logging.info("=" * 50)

            # 将 set 转换为列表格式返回
            collected_articles = [{'link': link} for link in collected_links]
            return collected_articles, article_index

        except Exception as e:
            logging.exception("获取公众号文章链接列表失败")
            raise

    async def build_workflow(self) -> tuple[str, List[Dict[str, Any]]]:
        """构建并执行完整的公众号文章链接采集工作流

        完整流程：
        1. 打开微信应用（如果未运行则启动，如果已运行则激活窗口）
        2. 从配置文件读取并构建公众号URL列表（自动提取biz参数并去重）
        3. 遍历每个公众号URL，依次执行：
           a. 打开微信搜索功能（使用快捷键 ctrl+f 或 cmd+f）
           b. 在搜索框中输入公众号URL并触发搜索
           c. 点击"访问网页"按钮进入公众号主页
           d. 采集目标日期往前（包含当天）的连续3天的所有文章链接（自动识别、点击、复制链接）
              - 使用VLM识别目标日期往前（包含当天）的连续3天的文章位置
              - 自动滚动页面加载更多文章
              - 去重处理，避免重复采集
           e. 关闭当前页面，返回微信主界面，准备处理下一个公众号
        4. 汇总所有采集结果并返回

        所有参数均从配置文件读取：
        - article_urls: 从 config.yaml 的 article_urls 读取
        - target_date: 从 config.yaml 的 target_date 读取

        Returns:
            tuple[str, List[Dict[str, Any]]]: 
                - output_path (str): 输出文件路径，方便后面的工作流获取信息
                - all_results (List[Dict[str, Any]]): 所有公众号的采集结果列表，每个元素包含：
                    - account_url (str): 公众号URL
                    - articles (List[Dict]): 该公众号采集到的文章列表
                        - link (str): 文章链接
                    - count (int): 采集到的文章数量
                    - error (str, 可选): 如果采集失败，包含错误信息

        Raises:
            Exception: 工作流执行过程中的任何严重错误
        """
        # 用于存储所有公众号的采集结果
        all_results = []
        # 全局文章序号计数器（跨公众号累加，实现全局统一编号）
        global_article_index = 0

        try:
            # ==================== 步骤1: 打开微信应用 ====================
            logging.info("=" * 60)
            logging.info("开始执行公众号文章采集工作流")
            logging.info("=" * 60)

            # 等待一段时间，避免 Windows 前台窗口保护机制
            # 用户刚点击"开始"按钮，焦点在浏览器上，Windows 会短暂锁定前台窗口
            # 等待 2 秒让保护机制失效
            logging.info("\n[准备阶段] 等待 2 秒，避免 Windows 前台窗口保护机制...")
            time.sleep(2)
            logging.info("等待完成，准备激活微信窗口")

            logging.info("\n[步骤1] 打开/激活微信应用...")
            self._open_wechat()
            logging.info("微信应用已就绪")

            # ==================== 步骤2: 构建公众号URL列表 ====================
            logging.info("\n[步骤2] 从配置文件构建公众号URL列表...")
            official_account_urls = self._build_official_account_url()
            logging.info(f"成功构建 {len(official_account_urls)} 个公众号URL")

            # 输出所有公众号URL供用户确认
            for i, url in enumerate(official_account_urls, 1):
                logging.info(f"  公众号 {i}: {url[:80]}...")

            # =============== 步骤3: 遍历每个公众号，依次采集文章 ==============
            logging.info("\n[步骤3] 开始遍历公众号列表，依次采集文章...")

            # 从配置读取目标日期（必须为 YYYY-MM-DD 格式）
            target_date_str = self.target_date_config
            if not target_date_str:
                raise ValueError("配置文件中缺少 target_date 参数")

            # YAML 解析器可能会将 YYYY-MM-DD 格式自动转换为 datetime.date 对象
            # 需要统一转换为字符串格式
            if isinstance(target_date_str, datetime):
                target_date_str = target_date_str.strftime("%Y-%m-%d")
            elif hasattr(target_date_str, "strftime"):  # datetime.date 对象
                target_date_str = target_date_str.strftime("%Y-%m-%d")
            elif not isinstance(target_date_str, str):
                raise ValueError(
                    f"target_date 类型错误，必须为字符串或日期类型，当前类型: {type(target_date_str)}")

            # 验证日期格式并解析
            try:
                target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"target_date 格式错误，必须为 YYYY-MM-DD 格式，当前值: {target_date_str}")

            logging.info(f"📅 目标日期: {target_date.strftime('%Y-%m-%d')}")

            # 创建统一的输出文件（所有公众号共享，兼容 PyInstaller 打包）
            timestamp = target_date.strftime("%Y%m%d")
            output_dir = get_output_dir()  # 会自动创建目录
            output_file = str(output_dir / f"articles_{timestamp}.md")
            # 初始化输出文件（写入文件头，符合模板格式）
            self._init_output_file(output_file, target_date)
            logging.info(f"已创建统一输出文件: {output_file}")

            for index, account_url in enumerate(official_account_urls):
                account_url: str = account_url
                logging.info("\n" + "=" * 60)
                logging.info(
                    f"正在处理第 {index}/{len(official_account_urls)} 个公众号")
                logging.info(f"URL: {account_url[:80]}...")
                logging.info("=" * 60)

                try:
                    # --- 3.1 打开微信搜索功能 ---
                    logging.info(f"\n[步骤3.{index}.1] 打开微信搜索功能...")
                    self._open_wechat_search()
                    logging.info("微信搜索界面已打开")

                    # --- 3.2 搜索公众号URL并进入主页 ---
                    logging.info(f"\n[步骤3.{index}.2] 搜索公众号URL并进入主页...")
                    self._search_official_account_url(account_url)
                    logging.info("已成功进入公众号主页")

                    # --- 3.3 采集当天文章链接列表 ---
                    logging.info(f"\n[步骤3.{index}.3] 开始采集当天所有文章链接...")

                    # 调用异步方法采集文章链接列表（使用全局序号，实现跨公众号连续编号）
                    articles, global_article_index = await self._get_official_account_article_list(
                        output_file,
                        start_index=global_article_index,  # 传入当前全局序号，返回更新后的序号
                        target_date=target_date
                    )

                    # 记录采集成功的结果
                    result = {
                        'account_url': account_url,
                        'articles': articles,
                        'count': len(articles),
                        'output_file': output_file
                    }
                    all_results.append(result)

                    logging.info(f"\n公众号 {index} 采集完成！")
                    logging.info(f"  - 文章链接数量: {len(articles)}")

                    # --- 3.4 返回微信主界面，准备处理下一个公众号 ---
                    if index < len(official_account_urls):
                        logging.info(f"\n[步骤3.{index}.4] 关闭当前页面，准备处理下一个公众号...")
                        # 使用快捷键关闭窗口：Windows 用 ctrl+w，Mac 用 cmd+w
                        # 需要按2次：第一次关闭公众号页面，第二次关闭搜索页面
                        if self.os_name == "darwin":
                            # Mac: 使用 cmd+w
                            logging.info("按 cmd+w 关闭窗口...")
                            press_keys("cmd", "w")
                            time.sleep(self.PRESS_DELAY)
                            press_keys("cmd", "w")
                        elif self.os_name == "win32":
                            # Windows: 使用 ctrl+w
                            logging.info("按 ctrl+w 关闭窗口...")
                            press_keys("ctrl", "w")
                            time.sleep(self.PRESS_DELAY)
                            press_keys("ctrl", "w")
                        else:
                            raise OSError(f"不支持的操作系统: {self.os_name}")

                        time.sleep(self.LOAD_DELAY)
                        logging.info("已返回微信主界面")

                except Exception as e:
                    # 单个公众号采集失败不影响其他公众号
                    logging.error(f"\n处理公众号 {index} 时发生错误: {e}")
                    logging.exception("详细错误信息:")

                    # 记录失败结果
                    result = {
                        'account_url': account_url,
                        'articles': [],
                        'count': 0,
                        'error': str(e)
                    }
                    all_results.append(result)

                    # 尝试恢复到微信主界面，避免影响后续公众号处理
                    try:
                        logging.info("尝试恢复到微信主界面...")
                        # 使用快捷键关闭窗口
                        if self.os_name == "darwin":
                            # Mac: 使用 cmd+w
                            press_keys("cmd", "w")
                            time.sleep(self.PRESS_DELAY)
                            press_keys("cmd", "w")
                        elif self.os_name == "win32":
                            # Windows: 使用 ctrl+w
                            press_keys("ctrl", "w")
                            time.sleep(self.PRESS_DELAY)
                            press_keys("ctrl", "w")

                        time.sleep(self.LOAD_DELAY)
                        logging.info("已恢复到微信主界面")
                    except Exception as recovery_error:
                        logging.error(f"恢复失败: {recovery_error}")
                        logging.warning("可能需要手动干预以继续后续采集")

                    # 继续处理下一个公众号
                    continue

            # ==================== 步骤4: 汇总并输出采集结果 ====================
            logging.info("\n" + "=" * 60)
            logging.info("所有公众号采集任务完成")
            logging.info("=" * 60)

            # 统计采集情况
            total_articles = sum(r['count'] for r in all_results)
            success_count = sum(1 for r in all_results if 'error' not in r)
            fail_count = len(official_account_urls) - success_count

            logging.info(f"\n📊 采集统计报告:")
            logging.info(f"  ✅ 公众号总数: {len(official_account_urls)}")
            logging.info(f"  ✅ 成功采集: {success_count}")
            logging.info(f"  ❌ 失败数量: {fail_count}")
            logging.info(f"  📝 文章链接总数: {total_articles}")

            logging.info(f"\n📋 详细结果:")
            for i, result in enumerate(all_results, 1):
                if 'error' in result:
                    logging.info(f"  公众号 {i}: ❌ 失败 - {result['error']}")
                else:
                    logging.info(f"  公众号 {i}: ✅ 成功 - {result['count']} 篇文章链接")

            logging.info(f"\n📁 统一输出文件: {output_file}")
            logging.info("\n" + "=" * 60)

            return output_file, all_results

        except Exception as e:
            logging.exception("工作流执行过程中发生严重错误")
            raise

        finally:
            # 无论成功还是失败，都清理临时文件夹，防止用户隐私信息泄露
            self._cleanup_temp_folder()

    async def run(self) -> str:
        """运行工作流的入口方法（异步接口）

        该方法是工作流的主入口，负责：
        1. 调用异步的 build_workflow 方法
        2. 处理工作流返回的结果
        3. 输出执行摘要

        这是一个异步方法，需要在异步环境中调用（使用 await）。
        如果需要更细粒度的控制，可以直接调用 build_workflow() 方法获取返回结果。

        所有参数均从配置文件读取。

        使用示例：
            collector = RPAArticleCollector()
            await collector.run()  # 异步调用

        Returns:
            str: 输出文件路径，方便后面的工作流获取信息
        """
        try:
            logging.info("启动公众号文章采集器...")

            # 运行异步工作流
            output_path, results = await self.build_workflow()

            # 输出最终结果摘要
            logging.info("\n工作流执行完成")
            logging.info(f"采集了 {len(results)} 个公众号")
            return output_path
        except KeyboardInterrupt:
            logging.warning("\n用户中断了工作流执行")
            raise KeyboardInterrupt("用户中断了工作流执行")
        except Exception as e:
            logging.exception("工作流执行失败")
            raise
