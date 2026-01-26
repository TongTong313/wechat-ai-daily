"""
公众号文章列表获取工作流（API版本）

通过微信公众平台后台接口获取指定公众号的文章列表，相比RPA方案：
优势：更高效、更稳定
缺点：需要微信公众号账号，并且需要登录 mp.weixin.qq.com 后台，获取 cookie 和 token

使用前提：
1. 需要有一个微信公众号账号
2. 登录 mp.weixin.qq.com 后台，获取 cookie 和 token
3. 在 config.yaml 完成相关配置

使用示例：
    >>> from wechat_ai_daily.workflows.api_article_collector import APIArticleCollector
    >>>
    >>> # 初始化工作流（从 config.yaml 读取所有配置）
    >>> collector = APIArticleCollector(config="configs/config.yaml")
    >>>
    >>> # 运行工作流（使用配置文件中的所有参数）
    >>> output_file = collector.run()
"""

import logging
import time
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from ruamel.yaml import YAML

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
        config (str, optional): 配置文件路径，默认为 "configs/config.yaml"

    Attributes:
        client (ArticleClient): 文章客户端实例
        account_names (List[str]): 公众号名称列表
    """

    def __init__(self, config: str = "configs/config.yaml") -> None:
        super().__init__()

        # 检查文件是否存在
        if not Path(config).exists():
            raise FileNotFoundError(f"配置文件不存在: {config}")

        # 加载配置文件
        yaml = YAML()
        with open(config, "r", encoding="utf-8") as f:
            self.config = yaml.load(f)

        # 从配置中读取 API 模式专属参数
        cookie = self.config.get("cookie")
        token = self.config.get("token")
        self.account_names = self.config.get("account_names", [])

        if not cookie:
            raise ValueError("配置文件中缺少 cookie 参数")
        if not token:
            raise ValueError("配置文件中缺少 token 参数")
        if not self.account_names:
            raise ValueError("配置文件中缺少 account_names 参数")

        # 初始化 ArticleClient
        self.client = ArticleClient(cookie=cookie, token=str(token))

        logger.info("APIArticleCollector 工作流初始化成功")
        logger.info(
            f"已配置 {len(self.account_names)} 个公众号: {', '.join(self.account_names)}")

    def _search_account(self, account_name: str) -> Optional[AccountMetadata]:
        """
        搜索公众号并返回第一个匹配结果

        Args:
            account_name (str): 公众号名称

        Returns:
            Optional[AccountMetadata]: AccountMetadata 对象，未找到时返回 None
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
            fakeid (str): 公众号唯一标识
            target_date (str): 目标日期，格式 "YYYY-MM-DD"
            account_name (str): 公众号名称（用于日志）

        Returns:
            List[ArticleMetadata]: 文章信息列表
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
        target_date: str
    ) -> str:
        """
        将文章列表保存为 Markdown 文件

        文件格式与 RPAArticleCollector 生成的格式一致，
        便于后续 DailyGenerator 工作流处理。

        Args:
            articles (List[ArticleMetadata]): 文章信息列表
            target_date (str): 目标日期

        Returns:
            str: 输出文件路径
        """
        # 生成输出文件路径
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

    def build_workflow(self) -> str:
        """
        执行完整的文章获取工作流

        工作流步骤：
        1. 遍历公众号名称列表，搜索获取 fakeid
        2. 对每个公众号，获取指定日期的文章列表
        3. 合并所有文章并去重
        4. 保存到 Markdown 文件

        所有参数均从配置文件读取：
        - account_names: 从 config.yaml 的 account_names 读取
        - target_date: 从 config.yaml 的 target_date 读取
        - output_path: 自动生成（output/articles_YYYYMMDD.md）

        Returns:
            str: 输出文件路径
        """
        logger.info("=== 开始公众号文章获取工作流 ===")

        # 从配置读取公众号列表
        account_names = self.account_names

        # 从配置读取目标日期（必须为 YYYY-MM-DD 格式）
        target_date = self.config.get("target_date")
        if not target_date:
            raise ValueError("配置文件中缺少 target_date 参数")

        # 验证日期格式
        try:
            datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"target_date 格式错误，必须为 YYYY-MM-DD 格式，当前值: {target_date}")

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
                target_date=target_date
            )
        else:
            logger.warning("未获取到任何文章，跳过文件保存")
            output_file = ""

        logger.info("=== 公众号文章获取工作流完成 ===")

        return output_file

    def run(self) -> str:
        """
        运行工作流（同步入口）

        所有参数均从配置文件读取。

        Returns:
            str: 输出文件路径
        """
        return self.build_workflow()
