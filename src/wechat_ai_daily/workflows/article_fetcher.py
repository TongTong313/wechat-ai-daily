"""
公众号文章列表获取工作流（API版本）

通过微信公众平台后台接口获取指定公众号的文章列表，相比RPA方案：
优势：更高效、更稳定
缺点：需要手动微信公众号账号，并且需要登录 mp.weixin.qq.com 后台，获取 cookie 和 token

使用前提：
1. 需要有一个微信公众号账号
2. 登录 mp.weixin.qq.com 后台，获取 cookie 和 token

使用示例：
    >>> from wechat_ai_daily.workflows.article_fetcher import ArticleFetcher
    >>>
    >>> # 初始化工作流
    >>> fetcher = ArticleFetcher(
    ...     cookie="your_cookie",
    ...     token="your_token"
    ... )
    >>>
    >>> # 运行工作流，获取指定日期的文章
    >>> fetcher.run(
    ...     account_names=["机器之心", "量子位"],
    ...     target_date="2026-01-25"
    ... )
"""

import logging
import time
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from .base import BaseWorkflow
from ..utils.wechat import ArticleClient, ArticleError
from ..utils.types import ArticleMetadata, AccountMetadata
from ..utils.paths import get_output_dir


logger = logging.getLogger(__name__)


class APIArticleCollector(BaseWorkflow):
    """
    公众号文章列表获取工作流

    通过微信公众平台后台接口获取指定公众号的文章列表。

    Args:
        cookie: 微信公众平台登录 cookie
        token: 微信公众平台登录 token

    Attributes:
        client: ArticleFetchClient 实例
    """

    def __init__(self, cookie: str, token: str) -> None:
        """
        初始化工作流

        Args:
            cookie: 微信公众平台登录 cookie
            token: 微信公众平台登录 token

        Raises:
            ValueError: cookie 或 token 为空时抛出
        """
        super().__init__()

        # 初始化客户端
        self.client = ArticleClient(cookie=cookie, token=token)

        logger.info("ArticleFetcher 工作流初始化成功")

    def _search_account(self, account_name: str) -> Optional[AccountMetadata]:
        """
        搜索公众号并返回第一个匹配结果

        Args:
            account_name: 公众号名称

        Returns:
            AccountMetadata 对象，未找到时返回 None
        """
        try:
            accounts = self.client.search_account(account_name)

            if not accounts:
                logger.warning(f"未找到公众号: {account_name}")
                return None

            # 返回第一个匹配结果
            account = accounts[0]
            logger.info(
                f"找到公众号: {account.nickname} (fakeid: {account.fakeid[:10]}...)")

            return account

        except ArticleError as e:
            logger.error(f"搜索公众号失败: {account_name}, 错误: {e}")
            return None

    def _get_articles_by_date(
        self,
        fakeid: str,
        target_date: str,
        account_name: str
    ) -> List[ArticleMetadata]:
        """
        获取指定日期的文章列表

        Args:
            fakeid: 公众号唯一标识
            target_date: 目标日期，格式 "YYYY-MM-DD"
            account_name: 公众号名称（用于日志）

        Returns:
            文章信息列表
        """
        try:
            articles = self.client.get_articles_by_date(
                fakeid=fakeid,
                target_date=target_date,
                max_pages=20,
                interval=3.0
            )

            logger.info(
                f"公众号 [{account_name}] 在 {target_date} 共有 {len(articles)} 篇文章")

            return articles

        except ArticleError as e:
            logger.error(f"获取文章列表失败: {account_name}, 错误: {e}")
            return []

    def _save_to_markdown(
        self,
        articles: List[ArticleMetadata],
        target_date: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        将文章列表保存为 Markdown 文件

        文件格式与 ArticleCollector 生成的格式一致，
        便于后续 DailyGenerator 工作流处理。

        Args:
            articles: 文章信息列表
            target_date: 目标日期
            output_path: 输出文件路径，为空时自动生成

        Returns:
            输出文件路径
        """
        # 生成输出文件路径
        if output_path is None:
            output_dir = get_output_dir()
            date_str = target_date.replace("-", "")
            output_path = str(output_dir / f"articles_{date_str}.md")

        # 生成 Markdown 内容
        lines = [
            "# 公众号文章链接采集结果",
            f"采集时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
            f"目标日期：{target_date}",
            f"采集方式：微信公众平台后台接口",
            "---",
            ""
        ]

        # 添加文章链接
        for i, article in enumerate(articles, 1):
            lines.append(f"{i}. {article.article_url}")

        # 写入文件
        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"文章链接已保存到: {output_path}")

        return output_path

    def build_workflow(
        self,
        account_names: List[str],
        target_date: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        执行完整的文章获取工作流

        工作流步骤：
        1. 遍历公众号名称列表，搜索获取 fakeid
        2. 对每个公众号，获取指定日期的文章列表
        3. 合并所有文章并去重
        4. 保存到 Markdown 文件

        Args:
            account_names: 公众号名称列表
            target_date: 目标日期，格式 "YYYY-MM-DD"，为空时使用当天日期
            output_path: 输出文件路径，为空时自动生成

        Returns:
            输出文件路径
        """
        logger.info("=== 开始公众号文章获取工作流 ===")

        # 处理目标日期
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"目标日期: {target_date}")
        logger.info(f"待采集公众号: {len(account_names)} 个")

        # 存储所有文章（使用链接去重）
        all_articles: List[ArticleMetadata] = []
        seen_links = set()

        # 遍历公众号
        for i, account_name in enumerate(account_names, 1):
            logger.info(f"正在处理第 {i}/{len(account_names)} 个公众号: {account_name}")

            # 搜索公众号
            account = self._search_account(account_name)
            if account is None:
                continue

            # 获取文章列表
            articles = self._get_articles_by_date(
                fakeid=account.fakeid,
                target_date=target_date,
                account_name=account.nickname
            )

            # 去重并添加到总列表
            for article in articles:
                if article.article_url not in seen_links:
                    seen_links.add(article.article_url)
                    all_articles.append(article)

            # 公众号之间的间隔（避免请求过快）
            if i < len(account_names):
                logger.debug("等待 3 秒后处理下一个公众号...")
                time.sleep(3)

        logger.info(f"采集完成，共获取 {len(all_articles)} 篇文章（已去重）")

        # 保存到文件
        if all_articles:
            output_file = self._save_to_markdown(
                articles=all_articles,
                target_date=target_date,
                output_path=output_path
            )
        else:
            logger.warning("未获取到任何文章，跳过文件保存")
            output_file = ""

        logger.info("=== 公众号文章获取工作流完成 ===")

        return output_file

    def run(
        self,
        account_names: List[str],
        target_date: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        运行工作流（同步入口）

        Args:
            account_names: 公众号名称列表
            target_date: 目标日期，格式 "YYYY-MM-DD"
            output_path: 输出文件路径

        Returns:
            输出文件路径
        """
        return self.build_workflow(
            account_names=account_names,
            target_date=target_date,
            output_path=output_path
        )
