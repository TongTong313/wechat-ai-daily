from openai import AsyncOpenAI
from typing import Dict, Any, List

import logging
import re
from openai.types.chat.chat_completion import ChatCompletion


async def chat_with_llm(llm_client: AsyncOpenAI,
                        messages: List[Dict[str, Any]],
                        model: str = "qwen-plus",
                        enable_thinking: bool = True,
                        thinking_budget: int = 1024) -> ChatCompletion:
    """
    调用大模型进行对话

    Args:
        llm_client (AsyncOpenAI): LLM 客户端
        messages (List[Dict[str, Any]]): 对话消息列表
        model (str): 模型名称，默认为 "qwen-plus"
        enable_thinking (bool): 是否启用思考，默认为 True
        thinking_budget (int): 思考预算，默认为 1024

    Returns:
        ChatCompletion: 模型返回的对话完成对象

    Raises:
        Exception: 调用模型失败时抛出
    """
    try:
        response = await llm_client.chat.completions.create(model=model, messages=messages, extra_body={"enable_thinking": enable_thinking, "thinking_budget": thinking_budget})
        return response
    except Exception as e:
        logging.exception(f"调用大模型失败: {e}")
        raise e


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
