"""
微信相关工具模块

包含：
- 进程管理：检查微信是否运行、激活微信窗口
- PublishClient：微信公众号发布客户端（草稿、发布、素材管理）
- ArticleClient：微信公众号文章获取客户端（基于后台接口）
"""

from .process import is_wechat_running, activate_wechat_window
from .publish_client import PublishClient
from .article_client import ArticleClient
from .html_normalizer import normalize_wechat_html
from .exceptions import WeChatAPIError, PublishError, ArticleError

__all__ = [
    # 进程管理
    "is_wechat_running",
    "activate_wechat_window",

    # 客户端
    "PublishClient",
    "ArticleClient",
    "normalize_wechat_html",

    # 异常
    "WeChatAPIError",
    "PublishError",
    "ArticleError",
]
