from typing import List, Tuple
from datetime import datetime
import requests
import logging
import re
import html
from bs4 import BeautifulSoup

from ..utils.types import ArticleMetadata


class DailyGenerator:
    """每日日报生成器

    根据公众号文章链接，生成每日AI公众号内容日报，具体Workflow包括：

    1. 读取OfficialAccountArticleCollector采集到的公众号文章链接文件
    2. 获取公众号文章的链接
    3. 通过代码访问公众号链接的网页代码，先使用提取每个公众号文章的摘要内容
    4. 使用LLM综合所有公众号文章的摘要内容，生成每日AI公众号内容日报，这个日报需要符合富文本的要求，可以直接复制粘贴形成我自己的公众号内容
    """

    def __init__(self) -> None:
        """初始化每日生成器"""
        pass

    def _parse_article_urls(self, markdown_file: str) -> List[str]:
        """解析文章链接

        从 OfficialAccountArticleCollector 生成的 markdown 文件中解析文章 URL。
        文件格式为：
            # 公众号文章链接采集结果
            采集时间：xxxx年x月x日
            ---

            1. https://mp.weixin.qq.com/s/xxxxx
            2. https://mp.weixin.qq.com/s/yyyyy
            ...

        Args:
            markdown_file: 公众号文章链接文件路径

        Returns:
            List[str]: 文章链接列表
        """
        import re

        article_urls = []

        # 读取文件内容
        with open(markdown_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 找到 --- 分隔符的位置，只解析其后的内容
        separator_index = content.find("---")
        if separator_index == -1:
            # 如果没有分隔符，返回空列表
            return article_urls

        # 获取分隔符之后的内容
        content_after_separator = content[separator_index + 3:]

        # 使用正则表达式匹配 "序号. URL" 格式的行
        # 匹配格式：数字 + . + 空格 + URL（以 http:// 或 https:// 开头）
        pattern = r'^\d+\.\s+(https?://\S+)$'

        # 逐行匹配
        for line in content_after_separator.strip().split('\n'):
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                url = match.group(1)
                article_urls.append(url)

        return article_urls

    def _get_html_content(self, article_url: str) -> str:
        """获取公众号文章的HTML内容

        Args:
            article_url: 公众号文章链接

        Returns:
            str: 公众号文章的HTML内容

        Raises:
            requests.exceptions.RequestException: 网络请求失败时抛出（连接错误、超时等）
            requests.exceptions.HTTPError: HTTP 状态码为 4xx/5xx 时抛出
        """

        # 设置请求头，模拟浏览器访问
        # 这样做是为了避免被微信服务器识别为爬虫而拒绝访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

        logging.info(f"正在获取文章HTML内容: {article_url}")

        # 发送 GET 请求获取页面内容
        # 网络异常（超时、连接失败等）会自动抛出 RequestException
        response = requests.get(article_url, headers=headers, timeout=15)

        # 检查状态码，4xx/5xx 自动抛出 HTTPError
        response.raise_for_status()

        html_content = response.text
        logging.info(f"成功获取HTML内容，长度: {len(html_content)} 字符")

        return html_content

    def _extract_js_metadata(self, html_content: str) -> dict:
        """从HTML中提取JavaScript变量区的元数据

        从微信公众号文章页面的 JavaScript 代码中提取文章元数据。
        这些变量通常位于页面的 <script> 标签内。

        Args:
            html_content: HTML页面内容

        Returns:
            dict: 包含以下字段的字典
                - title: 文章标题
                - author: 作者
                - publish_timestamp: 发布时间戳
                - cover_url: 封面图片URL
                - description: 文章摘要
                - account_name: 公众号名称
                - account_desc: 公众号简介
        """
        metadata = {
            'title': '',
            'author': '',
            'publish_timestamp': 0,
            'cover_url': '',
            'description': '',
            'account_name': '',
            'account_desc': '',
        }

        # 提取文章标题: var msg_title = '...'.html(false);
        title_match = re.search(
            r"var msg_title = '(.+?)'\.html\(false\)", html_content)
        if title_match:
            metadata['title'] = title_match.group(1)

        # 提取作者: var author = "...";
        author_match = re.search(r'var author = "(.+?)"', html_content)
        if author_match:
            metadata['author'] = author_match.group(1)

        # 提取发布时间戳: var ct = "1768180800";
        ct_match = re.search(r'var ct = "(\d+)"', html_content)
        if ct_match:
            metadata['publish_timestamp'] = int(ct_match.group(1))

        # 提取封面图片URL: var msg_cdn_url = "...";
        cover_match = re.search(r'var msg_cdn_url = "(.+?)"', html_content)
        if cover_match:
            metadata['cover_url'] = cover_match.group(1)

        # 提取文章摘要: var msg_desc = htmlDecode("...");
        # 需要对提取的内容进行 HTML 实体解码
        desc_match = re.search(
            r'var msg_desc = htmlDecode\("(.+?)"\)', html_content)
        if desc_match:
            metadata['description'] = html.unescape(desc_match.group(1))

        # 提取公众号名称: var nickname = htmlDecode("...");
        nickname_match = re.search(
            r'var nickname = htmlDecode\("(.+?)"\)', html_content)
        if nickname_match:
            metadata['account_name'] = html.unescape(nickname_match.group(1))

        # 提取公众号简介: var profile_signature = "...";
        signature_match = re.search(
            r'var profile_signature = "(.+?)"', html_content)
        if signature_match:
            metadata['account_desc'] = signature_match.group(1)

        return metadata

    def _extract_content_and_images(self, html_content: str) -> Tuple[str, List[str]]:
        """从HTML中提取正文内容和图片URL

        使用 BeautifulSoup 解析 HTML，从 #js_content 元素中提取：
        1. 正文纯文本内容（移除 HTML 标签）
        2. 所有图片的 URL 列表

        Args:
            html_content: HTML页面内容

        Returns:
            Tuple[str, List[str]]: (正文纯文本, 图片URL列表)
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # 定位正文内容区域
        js_content = soup.find('div', id='js_content')

        if not js_content:
            logging.warning("未找到 #js_content 元素")
            return '', []

        # 提取所有图片URL
        # 微信公众号图片使用 data-src 属性存储真实URL
        images = []
        for img in js_content.find_all('img'):
            img_url = img.get('data-src') or img.get('src')
            if img_url and img_url.startswith('http'):
                images.append(img_url)

        # 移除 script 和 style 标签，避免提取到代码内容
        for tag in js_content.find_all(['script', 'style']):
            tag.decompose()

        # 提取纯文本内容
        # separator='\n' 保留段落分隔
        # strip=True 移除首尾空白
        content_text = js_content.get_text(separator='\n', strip=True)

        # 清理多余空行（连续多个换行符替换为两个）
        content_text = re.sub(r'\n{3,}', '\n\n', content_text)

        return content_text, images

    def _format_timestamp(self, timestamp: int) -> str:
        """将Unix时间戳转换为可读格式

        Args:
            timestamp: Unix时间戳（秒）

        Returns:
            str: 格式化时间，如 "2026-01-12 09:20"
                 如果时间戳无效，返回 "未知时间"
        """
        if not timestamp or timestamp <= 0:
            return "未知时间"

        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, OSError):
            return "未知时间"

    def extract_article_metadata(self, html_content: str, article_url: str) -> ArticleMetadata:
        """从HTML内容中提取完整的文章元数据

        这是提取文章信息的主入口方法，整合所有提取逻辑。

        Args:
            html_content: HTML页面内容
            article_url: 文章原始URL

        Returns:
            ArticleMetadata: 结构化的文章元数据
        """
        # 1. 提取JS变量区的元数据
        js_meta = self._extract_js_metadata(html_content)

        # 2. 提取正文内容和图片
        content, images = self._extract_content_and_images(html_content)

        # 3. 时间戳转换为可读格式
        publish_time = self._format_timestamp(js_meta['publish_timestamp'])

        # 4. 组装 ArticleMetadata 对象
        return ArticleMetadata(
            title=js_meta['title'],
            author=js_meta['author'],
            publish_time=publish_time,
            article_url=article_url,
            cover_url=js_meta['cover_url'],
            description=js_meta['description'],
            account_name=js_meta['account_name'],
            account_desc=js_meta['account_desc'],
            content=content,
            images=images,
        )

    def extract_articles(self, markdown_file: str) -> List[ArticleMetadata]:
        """批量提取文章元数据

        从采集器生成的 markdown 文件中读取所有文章URL，
        依次获取HTML并提取元数据。单篇文章提取失败会跳过并继续。

        Args:
            markdown_file: 采集器生成的文章链接文件路径

        Returns:
            List[ArticleMetadata]: 成功提取的文章元数据列表
        """
        # 解析URL列表
        urls = self._parse_article_urls(markdown_file)
        logging.info(f"共解析到 {len(urls)} 个文章链接")

        articles = []
        for i, url in enumerate(urls, 1):
            logging.info(f"正在处理第 {i}/{len(urls)} 篇文章: {url}")
            try:
                # 获取HTML内容
                html_content = self._get_html_content(url)

                # 提取元数据
                metadata = self.extract_article_metadata(html_content, url)
                articles.append(metadata)

                logging.info(f"成功提取: {metadata.title}")

            except Exception as e:
                logging.error(f"提取文章失败，跳过: {url}, 错误: {e}")
                continue

        logging.info(f"提取完成，成功 {len(articles)}/{len(urls)} 篇")
        return articles

    def generate_daily(self) -> None:
        """生成每日内容"""
        pass
