"""
微信公众平台文章获取客户端

通过微信公众平台后台接口获取任意公众号的文章列表。

使用前提：
1. 需要有一个微信公众号账号（订阅号或服务号均可）
2. 登录 mp.weixin.qq.com 后台，获取 cookie 和 token

使用示例：
    >>> from wechat_ai_daily.utils.wechat import ArticleClient
    >>>
    >>> # 初始化客户端
    >>> client = ArticleClient(cookie="your_cookie", token="your_token")
    >>>
    >>> # 搜索公众号获取 fakeid
    >>> accounts = client.search_account("机器之心")
    >>> fakeid = accounts[0].fakeid
    >>>
    >>> # 获取文章列表
    >>> articles = client.get_article_list(fakeid, count=10)
    >>> for article in articles:
    ...     print(f"{article.title} - {article.article_url}")

获取 cookie 和 token 的方法：
1. 登录 mp.weixin.qq.com
2. 进入"草稿箱" -> 点击"新建图文" -> 点击"超链接" -> 选择"选择其他公众号"
3. 打开浏览器开发者工具（F12），切换到 Network 标签
4. 在搜索框中搜索任意公众号名称
5. 找到 searchbiz 请求，从请求头中复制 cookie，从 URL 参数中复制 token
"""

import time
import logging
import requests
from typing import Dict, List, Optional

from .base_client import BaseClient
from .exceptions import ArticleError
from ...utils.types import ArticleMetadata, AccountMetadata


logger = logging.getLogger(__name__)


class ArticleClient(BaseClient):
    """
    微信公众平台文章获取客户端

    通过微信公众平台后台接口获取任意公众号的文章列表。

    Args:
        cookie (str): 登录后的 cookie
        token (str): 登录后的 token（从 URL 参数中获取）

    Attributes:
        session (requests.Session): requests 会话对象
    """

    # 微信公众平台基础 URL
    BASE_URL = "https://mp.weixin.qq.com"

    # 默认请求头
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://mp.weixin.qq.com/cgi-bin/appmsg"
    }

    def __init__(self, cookie: str, token: str):
        """
        初始化微信公众号文章获取客户端

        该方法会创建一个 HTTP 会话（Session），并配置好必要的请求头和认证信息，
        用于后续向微信公众平台 API 发送请求，获取文章列表和详情。

        Args:
            cookie (str): 登录微信公众平台后浏览器中的完整 cookie 字符串
                   cookie 包含了登录态信息，用于验证用户身份
                   例如："appmsglist_action_3831653850=card; ..."
            token (str): 微信公众平台的 CSRF Token（防跨站请求伪造令牌）
                  从公众平台页面中提取，通常是一个长字符串
                  例如："1234567890_1234567890"

        Raises:
            ValueError: 当 cookie 或 token 为空时抛出异常
                       这两个参数是必需的，缺一不可
        """
        super().__init__()

        # 参数校验：确保 cookie 和 token 都不为空
        # 这是后续所有 API 请求的必要凭证
        if not cookie or not token:
            raise ValueError("cookie 和 token 不能为空")

        # 保存认证信息到实例变量
        self.cookie = cookie  # 存储 cookie 字符串，用于身份认证
        self.token = token    # 存储 token，用于 CSRF 防护

        # 创建 requests.Session 对象
        # Session 的好处：
        # 1. 自动管理 cookie，保持会话状态
        # 2. 连接复用（TCP keep-alive），提高性能
        # 3. 可以设置全局的请求头，避免每次请求都要设置
        self.session = requests.Session()

        # 设置请求头
        # 1. 先更新默认请求头（User-Agent、Accept 等）
        #    这些请求头模拟浏览器行为，避免被反爬虫机制拦截
        self.session.headers.update(self.DEFAULT_HEADERS)

        # 2. 再设置 Cookie 请求头，覆盖或添加到现有请求头中
        #    Cookie 是身份认证的关键，每次请求都会自动携带
        self.session.headers["Cookie"] = cookie

        # 记录初始化成功日志
        self._log_init_success({
            "Token": f"{token[:10]}..."
        })

    def _request(
        self,
        path: str,
        params: Optional[Dict] = None,
        method: str = "GET"
    ) -> Dict:
        """
        发送请求到微信公众平台

        Args:
            path: API 路径
            params: 请求参数
            method: HTTP 方法

        Returns:
            响应 JSON 数据

        Raises:
            ArticleError: 请求失败时抛出
        """
        url = f"{self.BASE_URL}{path}"

        # 统一添加 token 到所有请求参数中
        # 这是一个关键设计：token 在这里统一添加，而不是在每个业务方法中重复添加
        # 好处：
        # 1. 避免代码重复，每个方法（search_account、get_article_list 等）都不需要手动添加 token
        # 2. 保证所有请求都携带 token，不会遗漏
        # 3. 如果需要修改 token 的处理逻辑，只需在这一个地方修改即可
        if params is None:
            params = {}
        params["token"] = self.token  # 将初始化时保存的 token 添加到请求参数中

        self.logger.debug(f"{method} {path}")

        try:
            if method == "GET":
                response = self.session.get(url, params=params, timeout=30)
            else:
                response = self.session.post(url, data=params, timeout=30)

            result = response.json()

            # 检查微信公众平台 API 返回的业务错误
            # 微信公众平台 API 的响应格式通常为：
            # {
            #     "base_resp": {
            #         "ret": 0,           # 错误码，0 表示成功，非 0 表示失败
            #         "err_msg": "ok"     # 错误信息
            #     },
            #     ... 其他业务数据 ...
            # }

            # 1. 从响应中提取 base_resp 字段，如果不存在则返回空字典 {}
            #    base_resp 是微信公众平台标准的响应结构，包含了请求的执行状态
            base_resp = result.get("base_resp", {})

            # 2. 从 base_resp 中获取错误码 ret
            #    ret = 0 表示请求成功
            #    ret != 0 表示请求失败（例如：权限不足、参数错误、频率限制等）
            #    如果 ret 字段不存在，默认为 0（成功）
            ret = base_resp.get("ret", 0)

            # 3. 判断错误码，如果非 0 则抛出异常
            if ret != 0:
                # 获取详细的错误信息，如果没有则使用默认值"未知错误"
                # 常见错误例如：
                # - 200013: cookie 或 token 无效
                # - 200040: 请求过于频繁，需要降低频率
                # - -1: 系统错误
                errmsg = base_resp.get("err_msg", "未知错误")

                # 抛出自定义异常 ArticleError，包含错误码和错误信息
                # 调用方可以通过捕获此异常来处理不同的错误情况
                raise ArticleError(ret, errmsg)

            return result

        except requests.RequestException as e:
            self.logger.error(f"请求失败: {e}")
            raise ArticleError(-1, str(e))

    def search_account(
        self,
        keyword: str,
        begin: int = 0,
        count: int = 5
    ) -> List[AccountMetadata]:
        """
        搜索公众号

        Args:
            keyword (str): 搜索关键词（公众号名称或微信号）
            begin (int): 起始位置（用于分页）
            count (int): 获取数量（最大 5）

        Returns:
            List[AccountMetadata]: 公众号信息列表

        Example:
            >>> client = ArticleClient(cookie, token)
            >>> accounts = client.search_account("机器之心")
            >>> for acc in accounts:
            ...     print(f"{acc.nickname} - {acc.fakeid}")
        """
        params = {
            "action": "search_biz",
            "begin": begin,
            "count": min(count, 5),  # 最大 5
            "query": keyword,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1"
        }

        result = self._request("/cgi-bin/searchbiz", params)

        accounts = []
        for item in result.get("list", []):
            account = AccountMetadata(
                fakeid=item.get("fakeid", ""),
                nickname=item.get("nickname", ""),
                alias=item.get("alias", ""),
                round_head_img=item.get("round_head_img", ""),
                service_type=item.get("service_type", 0)
            )
            accounts.append(account)

        self.logger.info(f"搜索公众号 '{keyword}'，找到 {len(accounts)} 个结果")

        # 这里返回的是一个列表，列表中每个元素是一个 AccountMetadata 对象
        return accounts

    def get_article_list(
        self,
        fakeid: str,
        begin: int = 0,
        count: int = 10,
        article_type: int = 9
    ) -> List[ArticleMetadata]:
        """
        获取公众号文章列表

        Args:
            fakeid (str): 公众号唯一标识（通过 search_account 获取）
            begin (int): 起始位置（用于分页）
            count (int): 获取数量
            article_type (int): 文章类型（9: 图文消息）

        Returns:
            List[ArticleMetadata]: 文章信息列表（第一阶段数据，account_name 和 content 为空）

        Example:
            >>> articles = client.get_article_list(fakeid, count=10)
            >>> for article in articles:
            ...     print(f"{article.title} - {article.create_time_str}")
        """
        params = {
            "action": "list_ex",
            "begin": begin,
            "count": count,
            "fakeid": fakeid,
            "type": article_type,
            "query": "",
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1"
        }

        result = self._request("/cgi-bin/appmsg", params)

        articles = []
        for item in result.get("app_msg_list", []):
            # 使用工厂方法创建 ArticleMetadata 对象
            article = ArticleMetadata.from_api_response(item)
            articles.append(article)

        self.logger.info(f"获取文章列表，共 {len(articles)} 篇")
        return articles

    def get_articles_by_date(
        self,
        fakeid: str,
        target_date: str,
        max_pages: int = 20,
        interval: float = 3.0
    ) -> List[ArticleMetadata]:
        """
        获取指定日期的文章

        Args:
            fakeid (str): 公众号唯一标识
            target_date (str): 目标日期，格式 "YYYY-MM-DD"
            max_pages (int): 最大翻页数（防止无限循环）
            interval (float): 每次请求间隔（秒）

        Returns:
            List[ArticleMetadata]: 指定日期的文章列表（第一阶段数据，account_name 和 content 为空）

        Example:
            >>> articles = client.get_articles_by_date(fakeid, "2026-01-25")
            >>> for article in articles:
            ...     print(f"{article.title}")
        """
        target_articles = []
        begin = 0
        page_size = 5
        pages = 0

        self.logger.info(f"开始获取 {target_date} 的文章")

        while pages < max_pages:
            articles = self.get_article_list(
                fakeid, begin=begin, count=page_size)

            if not articles:
                break

            for article in articles:
                # 获取文章日期
                article_date = time.strftime(
                    "%Y-%m-%d", time.localtime(article.create_time)
                )

                if article_date == target_date:
                    target_articles.append(article)
                elif article_date < target_date:
                    # 文章日期早于目标日期，停止搜索
                    self.logger.info(f"已到达 {article_date}，停止搜索")
                    return target_articles

            begin += page_size
            pages += 1

            # 频率控制
            if pages < max_pages:
                time.sleep(interval)

        self.logger.info(f"共找到 {len(target_articles)} 篇 {target_date} 的文章")
        return target_articles
