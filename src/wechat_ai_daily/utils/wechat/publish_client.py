"""
微信公众号发布客户端

提供微信公众号的 API 调用功能，包括：
- access_token 获取和管理
- 草稿箱管理（创建、更新、删除草稿）
- 发布管理（发布草稿、查询发布状态）
- 素材管理（上传图片、视频等素材）

使用示例：
    >>> from wechat_ai_daily.utils.wechat import PublishClient
    >>> 
    >>> # 初始化客户端（从环境变量读取 AppID 和 AppSecret）
    >>> client = PublishClient()
    >>> 
    >>> # 创建草稿
    >>> articles = [{
    ...     "title": "文章标题",
    ...     "content": "<p>文章内容HTML</p>",
    ...     "thumb_media_id": "封面图media_id",
    ...     "author": "作者",
    ...     "digest": "摘要"
    ... }]
    >>> result = client.create_draft(articles)
    >>> print(f"草稿 media_id: {result['media_id']}")
    >>> 
    >>> # 发布草稿
    >>> publish_result = client.publish_draft(result['media_id'])
    >>> print(f"发布任务 ID: {publish_result['publish_id']}")

环境变量配置:
    WECHAT_APPID: 公众号 AppID
    WECHAT_APPSECRET: 公众号 AppSecret
"""

import os
import time
import logging
import requests
from typing import Dict, List, Optional

from .base_client import BaseClient
from .exceptions import PublishError


logger = logging.getLogger(__name__)


class PublishClient(BaseClient):
    """
    微信公众号发布客户端

    封装了微信公众号常用的 API 接口，包括草稿管理、发布管理、素材管理等。

    Args:
        appid: 公众号 AppID，为空时从环境变量 WECHAT_APPID 读取
        appsecret: 公众号 AppSecret，为空时从环境变量 WECHAT_APPSECRET 读取

    Attributes:
        access_token: 当前有效的 access_token
        token_expires_at: token 过期时间戳
    """

    # API 基础 URL
    BASE_URL = "https://api.weixin.qq.com"

    def __init__(self, appid: Optional[str] = None, appsecret: Optional[str] = None):
        """
        初始化微信发布客户端

        Args:
            appid: 公众号 AppID，为空时从环境变量 WECHAT_APPID 读取
            appsecret: 公众号 AppSecret，为空时从环境变量 WECHAT_APPSECRET 读取

        Raises:
            ValueError: 未提供 AppID 或 AppSecret 且环境变量未设置时抛出
        """
        super().__init__()
        
        # 确定 AppID 来源
        if appid:
            self.appid = appid
            appid_source = "参数传入"
        elif os.getenv("WECHAT_APPID"):
            self.appid = os.getenv("WECHAT_APPID")
            appid_source = "环境变量"
        else:
            self.appid = None
            appid_source = "未设置"

        # 确定 AppSecret 来源
        if appsecret:
            self.appsecret = appsecret
            appsecret_source = "参数传入"
        elif os.getenv("WECHAT_APPSECRET"):
            self.appsecret = os.getenv("WECHAT_APPSECRET")
            appsecret_source = "环境变量"
        else:
            self.appsecret = None
            appsecret_source = "未设置"

        if not self.appid or not self.appsecret:
            raise ValueError(
                "未找到 AppID 或 AppSecret。\n"
                "请通过参数传入，或设置环境变量 WECHAT_APPID 和 WECHAT_APPSECRET\n"
                "提示：可以在项目根目录创建 .env 文件来配置环境变量（参考 .env.example）"
            )

        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0

        self._log_init_success({
            "AppID": f"{self.appid[:8]}... (来源: {appid_source})",
            "AppSecret": f"******** (来源: {appsecret_source})"
        })

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
            PublishError: 获取 token 失败时抛出
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

        self.logger.info("正在获取 access_token（使用稳定版接口）...")
        response = requests.post(url, json=data, timeout=10)
        result = response.json()

        # 检查错误
        if "errcode" in result and result["errcode"] != 0:
            raise PublishError(
                result["errcode"], result.get("errmsg", "未知错误"))

        if "access_token" not in result:
            raise PublishError(-1, f"获取 access_token 失败，响应: {result}")

        # 缓存 token（提前 5 分钟过期以确保调用时 token 有效）
        self.access_token = result["access_token"]
        expires_in = result.get("expires_in", 7200)
        self.token_expires_at = time.time() + expires_in - 300

        self.logger.info(f"成功获取 access_token，有效期: {expires_in} 秒")
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
            PublishError: API 调用失败时抛出
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
        self.logger.debug(f"{method} {path}")
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
            raise PublishError(errcode, errmsg)

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
            PublishError: 创建失败时抛出

        Example:
            >>> client = PublishClient()
            >>> articles = [{
            ...     "title": "今日AI资讯",
            ...     "author": "Double童发发",
            ...     "content": "<p>文章内容...</p>",
            ...     "thumb_media_id": "your_media_id"
            ... }]
            >>> result = client.create_draft(articles)
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
            >>> result = client.publish_draft("xxx")
            >>> publish_id = result["publish_id"]
            >>> # 等待几秒后查询状态
            >>> status = client.get_publish_status(publish_id)
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
            PublishError: 上传失败时抛出

        Example:
            >>> media_id = client.upload_media("cover.jpg", "image")
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

        self.logger.info(f"成功上传素材: {result['media_id']}")
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
            >>> url = client.upload_image("article_img.jpg")
            >>> html = f'<img src="{url}" />'
        """
        with open(image_path, "rb") as f:
            files = {"media": (os.path.basename(image_path), f)}
            result = self._request(
                method="POST",
                path="/cgi-bin/media/uploadimg",
                files=files
            )

        self.logger.info(f"成功上传图文消息图片: {result['url']}")
        return result["url"]
