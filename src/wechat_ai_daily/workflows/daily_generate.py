from typing import List


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

    def generate_daily(self) -> None:
        """生成每日内容"""
        pass
