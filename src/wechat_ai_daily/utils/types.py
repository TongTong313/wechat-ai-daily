"""
公众号文章数据类型定义

本模块定义了用于存储和传递公众号文章元数据的数据结构。
使用 Pydantic BaseModel 以便于 JSON 序列化和与大模型框架集成。
"""

import time
from typing import List, Optional
from pydantic import BaseModel, Field


class ArticleMetadata(BaseModel):
    """
    公众号文章元数据（支持渐进式填充）

    该类支持分阶段填充数据（仅在后台API接口获取文章信息时涉及，RPA模式不涉及）：
    - 第一阶段（文章列表 API）：填充基础信息（title, article_url, cover_url, digest, publish_time 等）
    - 第二阶段（HTML 解析）：填充详细内容（account_name, content）
    使用场景：
    1. 从微信公众平台 API 获取文章列表时创建初始对象
    2. 获取文章详情 HTML 后，解析并填充 account_name 和 content 字段
    3. 传递给大模型生成摘要和评分

    Attributes:
        title (str): 文章标题
        article_url (str): 文章原始链接
        cover_url (str): 文章封面图片 URL（可能为空）
        digest (str): 文章摘要/描述（微信公众号原始摘要）
        publish_time (str): 发布时间，格式 "YYYY-MM-DD HH:MM" 或 "YYYY-MM-DD HH:MM:SS"
        account_name (str): 公众号名称（第二阶段从 HTML 解析后填充）
        content (str): 文章正文纯文本内容（第二阶段从 HTML 解析后填充）
        create_time (Optional[int]): 创建时间戳（秒），用于精确时间计算
        update_time (Optional[int]): 更新时间戳（秒）
        aid (Optional[str]): 文章 ID（微信内部 ID）
        appmsgid (Optional[int]): 图文消息 ID
        itemidx (Optional[int]): 文章在图文消息中的索引（多图文时使用，单图文为 1）

    """

    # === 核心字段（第一阶段：微信API后端接口获取文章信息时自动填充）===
    title: str = Field(description="文章标题")
    article_url: str = Field(description="文章原始链接")
    cover_url: str = Field(default="", description="文章封面图片 URL")
    digest: str = Field(default="", description="文章摘要/描述（微信公众号原始摘要）")
    publish_time: str = Field(description="发布时间，格式如 '2026-01-12 10:00'")

    # === 详细字段（第二阶段：HTML 解析后自动填充）===
    account_name: str = Field(default="", description="公众号名称（HTML 解析后填充）")
    content: str = Field(default="", description="文章正文纯文本内容（HTML 解析后填充）")

    # === API 原始字段（可选，用于高级场景，RPA模式不涉及）===
    create_time: Optional[int] = Field(default=None, description="创建时间戳（秒）")
    update_time: Optional[int] = Field(default=None, description="更新时间戳（秒）")
    aid: Optional[str] = Field(default=None, description="文章 ID")
    appmsgid: Optional[int] = Field(default=None, description="图文消息 ID")
    itemidx: Optional[int] = Field(default=None, description="文章在图文消息中的索引")

    @property
    def create_time_str(self) -> str:
        """获取格式化的创建时间（如果有时间戳）"""
        if self.create_time:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.create_time))
        return self.publish_time

    @property
    def update_time_str(self) -> str:
        """获取格式化的更新时间（如果有时间戳）"""
        if self.update_time:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.update_time))
        return ""

    @classmethod
    def from_api_response(cls, item: dict) -> "ArticleMetadata":
        """
        从微信公众平台 API 响应创建 ArticleMetadata 对象（第一阶段）

        Args:
            item: API 返回的文章数据字典

        Returns:
            ArticleMetadata 对象（account_name 和 content 为空，等待第二阶段填充）

        Example:
            >>> item = {
            ...     "title": "AI技术突破",
            ...     "link": "https://mp.weixin.qq.com/s/xxx",
            ...     "cover": "https://mmbiz.qpic.cn/xxx",
            ...     "digest": "本文介绍最新AI技术",
            ...     "create_time": 1737878400,
            ...     "update_time": 1737878400,
            ...     "aid": "123456",
            ...     "appmsgid": 100000001,
            ...     "itemidx": 1
            ... }
            >>> article = ArticleMetadata.from_api_response(item)
        """
        create_time = item.get("create_time", 0)
        publish_time = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(create_time))

        return cls(
            title=item.get("title", ""),
            article_url=item.get("link", ""),
            cover_url=item.get("cover", ""),
            digest=item.get("digest", ""),
            publish_time=publish_time,
            account_name="",  # 第一阶段为空，等待 HTML 解析填充
            content="",  # 第一阶段为空，等待 HTML 解析填充
            create_time=create_time,
            update_time=item.get("update_time", 0),
            aid=item.get("aid", ""),
            appmsgid=item.get("appmsgid", 0),
            itemidx=item.get("itemidx", 0)
        )


class AccountMetadata(BaseModel):
    """
    公众号信息元数据

    Attributes:
        fakeid: 公众号唯一标识（用于 API 调用获取文章列表）
        nickname: 公众号名称
        alias: 公众号微信号（可能为空）
        round_head_img: 公众号头像 URL
        service_type: 服务类型（0: 订阅号, 1: 服务号, 2: 企业号）

    Example:
        >>> account = AccountMetadata(
        ...     fakeid="MzI1NjU2MjU2MA==",
        ...     nickname="机器之心",
        ...     alias="almosthuman2014",
        ...     round_head_img="https://mmbiz.qpic.cn/xxx",
        ...     service_type=0
        ... )
    """
    fakeid: str = Field(description="公众号唯一标识（用于 API 调用）")
    nickname: str = Field(description="公众号名称")
    alias: str = Field(default="", description="公众号微信号")
    round_head_img: str = Field(default="", description="公众号头像 URL")
    service_type: int = Field(description="服务类型（0: 订阅号, 1: 服务号, 2: 企业号）")


class ArticleSummary(BaseModel):
    """
    通过大模型对公众号文章进行分析后生成的文章摘要总结信息

    Attributes:
        title: 文章标题
        account_name: 公众号名称
        publish_time: 发布时间，格式如 '2026-01-12 10:00'
        article_url: 文章原始链接
        cover_url: 文章封面图片URL
        keywords: 文章关键词列表（3-5个）
        score: 文章推荐度评分，范围为0-5，0颗星到五颗星，0分表示无价值（包括去重剔除）
        summary: 文章摘要，主要描述文章的主要内容
        reason: 文章推荐理由，包括文章的亮点、文章的不足、文章的改进建议等
    """
    # === 确定性信息（直接从 ArticleMetadata 获取，不通过大模型生成）===
    title: str = Field(description="文章标题")
    account_name: str = Field(description="公众号名称")
    publish_time: str = Field(description="发布时间，格式如 '2026-01-12 10:00'")
    article_url: str = Field(description="文章原始链接")
    cover_url: str = Field(description="文章封面图片URL")

    # === 非确定性信息（通过大模型生成）===
    keywords: List[str] = Field(
        default_factory=list, description="文章关键词列表（3-5个）")
    score: int = Field(
        ge=0, le=5, description="文章推荐度评分，范围为0-5，0颗星到五颗星，0分表示无价值（包括去重剔除）")
    summary: str = Field(description="文章摘要，主要描述文章的主要内容")
    reason: str = Field(description="文章推荐理由，包括文章的亮点、文章的不足、文章的改进建议等")
