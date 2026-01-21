"""
公众号文章数据类型定义

本模块定义了用于存储和传递公众号文章元数据的数据结构。
使用 Pydantic BaseModel 以便于 JSON 序列化和与大模型框架集成。
"""

from typing import List
from pydantic import BaseModel, Field


class ArticleMetadata(BaseModel):
    """
    公众号文章元数据

    存储从微信公众号文章HTML中提取的所有关键信息，
    用于后续大模型处理生成内容总结和导读。

    Attributes:
        title: 文章标题
        author: 文章作者
        publish_time: 发布时间，格式如 "2026-01-12 10:00"
        article_url: 文章原始链接
        cover_url: 文章封面图片URL
        description: 文章摘要/描述（公众号原始设置的描述）
        account_name: 公众号名称
        account_desc: 公众号简介
        content: 文章正文纯文本内容
        images: 文章中所有图片的URL列表

    Example:
        >>> article = ArticleMetadata(
        ...     title="AI技术突破",
        ...     author="张三",
        ...     publish_time="2026-01-12 10:00",
        ...     article_url="https://mp.weixin.qq.com/s/xxx",
        ...     cover_url="https://mmbiz.qpic.cn/xxx",
        ...     description="本文介绍最新AI技术进展",
        ...     account_name="机器之心",
        ...     account_desc="专业的人工智能媒体",
        ...     content="正文内容...",
        ...     images=["https://mmbiz.qpic.cn/img1", "https://mmbiz.qpic.cn/img2"]
        ... )
        >>> # 转换为字典（用于输入大模型）
        >>> article.model_dump()
        >>> # 转换为JSON字符串
        >>> article.model_dump_json()
    """

    # === 文章基本信息 ===
    title: str = Field(description="文章标题")
    author: str = Field(description="文章作者")
    publish_time: str = Field(description="发布时间，格式如 '2026-01-12 10:00'")
    article_url: str = Field(description="文章原始链接")
    cover_url: str = Field(description="文章封面图片URL")
    description: str = Field(description="文章摘要/描述")

    # === 公众号信息 ===
    account_name: str = Field(description="公众号名称")
    account_desc: str = Field(description="公众号简介")

    # === 正文内容 ===
    content: str = Field(description="文章正文纯文本内容")
    images: List[str] = Field(default_factory=list, description="文章中所有图片URL列表")
