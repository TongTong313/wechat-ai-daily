from typing import List
import requests
import logging


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

    def generate_daily(self) -> None:
        """生成每日内容"""
        pass
