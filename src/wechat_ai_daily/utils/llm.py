from openai import AsyncOpenAI
from typing import Dict, Any, List
from pydantic import ValidationError
import logging
import re
import json

from ..utils.types import ArticleMetadata, ArticleSummary


def extract_json_from_response(response: str) -> str:
    """从大模型响应中提取 JSON 字符串

    大模型可能返回的格式：
    1. 纯 JSON: {"title": "xxx", ...}
    2. Markdown 代码块: ```json\n{"title": "xxx", ...}\n```
    3. 带有额外文字说明的响应

    Args:
        response: 大模型的原始响应文本

    Returns:
        str: 提取出的 JSON 字符串
    """
    # 尝试匹配 markdown 代码块中的 JSON
    # 支持 ```json 和 ``` 两种格式
    code_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    match = re.search(code_block_pattern, response)
    if match:
        return match.group(1).strip()

    # 尝试匹配花括号包围的 JSON 对象
    json_pattern = r'\{[\s\S]*\}'
    match = re.search(json_pattern, response)
    if match:
        return match.group(0).strip()

    # 如果都没匹配到，返回原始响应（去除首尾空白）
    return response.strip()


async def generate_article_summary(llm_client: AsyncOpenAI,
                                   article_metadata: ArticleMetadata,
                                   model: str = "qwen3-plus",
                                   max_retries: int = 2) -> ArticleSummary:
    """
    根据文章元数据，使用大模型生成文章摘要总结信息，给出文章推荐度评分，并给出推荐理由

    重试机制会保持完整的对话上下文，让模型基于之前的对话修正输出。

    Args:
        llm_client (AsyncOpenAI): LLM 客户端
        article_metadata (ArticleMetadata): 文章元数据
        model (str): 模型名称，默认为 "qwen3-plus"
        max_retries (int): 最大重试次数，默认为 2

    Returns:
        ArticleSummary: 解析成功返回摘要对象

    Raises:
        ValueError: JSON 解析最终失败时抛出
    """

    SYSTEM_PROMPT = """
# 角色与任务要求
你是每日AI公众号内容推荐助手，你的任务是：根据公众号文章元数据，生成文章摘要、推荐度评分和推荐理由，你评分较高的文章我会形成每日AI公众号内容日报，推荐给用户。

# 具体要求
1. 文章摘要限200字以内，简明扼要的阐述公众号文章主要说了一个什么样的技术、应用、故事或者观点等
2. 文章推荐度评分范围为 0-100，0为不推荐，100为强烈推荐，通常90分以上推荐度才会被推荐给用户。
3. 文章推荐理由主要阐明读了这个文章以后能得到什么样的收获和启发？文章的价值在哪里等，字数限制100字以内。
4. 你的评分要尽可能严格，我们要推荐最优质的文章给用户，不要因为文章质量不高而推荐给用户。
5. 请使用中文回复。

# 输出格式
要求通过json格式输出，格式如下：
```json
{
    "title": "文章标题",
    "account_name": "公众号名称",
    "publish_time": "2026-01-12",
    "score": 整数型分数值(0-100),
    "summary": "文章摘要",
    "reason": "文章推荐理由"
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

    # 首次调用大模型
    response = await llm_client.chat.completions.create(model=model, messages=messages)
    raw_content = response.choices[0].message.content

    # 尝试解析
    try:
        json_str = extract_json_from_response(raw_content)
        return ArticleSummary.model_validate_json(json_str)
    except (ValidationError, json.JSONDecodeError) as e:
        logging.warning(f"解析 JSON 失败: {e}")
        last_error = str(e)

    # 解析失败，进入重试循环（保持对话上下文）
    for attempt in range(max_retries):
        logging.info(f"尝试让大模型修正 JSON 格式 (第 {attempt + 1}/{max_retries} 次)")

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
            response = await llm_client.chat.completions.create(model=model, messages=messages)
            raw_content = response.choices[0].message.content

            # 尝试解析修正后的输出
            json_str = extract_json_from_response(raw_content)
            return ArticleSummary.model_validate_json(json_str)

        except (ValidationError, json.JSONDecodeError) as e:
            logging.warning(f"第 {attempt + 1} 次修正后仍解析失败: {e}")
            last_error = str(e)
        except Exception as e:
            logging.error(f"调用大模型修正时发生异常: {e}")
            break

    logging.error(f"JSON 解析最终失败，已重试 {max_retries} 次")
    raise ValueError(f"JSON 解析最终失败，已重试 {max_retries} 次")
