# 视觉语言大模型相关方法类
from openai import AsyncOpenAI
from openai.types.chat.chat_completion import ChatCompletion
from typing import List, Dict, Any
import mimetypes
import base64
import logging


def encode_img_to_base64(img_path: str) -> str:
    """
    将图片编码为 base64

    Args:
        img_path: 图片路径

    Returns:
        str: base64 编码的图片字符串
    """
    mime_type, _ = mimetypes.guess_type(img_path)
    if not mime_type or not mime_type.startswith("image/"):
        raise ValueError("不支持或无法识别的图像格式")
    with open(img_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:{mime_type};base64,{encoded_string}"


async def chat_with_vlm(
        vlm_client: AsyncOpenAI,
        messages: List[Dict[str, Any]],
        model: str = "qwen3-vl-plus",
        enable_thinking: bool = True,
        thinking_budget: int = 1024) -> ChatCompletion:
    """
    调用 qwen-vl 模型进行对话

    Args:
        vlm_client (AsyncOpenAI): VLM 模型客户端
        messages (List[Dict[str, Any]]): 对话消息列表
        model (str): 模型名称，默认为 "qwen3-vl-plus"
        enable_thinking (bool): 是否启用思考，默认为 True
        thinking_budget (int): 思考预算，默认为 1024

    Returns:
        ChatCompletion: 模型返回的对话完成对象

    Raises:
        Exception: 调用模型失败时抛出
    """
    try:
        response = await vlm_client.chat.completions.create(
            model=model,
            messages=messages,
            extra_body={
                "enable_thinking": enable_thinking,
                "thinking_budget": thinking_budget
            }
        )
        return response
    except Exception as e:
        logging.exception("调用 VLM 模型失败")
        raise
