import requests
from typing import Dict, List, Optional
import os
import subprocess
import logging
import time

import ctypes
import ctypes.wintypes
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
                    logging.info("微信窗口已激活到前台")
                else:
                    error_msg = "无法激活微信窗口"
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


"""
微信公众号 API 工具类

提供微信公众号的 API 调用功能，包括：
- access_token 获取和管理
- 草稿箱管理（创建、更新、删除草稿）
- 发布管理（发布草稿、查询发布状态）
- 素材管理（上传图片、视频等素材）

使用示例：
    >>> from wechat_ai_daily.utils.wechat_api import WeChatAPI
    >>> 
    >>> # 初始化 API（从环境变量读取 AppID 和 AppSecret）
    >>> api = WeChatAPI()
    >>> 
    >>> # 创建草稿
    >>> articles = [{
    ...     "title": "文章标题",
    ...     "content": "<p>文章内容HTML</p>",
    ...     "thumb_media_id": "封面图media_id",
    ...     "author": "作者",
    ...     "digest": "摘要"
    ... }]
    >>> result = api.create_draft(articles)
    >>> print(f"草稿 media_id: {result['media_id']}")
    >>> 
    >>> # 发布草稿
    >>> publish_result = api.publish_draft(result['media_id'])
    >>> print(f"发布任务 ID: {publish_result['publish_id']}")

环境变量配置：
    WECHAT_APPID: 公众号 AppID
    WECHAT_APPSECRET: 公众号 AppSecret
    DASHSCOPE_API_KEY: 阿里云 API Key（可选，仅用于 VLM 功能）
"""


logger = logging.getLogger(__name__)


class WeChatAPIError(Exception):
    """微信 API 调用错误"""

    def __init__(self, errcode: int, errmsg: str):
        self.errcode = errcode
        self.errmsg = errmsg
        super().__init__(f"[{errcode}] {errmsg}")


class WeChatAPI:
    """
    微信公众号 API 客户端

    封装了微信公众号常用的 API 接口，包括草稿管理、发布管理、素材管理等。

    Args:
        appid (str): 公众号 AppID
        appsecret (str): 公众号 AppSecret

    Attributes:
        access_token (str): 当前有效的 access_token
        token_expires_at (float): token 过期时间戳
    """

    # API 基础 URL
    BASE_URL = "https://api.weixin.qq.com"

    def __init__(self, appid: Optional[str] = None, appsecret: Optional[str] = None):
        """
        初始化微信 API 客户端

        Args:
            appid: 公众号 AppID，为空时从环境变量 WECHAT_APPID 读取
            appsecret: 公众号 AppSecret，为空时从环境变量 WECHAT_APPSECRET 读取

        Raises:
            ValueError: 未提供 AppID 或 AppSecret 且环境变量未设置时抛出
        """
        self.appid = appid or os.getenv("WECHAT_APPID")
        self.appsecret = appsecret or os.getenv("WECHAT_APPSECRET")

        if not self.appid or not self.appsecret:
            raise ValueError(
                "未找到 AppID 或 AppSecret。\n"
                "请通过参数传入，或设置环境变量 WECHAT_APPID 和 WECHAT_APPSECRET"
            )

        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0

        logger.info(f"微信 API 客户端初始化成功，AppID: {self.appid[:8]}...")

    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        获取 access_token

        access_token 是调用微信 API 的凭证，有效期为 7200 秒（2小时）。
        本方法会自动缓存 token，并在过期前 5 分钟自动刷新。

        Args:
            force_refresh: 是否强制刷新 token（忽略缓存）

        Returns:
            access_token 字符串

        Raises:
            WeChatAPIError: 获取 token 失败时抛出
        """
        # 如果有缓存的 token 且未过期，直接返回
        if not force_refresh and self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        # 请求新的 token
        # 使用稳定版接口，不受 IP 白名单限制
        url = f"{self.BASE_URL}/cgi-bin/stable_token"
        data = {
            "grant_type": "client_credential",
            "appid": self.appid,
            "secret": self.appsecret
        }

        logger.info("正在获取 access_token（使用稳定版接口）...")
        response = requests.post(url, json=data, timeout=10)
        result = response.json()

        # 检查错误
        if "errcode" in result and result["errcode"] != 0:
            raise WeChatAPIError(
                result["errcode"], result.get("errmsg", "未知错误"))

        if "access_token" not in result:
            raise WeChatAPIError(-1, f"获取 access_token 失败，响应: {result}")

        # 缓存 token（提前 5 分钟过期以确保调用时 token 有效）
        self.access_token = result["access_token"]
        expires_in = result.get("expires_in", 7200)
        self.token_expires_at = time.time() + expires_in - 300

        logger.info(f"成功获取 access_token，有效期: {expires_in} 秒")
        return self.access_token

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict:
        """
        发送 HTTP 请求到微信 API

        自动附加 access_token，处理错误响应。

        Args:
            method: HTTP 方法（GET、POST 等）
            path: API 路径（如 /cgi-bin/draft/add）
            params: URL 参数
            json_data: JSON 请求体
            files: 文件上传参数

        Returns:
            API 响应的 JSON 数据

        Raises:
            WeChatAPIError: API 调用失败时抛出
        """
        # 获取 access_token
        access_token = self.get_access_token()

        # 构建完整 URL
        url = f"{self.BASE_URL}{path}"

        # 添加 access_token 到参数
        if params is None:
            params = {}
        params["access_token"] = access_token

        # 发送请求
        logger.debug(f"{method} {path}")
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            files=files,
            timeout=30
        )

        result = response.json()

        # 检查错误码
        errcode = result.get("errcode", 0)
        if errcode != 0:
            errmsg = result.get("errmsg", "未知错误")
            raise WeChatAPIError(errcode, errmsg)

        return result

    # ==================== 草稿管理 ====================

    def create_draft(self, articles: List[Dict]) -> Dict:
        """
        创建草稿

        Args:
            articles: 文章列表，每个文章是一个字典，包含以下字段：
                - title (str): 标题，必填
                - author (str): 作者，选填
                - digest (str): 摘要，选填（不填则自动从正文提取前54字）
                - content (str): 正文内容，HTML 格式，必填
                - content_source_url (str): 原文链接，选填
                - thumb_media_id (str): 封面图片的 media_id，必填
                - need_open_comment (int): 是否打开评论，0不打开，1打开，选填
                - only_fans_can_comment (int): 是否仅粉丝可评论，0所有人，1仅粉丝，选填

        Returns:
            包含 media_id 的字典：{"media_id": "xxx"}

        Raises:
            WeChatAPIError: 创建失败时抛出

        Example:
            >>> api = WeChatAPI()
            >>> articles = [{
            ...     "title": "今日AI资讯",
            ...     "author": "Double童发发",
            ...     "content": "<p>文章内容...</p>",
            ...     "thumb_media_id": "your_media_id"
            ... }]
            >>> result = api.create_draft(articles)
            >>> print(result["media_id"])
        """
        return self._request(
            method="POST",
            path="/cgi-bin/draft/add",
            json_data={"articles": articles}
        )

    def get_draft(self, media_id: str) -> Dict:
        """
        获取草稿详情

        Args:
            media_id: 草稿的 media_id

        Returns:
            草稿详情数据
        """
        return self._request(
            method="POST",
            path="/cgi-bin/draft/get",
            json_data={"media_id": media_id}
        )

    def delete_draft(self, media_id: str) -> Dict:
        """
        删除草稿

        Args:
            media_id: 草稿的 media_id

        Returns:
            删除结果
        """
        return self._request(
            method="POST",
            path="/cgi-bin/draft/delete",
            json_data={"media_id": media_id}
        )

    def update_draft(self, media_id: str, index: int, articles: Dict) -> Dict:
        """
        更新草稿

        Args:
            media_id: 草稿的 media_id
            index: 要更新的文章在图文消息中的位置（多图文时使用），第一篇为 0
            articles: 更新后的文章数据（格式同 create_draft）

        Returns:
            更新结果
        """
        return self._request(
            method="POST",
            path="/cgi-bin/draft/update",
            json_data={
                "media_id": media_id,
                "index": index,
                "articles": articles
            }
        )

    def get_draft_count(self) -> int:
        """
        获取草稿总数

        Returns:
            草稿总数
        """
        result = self._request(
            method="GET",
            path="/cgi-bin/draft/count"
        )
        return result.get("total_count", 0)

    def list_drafts(self, offset: int = 0, count: int = 20) -> Dict:
        """
        获取草稿列表

        Args:
            offset: 偏移量（从第几条开始获取）
            count: 获取数量（最多 20）

        Returns:
            包含草稿列表的字典
        """
        return self._request(
            method="POST",
            path="/cgi-bin/draft/batchget",
            json_data={"offset": offset, "count": count, "no_content": 0}
        )

    # ==================== 发布管理 ====================

    def publish_draft(self, media_id: str) -> Dict:
        """
        发布草稿

        将草稿提交发布到公众号。发布是异步任务，需要通过 get_publish_status 查询状态。

        Args:
            media_id: 草稿的 media_id

        Returns:
            包含 publish_id 的字典：{"publish_id": "xxx", "msg_data_id": "xxx"}

        Example:
            >>> result = api.publish_draft("xxx")
            >>> publish_id = result["publish_id"]
            >>> # 等待几秒后查询状态
            >>> status = api.get_publish_status(publish_id)
        """
        return self._request(
            method="POST",
            path="/cgi-bin/freepublish/submit",
            json_data={"media_id": media_id}
        )

    def get_publish_status(self, publish_id: str) -> Dict:
        """
        查询发布状态

        Args:
            publish_id: 发布任务 ID

        Returns:
            发布状态信息，包含：
            - publish_id: 发布任务 ID
            - publish_status: 发布状态（0发布成功，1发布中，2原创审核中，3原创审核失败，4发布失败）
            - article_id: 当发布成功时，返回图文消息 article_id
            - article_detail: 文章详情
            - fail_idx: 发布失败时的文章索引
        """
        return self._request(
            method="POST",
            path="/cgi-bin/freepublish/get",
            json_data={"publish_id": publish_id}
        )

    def delete_published(self, article_id: str, index: int = 0) -> Dict:
        """
        删除已发布的文章

        注意：此操作不可逆，请谨慎使用。

        Args:
            article_id: 已发布文章的 article_id
            index: 要删除的文章在图文消息中的位置，第一篇为 0

        Returns:
            删除结果
        """
        return self._request(
            method="POST",
            path="/cgi-bin/freepublish/delete",
            json_data={"article_id": article_id, "index": index}
        )

    def list_published(self, offset: int = 0, count: int = 20) -> Dict:
        """
        获取已发布文章列表

        Args:
            offset: 偏移量
            count: 获取数量（最多 20）

        Returns:
            已发布文章列表
        """
        return self._request(
            method="POST",
            path="/cgi-bin/freepublish/batchget",
            json_data={"offset": offset, "count": count, "no_content": 0}
        )

    # ==================== 素材管理 ====================

    def upload_media(self, media_path: str, media_type: str = "image") -> str:
        """
        上传永久素材

        Args:
            media_path: 素材文件路径
            media_type: 素材类型，可选值：image（图片）、voice（语音）、video（视频）、thumb（缩略图）

        Returns:
            media_id 字符串

        Raises:
            WeChatAPIError: 上传失败时抛出

        Example:
            >>> media_id = api.upload_media("cover.jpg", "image")
            >>> print(f"封面图 media_id: {media_id}")
        """
        with open(media_path, "rb") as f:
            files = {"media": (os.path.basename(media_path), f)}
            result = self._request(
                method="POST",
                path="/cgi-bin/material/add_material",
                params={"type": media_type},
                files=files
            )

        logger.info(f"成功上传素材: {result['media_id']}")
        return result["media_id"]

    def upload_image(self, image_path: str) -> str:
        """
        上传图文消息内的图片

        注意：此接口上传的图片不占用公众号的素材库空间，专门用于图文消息正文中的图片。

        Args:
            image_path: 图片文件路径

        Returns:
            图片 URL（可直接用于 <img> 标签的 src 属性）

        Example:
            >>> url = api.upload_image("article_img.jpg")
            >>> html = f'<img src="{url}" />'
        """
        with open(image_path, "rb") as f:
            files = {"media": (os.path.basename(image_path), f)}
            result = self._request(
                method="POST",
                path="/cgi-bin/media/uploadimg",
                files=files
            )

        logger.info(f"成功上传图文消息图片: {result['url']}")
        return result["url"]
