# 每日公众号日报生成器

from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
import requests
import logging
import re
import html
import asyncio
import os
from ruamel.yaml import YAML
from openai import AsyncOpenAI
from bs4 import BeautifulSoup
from pydantic import ValidationError
import json
from datetime import datetime
from pathlib import Path

from .base import BaseWorkflow
from ..utils.llm import chat_with_llm, extract_json_from_response
from ..utils.types import ArticleMetadata, ArticleSummary
from ..utils.paths import get_output_dir, get_templates_dir


class DailyGenerator(BaseWorkflow):
    """每日日报生成器

    根据公众号文章链接，生成每日AI公众号内容日报，具体Workflow包括：

    1. 读取ArticleCollector采集到的公众号文章链接文件
    2. 获取公众号文章的链接
    3. 通过代码访问公众号链接的网页代码，先使用提取每个公众号文章的摘要内容
    4. 使用LLM综合所有公众号文章的摘要内容，生成每日AI公众号内容日报，这个日报需要符合富文本的要求，可以直接复制粘贴形成我自己的公众号内容
    """

    def __init__(self,
                 config: str = "configs/config.yaml",
                 llm_client: Optional[AsyncOpenAI] = None,
                 max_retries: int = 2) -> None:
        """初始化每日生成器

        Args:
            config: 配置文件路径，默认为 "configs/config.yaml"
            llm_client: LLM 客户端，如果不提供则使用默认配置创建
            max_retries: 最大重试次数，默认为 2
        """
        # 读取配置文件
        yaml = YAML()
        with open(config, "r", encoding="utf-8") as f:
            self.config = yaml.load(f)

        # 如果未提供 LLM 客户端，使用默认配置创建（需要设置 DASHSCOPE_API_KEY 环境变量）
        if llm_client is None:
            self.llm_client = AsyncOpenAI(
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        else:
            self.llm_client = llm_client

        self.max_retries = max_retries

        # 富文本模板缓存（延迟加载）
        self._rich_text_templates: Optional[Dict[str, str]] = None

    def _load_rich_text_templates(self) -> Dict[str, str]:
        """加载富文本 HTML 模板

        从 templates/rich_text_template.html 文件中解析出各个模板片段。
        模板使用特殊注释标记分隔：<!-- ===== XXX_START ===== --> 和 <!-- ===== XXX_END ===== -->

        Returns:
            Dict[str, str]: 包含以下 key 的字典：
                - header: HTML 文档头 + 外层容器开始
                - article_card: 单篇文章卡片模板（含占位符）
                - separator: 文章之间的过渡装饰
                - footer: 底部 + 外层容器结束
        """
        # 定位模板文件路径（使用路径工具，兼容 PyInstaller 打包）
        template_path = get_templates_dir() / "rich_text_template.html"

        # 读取模板文件
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        templates = {}

        # 解析各个模板片段
        # 使用正则表达式提取标记之间的内容
        patterns = {
            "header": r"<!-- ===== HEADER_START ===== -->(.*?)<!-- ===== HEADER_END ===== -->",
            "article_card": r"<!-- ===== ARTICLE_CARD_START ===== -->(.*?)<!-- ===== ARTICLE_CARD_END ===== -->",
            "separator": r"<!-- ===== SEPARATOR_START ===== -->(.*?)<!-- ===== SEPARATOR_END ===== -->",
            "footer": r"<!-- ===== FOOTER_START ===== -->(.*?)<!-- ===== FOOTER_END ===== -->",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL)
            if match:
                # 去除首尾空白，但保留内部格式
                templates[key] = match.group(1).strip()
            else:
                logging.warning(f"未找到模板片段: {key}")
                templates[key] = ""

        return templates

    def _get_rich_text_templates(self) -> Dict[str, str]:
        """获取富文本模板（带缓存）

        Returns:
            Dict[str, str]: 模板字典
        """
        if self._rich_text_templates is None:
            self._rich_text_templates = self._load_rich_text_templates()
        return self._rich_text_templates

    def _parse_article_urls(self, markdown_file: str) -> List[str]:
        """解析文章链接

        从 ArticleCollector 生成的 markdown 文件中解析文章 URL。
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

    def _extract_js_metadata(self, html_content: str) -> Dict[str, Any]:
        """从HTML中提取JavaScript变量区的元数据

        从微信公众号文章页面的 JavaScript 代码中提取文章元数据。
        这些变量通常位于页面的 <script> 标签内。

        Args:
            html_content: HTML页面内容

        Returns:
            Dict[str, Any]: 包含以下字段的字典
                - title: 文章标题
                - author: 作者
                - publish_timestamp: 发布时间戳
                - cover_url: 封面图片URL
                - description: 文章摘要
                - account_name: 公众号名称
        """
        metadata = {
            'title': '',
            'author': '',
            'publish_timestamp': 0,
            'cover_url': '',
            'description': '',
            'account_name': '',
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

    def _extract_article_metadata(self, html_content: str, article_url: str) -> ArticleMetadata:
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
            content=content,
            images=images,
        )

    def _replace_quotes_with_chinese(self, text: str) -> str:
        """智能替换英文引号为中文左右引号

        根据引号的配对状态判断是左引号还是右引号：
        - 第1、3、5... 次出现的引号替换为左引号（" 或 '）
        - 第2、4、6... 次出现的引号替换为右引号（" 或 '）

        Args:
            text (str): 原始文本

        Returns:
            str: 替换后的文本
        """
        result = []
        double_quote_open = False  # 双引号状态：False=下一个是左引号，True=下一个是右引号
        single_quote_open = False  # 单引号状态：False=下一个是左引号，True=下一个是右引号

        for char in text:
            if char == '"':
                if double_quote_open:
                    result.append('"')  # 右双引号
                    double_quote_open = False
                else:
                    result.append('"')  # 左双引号
                    double_quote_open = True
            elif char == "'":
                if single_quote_open:
                    result.append(''')  # 右单引号
                    single_quote_open = False
                else:
                    result.append(''')  # 左单引号
                    single_quote_open = True
            else:
                result.append(char)

        return ''.join(result)

    def _sanitize_llm_summary_output(self, text: str) -> str:
        """清理和规范化 LLM 输出的内容速览（允许 <strong> 标签）

        处理以下问题：
        1. 替换英文标点为中文标点
        2. 移除 Markdown 格式标记
        3. 移除非 strong 的 HTML 标签
        4. 保留 <strong> 标签用于关键词标记
        5. 转义花括号防止 str.format() 报错

        Args:
            text (str): 原始文本

        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""

        # 1. 智能替换英文引号为中文左右引号
        text = self._replace_quotes_with_chinese(text)

        # 替换其他英文标点为中文标点
        replacements = {
            ',': '，',  # 逗号
            ':': '：',  # 冒号
            ';': '；',  # 分号
            '!': '！',  # 感叹号
            '?': '？',  # 问号
            '(': '（',  # 左括号
            ')': '）',  # 右括号
        }

        for en_punct, zh_punct in replacements.items():
            text = text.replace(en_punct, zh_punct)

        # 2. 移除 Markdown 加粗标记 **xxx**
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)

        # 3. 移除 HTML 标签（保守策略：只移除常见格式标签，但保留 strong）
        html_tags = ['b', 'em', 'i', 'u', 'span', 'div', 'p']
        for tag in html_tags:
            text = re.sub(f'<{tag}[^>]*>', '', text)
            text = re.sub(f'</{tag}>', '', text)

        # 4. 转义花括号（防止 format() 报错）
        text = text.replace('{', '{{').replace('}', '}}')

        # 5. 清理多余空白字符
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _sanitize_llm_reason_output(self, text: str) -> str:
        """清理和规范化 LLM 输出的精选理由（移除所有 HTML 标签）

        处理以下问题：
        1. 替换英文标点为中文标点
        2. 移除 Markdown 格式标记
        3. 移除所有 HTML 标签
        4. 转义花括号防止 str.format() 报错

        Args:
            text (str): 原始文本

        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""

        # 1. 智能替换英文引号为中文左右引号
        text = self._replace_quotes_with_chinese(text)

        # 替换其他英文标点为中文标点
        replacements = {
            ',': '，',  # 逗号
            ':': '：',  # 冒号
            ';': '；',  # 分号
            '!': '！',  # 感叹号
            '?': '？',  # 问号
            '(': '（',  # 左括号
            ')': '）',  # 右括号
        }

        for en_punct, zh_punct in replacements.items():
            text = text.replace(en_punct, zh_punct)

        # 2. 移除 Markdown 加粗标记 **xxx**
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)

        # 3. 移除所有 HTML 标签
        html_tags = ['strong', 'b', 'em', 'i', 'u', 'span', 'div', 'p']
        for tag in html_tags:
            text = re.sub(f'<{tag}[^>]*>', '', text)
            text = re.sub(f'</{tag}>', '', text)

        # 4. 转义花括号（防止 format() 报错）
        text = text.replace('{', '{{').replace('}', '}}')

        # 5. 清理多余空白字符
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    async def _generate_one_article_summary(self, article_metadata: ArticleMetadata) -> Optional[ArticleSummary]:
        """为单篇文章生成摘要

        根据文章元数据，使用大模型生成文章摘要总结信息，给出文章推荐度评分，并给出推荐理由。
        重试机制会保持完整的对话上下文，让模型基于之前的对话修正输出。

        Args:
            article_metadata (ArticleMetadata): 文章元数据
        Returns:
            ArticleSummary: 文章摘要对象，如果生成失败返回 None
        """
        try:
            logging.info(f"正在为文章生成摘要: {article_metadata.title}")

            SYSTEM_PROMPT = """
# 角色与任务要求
你是每日AI公众号内容推荐助手，你的任务是：根据公众号文章元数据，生成文章摘要、推荐度评分和推荐理由，你评分较高的文章我会形成每日AI公众号内容日报，推荐给用户。

# 具体要求

## 生成内容要求
1. 内容速览尽量控制在200字以内，但也不要少于100字，简明扼要的阐述公众号文章主要内容是什么，比如说了一个什么样的技术、应用、故事或者观点等
2. 关键词列表（3-5个），关键词要能够准确反映文章的核心主旨、核心技术、核心应用、核心观点等，关键词要使用中文，但不要包含人工智能或者AI关键词，因为所有的文章本身就是AI相关的了。
3. 文章推荐度评分范围为0-5，分别代表零颗星到五颗星，五颗星为强烈推荐，四颗星为推荐，三颗星为一般推荐，两颗星为不推荐，一颗星非常不推荐但凑合能看，零颗星不仅非常不推荐且没有任何价值。
4. 精选理由主要阐明读了这个文章以后能得到什么样的收获和启发？文章的价值在哪里等，字数限制100字以内。
5. 请使用中文回复，并**严格使用中文标点符号**（尤其是**中文引号**！！！中文基本不会用单引号，全都用双引号即可）。**在内容速览中可以使用 <strong>关键词</strong> 标记重要词汇**，但精选理由中不要使用任何格式化标记，输出纯文本内容即可。

## 评分规则
1. 你的评分要尽可能严格，不允许无脑随便打五颗星，五颗星必须给出充分的理由！我们要推荐最优质的文章给用户，不要因为文章质量不高而推荐给用户，宁缺毋滥！
2. 好的文章不能出现明显的AI生成的痕迹，如果你发现这个文章有疑似AI生成的嫌疑，则最高只能打三颗星。
3. 文章的主题必须适合AI相关的技术、产品、前沿动态，一些广告、招聘等内容不在推荐范围内，遇到这种内容直接给零颗星。
4. 文章要求务实，过分吹牛的文章不能给到很高的分数，建议最多给三颗星。
5. 好文章的标准（满足其一即可），这些文章建议给相对较高的分数：
- 文章能够反映当前最前沿的技术，介绍有一定深度
- 文章能够帮助阅读者解决一个或多个实际应用场景的问题
- 文章具有一定的趣味性，能够吸引阅读者的兴趣
- 文章反映了一种新型的产品形态，能够给读者较大启发


# 输出格式
要求通过json格式输出，格式如下：
```json
{
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "score": 整数型分数值(0-5),
    "summary": "内容速览（100字以上，200字以内，可使用<strong>标签标记关键词）",
    "reason": "精选理由（100字以内，纯文本）"
}
```
"""

            USER_PROMPT = f"""
    文章元数据: {article_metadata}
    """

            # 初始化对话消息列表
            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT}
            ]

            # 获取LLM模型配置
            model = self.config.get("model_config", {}).get(
                "LLM", {}).get("model", "qwen-plus")
            enable_thinking = self.config.get("model_config", {}).get(
                "LLM", {}).get("enable_thinking", True)
            thinking_budget = self.config.get("model_config", {}).get(
                "LLM", {}).get("thinking_budget", 1024)

            # 首次调用大模型
            response = await chat_with_llm(
                llm_client=self.llm_client,
                messages=messages,
                model=model,
                enable_thinking=enable_thinking,
                thinking_budget=thinking_budget
            )
            raw_content = response.choices[0].message.content

            # 尝试解析
            try:
                json_str = extract_json_from_response(raw_content)
                # 将 JSON 字符串解析为 Python 字典
                llm_output = json.loads(json_str)

                summary = ArticleSummary(
                    # 确定性信息：直接从元数据获取
                    title=article_metadata.title,
                    account_name=article_metadata.account_name,
                    publish_time=article_metadata.publish_time,
                    article_url=article_metadata.article_url,
                    cover_url=article_metadata.cover_url,

                    # 不确定性信息：从大模型输出获取（需清理）
                    keywords=llm_output.get('keywords', []),
                    score=llm_output['score'],
                    summary=self._sanitize_llm_summary_output(
                        llm_output['summary']),
                    reason=self._sanitize_llm_reason_output(
                        llm_output['reason'])
                )
                logging.info(
                    f"文章摘要生成成功: {article_metadata.title}, 评分: {summary.score}")
                return summary
            except (ValidationError, json.JSONDecodeError) as e:
                logging.warning(f"解析 JSON 失败: {e}")
                last_error = str(e)

            # 解析失败，进入重试循环（保持对话上下文）
            for attempt in range(self.max_retries):
                logging.info(
                    f"尝试让大模型修正 JSON 格式 (第 {attempt + 1}/{self.max_retries} 次)")

                # 将模型之前的输出追加到对话历史
                messages.append({"role": "assistant", "content": raw_content})

                # 追加修正请求
                fix_prompt = f"""
    你的输出格式有误，无法解析为有效的 JSON。

    错误信息: {last_error}

    请重新输出，严格按照要求的 JSON 格式，不要添加任何额外文字或 markdown 代码块标记。
    """
                messages.append({"role": "user", "content": fix_prompt})

                try:
                    # 带上下文重新调用大模型
                    response = await chat_with_llm(
                        llm_client=self.llm_client,
                        messages=messages,
                        model=model,
                        enable_thinking=enable_thinking,
                        thinking_budget=thinking_budget
                    )
                    raw_content = response.choices[0].message.content

                    # 尝试解析修正后的输出
                    json_str = extract_json_from_response(raw_content)
                    # 将 JSON 字符串解析为 Python 字典
                    llm_output = json.loads(json_str)

                    # 手动构造 ArticleSummary 对象
                    summary = ArticleSummary(
                        # 确定性信息：直接从元数据获取
                        title=article_metadata.title,
                        account_name=article_metadata.account_name,
                        publish_time=article_metadata.publish_time,
                        article_url=article_metadata.article_url,
                        cover_url=article_metadata.cover_url,

                        # 不确定性信息：从大模型输出获取（需清理）
                        keywords=llm_output.get('keywords', []),
                        score=llm_output['score'],
                        summary=self._sanitize_llm_summary_output(
                            llm_output['summary']),
                        reason=self._sanitize_llm_reason_output(
                            llm_output['reason'])
                    )
                    logging.info(
                        f"文章摘要生成成功: {article_metadata.title}, 评分: {summary.score}")
                    return summary

                except (ValidationError, json.JSONDecodeError) as e:
                    logging.warning(f"第 {attempt + 1} 次修正后仍解析失败: {e}")
                    last_error = str(e)
                except Exception as e:
                    logging.error(f"调用大模型修正时发生异常: {e}")
                    break

            # 所有重试都失败
            logging.error(f"JSON 解析最终失败，已重试 {self.max_retries} 次")
            return None

        except Exception as e:
            logging.error(f"生成文章摘要失败: {article_metadata.title}, 错误: {e}")
            return None

    async def _result_optimize(self, high_score_summaries: List[ArticleSummary]) -> List[ArticleSummary]:
        """对高分文章（≥3星）进行去重优化

        通过大模型识别相似主题的文章，每组只保留评分最高（或时间最早）的一篇，
        其他文章的 score 修改为 0（标记为无价值/去重剔除）。

        注意：此函数接收的是已经筛选过的高分文章列表（由调用方筛选），
             不会在函数内部再次进行 score >= 3 的筛选。

        Args:
            high_score_summaries: 高分文章摘要列表（score >= 3）

        Returns:
            List[ArticleSummary]: 优化后的文章摘要列表（相似文章已降分为0）
        """
        try:
            logging.info("开始对高分文章进行去重优化")

            # 如果高分文章少于2篇，无需去重
            if len(high_score_summaries) < 2:
                logging.info(
                    f"高分文章数量为 {len(high_score_summaries)}，无需去重")
                return high_score_summaries

            logging.info(
                f"当前有 {len(high_score_summaries)} 篇高分文章，正在进行去重分析")

            # 1. 构造输入数据（只包含必要字段）
            articles_data = [
                {
                    "title": s.title,
                    "keywords": s.keywords,
                    "summary": s.summary,
                    "score": s.score,
                    "publish_time": s.publish_time
                }
                for s in high_score_summaries
            ]

            # 2. 调用大模型进行去重分析
            removed_titles = await self._call_llm_for_deduplication(articles_data)

            # 3. 根据返回的 title 列表，修改对应文章的 score
            if not removed_titles:
                logging.info("未发现需要剔除的重复文章")
                return high_score_summaries

            logging.info(f"识别出 {len(removed_titles)} 篇需要剔除的重复文章")

            # 创建新列表（使用 model_copy 避免修改原对象）
            optimized_summaries = []
            for summary in high_score_summaries:
                if summary.title in removed_titles:
                    # 降分为 0（标记为无价值/去重剔除）
                    new_summary = summary.model_copy(update={"score": 0})
                    logging.info(
                        f"  - 文章已降分: {summary.title} ({summary.score}星 -> 0星(去重剔除))")
                    optimized_summaries.append(new_summary)
                else:
                    optimized_summaries.append(summary)

            logging.info("去重优化完成")
            return optimized_summaries

        except Exception as e:
            logging.error(f"去重优化过程中发生异常: {e}")
            logging.warning("返回原始列表（未进行去重优化）")
            return high_score_summaries

    async def _call_llm_for_deduplication(self, articles_data: List[Dict[str, Any]]) -> List[str]:
        """调用大模型进行去重分析

        Args:
            articles_data: 高分文章数据列表（包含 title、keywords、summary、score、publish_time）

        Returns:
            需要剔除的文章 title 列表
        """
        # 获取模型配置
        model = self.config.get('model_config', {}).get(
            'LLM', {}).get('model', 'qwen-plus')
        enable_thinking = self.config.get('model_config', {}).get(
            'LLM', {}).get('enable_thinking', True)
        thinking_budget = self.config.get('model_config', {}).get(
            'LLM', {}).get('thinking_budget', 1024)

        # 构造系统提示词
        SYSTEM_PROMPT = """
你是每日AI公众号摘要内容去重助手。你的任务是：识别主题相似或重复的文章，并给出需要剔除的文章列表。

# 背景说明
用户提供了一批已经评分为三星及以上的公众号文章摘要。这些文章可能存在主题重复的情况（例如多篇文章都报道了同一个AI产品发布、同一个技术突破等）。为了给读者提供更丰富多样的内容，我们需要对相似主题的文章进行去重。

# 相似主题的判断标准
以下情况视为"相似主题"或"重复内容"：
1. **同一事件报道**：多篇文章报道同一个新闻事件、产品发布、技术突破等
2. **同一技术/产品介绍**：多篇文章介绍同一个AI模型、工具、应用等
3. **同一观点论述**：多篇文章表达相同或相似的核心观点
4. **核心关键词高度重合**：虽然表述不同，但核心主题一致（例如都在讲"GPT-5"、"文生视频"等）

注意：以下情况**不算**相似主题：
- 同一大领域但不同细分方向（例如"图像生成"和"视频生成"）
- 同一技术的不同应用场景（例如"ChatGPT在教育"和"ChatGPT在医疗"）
- 不同角度的分析（例如"技术解析"和"商业分析"）

# 去重规则
当识别出相似主题的文章组时，按以下规则保留一篇：
1. **优先保留评分更高的**（score 更高）
2. **评分相同时保留发布时间更早的**（publish_time 更早）
3. **其他同组文章全部标记为需要剔除**

# 输出要求
只输出**需要剔除的文章标题列表**，使用以下 JSON 格式：

```json
{
    "removed_titles": [
        "需要剔除的文章1标题",
        "需要剔除的文章2标题"
    ],
    "reason": "简要说明去重理由，例如：'文章A、B都报道了OpenAI发布GPT-5这一事件，保留了评分更高的文章A'"
}
```

**特别注意**：
- 如果没有发现相似主题的文章，返回：`{"removed_titles": [], "reason": "未发现主题重复的文章"}`
- 不要修改原文章的任何信息，只返回需要剔除的 title 列表
- removed_titles 必须是数组格式，即使为空也要返回 []
- reason 字段用于记录日志，便于调试和审核

"""

        # 构造用户提示词
        articles_json = json.dumps(articles_data, ensure_ascii=False, indent=2)
        user_prompt = f"""
请分析以下三星及以上评分的文章列表，识别相似主题并给出需要剔除的文章：

{articles_json}

请严格按照 JSON 格式输出结果。
"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        # 调用大模型（带重试机制）
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                logging.info(
                    f"调用大模型进行去重分析 (第 {attempt + 1}/{self.max_retries + 1} 次)")

                response = await chat_with_llm(
                    llm_client=self.llm_client,
                    messages=messages,
                    model=model,
                    enable_thinking=enable_thinking,
                    thinking_budget=thinking_budget
                )

                raw_content = response.choices[0].message.content

                # 解析 JSON 输出
                json_str = extract_json_from_response(raw_content)
                result = json.loads(json_str)

                # 验证输出格式
                if "removed_titles" not in result:
                    raise ValueError("输出格式错误：缺少 removed_titles 字段")

                if not isinstance(result["removed_titles"], list):
                    raise ValueError("输出格式错误：removed_titles 必须是数组")

                removed_titles = result["removed_titles"]
                reason = result.get("reason", "未提供理由")

                logging.info(f"去重分析完成")
                logging.info(f"去重理由: {reason}")
                if removed_titles:
                    logging.info(f"需要剔除的文章:")
                    for title in removed_titles:
                        logging.info(f"  - {title}")
                else:
                    logging.info("没有发现需要剔除的文章")

                return removed_titles

            except (json.JSONDecodeError, ValueError) as e:
                logging.warning(f"解析大模型输出失败 (第 {attempt + 1} 次): {e}")
                last_error = str(e)

                if attempt < self.max_retries:
                    # 追加错误信息，让大模型重新输出
                    messages.append(
                        {"role": "assistant", "content": raw_content})
                    messages.append({
                        "role": "user",
                        "content": f"输出格式有误，错误信息: {last_error}\n\n请严格按照要求的 JSON 格式重新输出。"
                    })
                else:
                    logging.error(f"去重分析最终失败，已重试 {self.max_retries} 次")
                    return []  # 返回空列表，不进行去重

            except Exception as e:
                logging.error(f"调用大模型时发生异常: {e}")
                return []

        return []

    def _generate_stars_html(self, score: int) -> str:
        """生成星星评级的 HTML 字符串

        Args:
            score(int): 评分（0-5）

        Returns:
            str: 星星 HTML 字符串
        """
        filled_star = '<span style="color: #FFD700; font-size: 14px;">★</span>'  # 实心星（金色）
        empty_star = '<span style="color: #D3D3D3; font-size: 14px;">☆</span>'   # 空心星（灰色）

        # 生成星星
        stars = filled_star * score + empty_star * (5 - score)

        return stars

    def _generate_rich_text_content(self, article_summary: ArticleSummary) -> str:
        """将 ArticleSummary 对象转换为富文本 HTML 卡片

        使用预定义的 HTML 模板进行填充，不调用 LLM，确保输出稳定且速度快。

        Args:
            article_summary: ArticleSummary 对象

        Returns:
            str: 单篇文章的 HTML 卡片内容
        """
        # 获取模板
        templates = self._get_rich_text_templates()
        article_card_template = templates.get("article_card", "")

        if not article_card_template:
            logging.error("未找到文章卡片模板")
            return ""

        # 处理关键词列表，转换为 HTML 标签字符串
        keywords_html = ""
        if article_summary.keywords:
            keyword_tags = []
            for keyword in article_summary.keywords:
                # 转义花括号防止 format() 报错
                keyword_escaped = keyword.replace('{', '{{').replace('}', '}}')
                keyword_tag = f'<span style="display: inline-block; padding: 3px 10px; background-color: rgba(7, 193, 96, 0.08); color: #07c160; font-size: 12px; border-radius: 12px; border: 1px solid rgba(7, 193, 96, 0.2);">{keyword_escaped}</span>'
                keyword_tags.append(keyword_tag)
            keywords_html = " ".join(keyword_tags)

        # 生成星星评级 HTML
        stars_html = self._generate_stars_html(article_summary.score)

        # 使用模板填充
        # 注意：使用 format() 方法填充占位符
        try:
            html_card = article_card_template.format(
                title=article_summary.title,
                account_name=article_summary.account_name,
                keywords_html=keywords_html,
                article_url=article_summary.article_url,
                cover_url=article_summary.cover_url,
                summary=article_summary.summary,
                stars_html=stars_html,
                reason=article_summary.reason
            )
            return html_card
        except KeyError as e:
            logging.error(f"模板填充失败，缺少字段: {e}")
            return ""
        except Exception as e:
            logging.error(f"生成富文本卡片失败: {e}")
            return ""

    def _check_article_publish_time(self, article_metadata: ArticleMetadata, date: datetime) -> bool:
        """检查文章发布日期是否与指定日期匹配

        Args:
            article_metadata(ArticleMetadata): 文章元数据
            date(datetime): 目标日期
        Returns:
            bool: 如果文章发布日期与目标日期相同返回 True，否则返回 False
        """
        try:
            # 将字符串格式的发布时间解析为 datetime 对象
            # publish_time 格式: "2026-01-12 10:00"
            article_datetime = datetime.strptime(
                article_metadata.publish_time, "%Y-%m-%d %H:%M")

            # 只比较日期部分（忽略时间）
            return article_datetime.date() == date.date()
        except (ValueError, AttributeError) as e:
            # 如果解析失败或格式不正确，记录警告并返回 False
            logging.warning(
                f"无法解析文章发布时间: {article_metadata.publish_time}, 错误: {e}")
            return False

    async def build_workflow(self, markdown_file: str, date: datetime):
        """执行完整的日报生成工作流

        工作流步骤：
        1. 从 markdown 文件中解析文章链接
        2. 获取每篇文章的 HTML 内容并提取元数据
        3. 使用 LLM 为每篇文章生成摘要和评分
        4. 将所有文章摘要按照评分降序排列
        5. 对高分文章（3星及以上）进行去重优化
        6. 为高分文章（3星及以上）或得分最高的3篇文章生成富文本内容
        7. 保存富文本内容到HTML文件

        Args:
            markdown_file(str): 采集器生成的文章链接文件路径
            date(datetime): 日期
        Returns:
            None: 富文本内容会保存到 output/daily_rich_text_YYYYMMDD.html 文件
        """
        logging.info("=== 开始每日日报生成工作流 ===")

        summaries = []

        # 步骤1：提取所有文章元数据
        logging.info("步骤1: 提取文章元数据...")

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
                metadata = self._extract_article_metadata(html_content, url)

                # 检查文章发布日期是否与目标日期匹配
                if not self._check_article_publish_time(metadata, date):
                    logging.info(
                        f"文章发布日期不匹配，跳过: {metadata.title} "
                        f"(发布时间: {metadata.publish_time}, 目标日期: {date.strftime('%Y-%m-%d')})"
                    )
                    continue

                articles.append(metadata)
                logging.info(
                    f"成功提取: {metadata.title} (发布时间: {metadata.publish_time})")

            except Exception as e:
                logging.error(f"提取文章失败，跳过: {url}, 错误: {e}")
                continue

        logging.info(f"提取完成，成功 {len(articles)}/{len(urls)} 篇")
        logging.info(
            f"其中符合目标日期({date.strftime('%Y年%m月%d日')})的文章: {len(articles)} 篇")

        if not articles:
            logging.warning("未提取到任何文章，工作流结束")
            return []

        # 步骤2：为每篇文章生成摘要
        logging.info("步骤2: 生成文章摘要...")
        for article in articles:
            summary = await self._generate_article_summary(article, date)
            if summary:
                summaries.append(summary)
            else:
                logging.error(f"生成文章摘要失败: {article.title}")
                continue

        # 步骤3：按评分降序排列
        summaries.sort(key=lambda x: x.score, reverse=True)

        logging.info("=== 每日日报生成工作流完成 ===")
        logging.info(f"共生成 {len(summaries)} 篇文章摘要")

        # 步骤4：输出高分文章（3星及以上）
        high_score_articles = [s for s in summaries if s.score >= 3]
        if high_score_articles:
            logging.info(f"推荐文章（3星及以上）: {len(high_score_articles)} 篇")
            for s in high_score_articles:
                logging.info(f"  - [{s.score}星] {s.title}")

            # 步骤4.5：对高分文章进行去重优化（新增）
            logging.info("步骤5: 对高分文章进行去重优化...")
            high_score_articles = await self._result_optimize(high_score_articles)

            # 输出去重后的结果
            high_score_articles_after_optimize = [
                s for s in high_score_articles if s.score >= 3]
            if len(high_score_articles_after_optimize) < len(high_score_articles):
                logging.info(
                    f"去重后剩余推荐文章: {len(high_score_articles_after_optimize)} 篇")
                for s in high_score_articles_after_optimize:
                    logging.info(f"  - [{s.score}星] {s.title}")

        # 步骤6：为高分文章（3星及以上）或得分最高的若干篇文章生成富文本内容
        logging.info("步骤6: 生成富文本内容...")

        # 筛选逻辑：优先3星及以上，不足3篇则扩展到所有非去重文章
        if high_score_articles:
            # 从去重后的 high_score_articles 中筛选 >= 3 星的文章
            high_score_articles_final = [
                s for s in high_score_articles if s.score >= 3]

            if len(high_score_articles_final) < 3:
                logging.warning(
                    f"3星及以上文章仅有 {len(high_score_articles_final)} 篇，"
                    f"扩展选取去重后的所有有价值文章（score > 0）"
                )
                # 将 high_score_articles 与原始 summaries 合并，排除无价值文章（score = 0）
                # 1. 从 high_score_articles 中获取所有 score > 0 的文章
                valid_high_score = [
                    s for s in high_score_articles if s.score > 0]

                # 2. 从原始 summaries 中获取所有 score < 3 且 > 0 的文章（1-2分的文章）
                low_score_articles = [s for s in summaries if 0 < s.score < 3]

                # 3. 合并并按评分降序排列
                all_valid_articles = valid_high_score + low_score_articles
                # 去重（避免重复），按 title 去重
                seen_titles = set()
                unique_articles = []
                for article in all_valid_articles:
                    if article.title not in seen_titles:
                        seen_titles.add(article.title)
                        unique_articles.append(article)

                # 按评分降序排列，有几篇取几篇（不强制3篇）
                high_score_articles_final = sorted(
                    unique_articles, key=lambda x: x.score, reverse=True
                )

                logging.info(f"扩展后共选取 {len(high_score_articles_final)} 篇文章")
        else:
            # 如果原本就没有3星以上文章，从所有文章中选取所有正分文章（score >= 0）
            logging.warning("没有3星及以上的文章，从所有文章中选取所有正分文章（score > 0）")
            high_score_articles_final = sorted(
                [s for s in summaries if s.score > 0],
                key=lambda x: x.score,
                reverse=True
            )

            if len(high_score_articles_final) == 0:
                logging.error("所有文章评分都为0分，没有任何有价值的文章")
            else:
                logging.info(f"共选取 {len(high_score_articles_final)} 篇有价值文章")

        # 最终检查
        if not high_score_articles_final or len(high_score_articles_final) == 0:
            logging.error("没有任何有价值的文章可用于生成富文本")
            logging.info("=== 每日日报生成工作流完成 ===")
            return

        logging.info(f"正在为 {len(high_score_articles_final)} 篇公众号文章生成富文本...")
        logging.info("最终文章列表:")
        for i, s in enumerate(high_score_articles_final, 1):
            logging.info(f"  {i}. [{s.score}星] {s.title}")

        rich_text_contents = []
        for i, article in enumerate(high_score_articles_final, 1):
            logging.info(
                f"生成第 {i}/{len(high_score_articles_final)} 篇: {article.title}")
            try:
                # 注意：_generate_rich_text_content 现在是同步方法（使用模板填充）
                rich_text_content = self._generate_rich_text_content(article)
                if rich_text_content:
                    rich_text_contents.append(rich_text_content)
                    logging.info(f"  ✓ 富文本生成成功")
                else:
                    logging.error(f"  ✗ 生成富文本内容失败（返回为空）: {article.title}")
            except Exception as e:
                logging.error(f"  ✗ 生成富文本内容时发生异常: {article.title}, 错误: {e}")
                continue

        # 步骤7：保存富文本内容到文件
        logging.info("步骤7: 保存富文本内容到文件...")

        if not rich_text_contents:
            logging.warning("没有成功生成任何富文本内容，跳过文件保存")
            logging.info("=== 每日日报生成工作流完成 ===")
            return

        # 获取模板
        templates = self._get_rich_text_templates()
        header = templates.get("header", "")
        separator = templates.get("separator", "")
        footer = templates.get("footer", "")

        # 组装最终 HTML
        # 结构：HEADER + (CARD + SEPARATOR) * (n-1) + CARD + FOOTER
        html_parts = [header]
        for i, card in enumerate(rich_text_contents):
            html_parts.append(card)
            # 最后一篇文章后不加分隔符
            if i < len(rich_text_contents) - 1:
                html_parts.append(separator)
        html_parts.append(footer)

        final_html = "\n\n".join(html_parts)

        # 生成输出文件名（基于当前日期，使用路径工具兼容 PyInstaller 打包）
        output_dir = get_output_dir()  # 会自动创建目录
        output_file = str(
            output_dir / f"daily_rich_text_{date.strftime('%Y%m%d')}.html")

        # 保存到文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_html)

        logging.info(f"✓ 富文本内容已保存到: {output_file}")
        logging.info(
            f"✓ 共生成 {len(rich_text_contents)}/{len(high_score_articles_final)} 篇富文本内容")
        logging.info("提示: 可以直接复制文件中 <body> 标签内的内容到微信公众号编辑器")
        logging.info("=== 每日日报生成工作流完成 ===")

        return output_file

    async def run(self, markdown_file: str, date: datetime) -> str:
        """异步运行方法

        Args:
            markdown_file(str): 采集器生成的文章链接文件路径，方便后面的工作流获取信息
            date(datetime): 日期

        Returns:
            str: 输出文件路径，方便后面的工作流获取信息
        """
        return await self.build_workflow(markdown_file, date)
