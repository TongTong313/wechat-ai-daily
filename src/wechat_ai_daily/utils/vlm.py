# 视觉语言大模型相关方法类
from openai import AsyncOpenAI
from typing import List, Dict, Any
import mimetypes
import base64
import re


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


async def get_text_location_from_img(
        vlm_client: AsyncOpenAI,
        img_path: str,
        text: str,
        model: str = "qwen3-vl-plus",
        max_retries: int = 3) -> List[Dict[str, Any]]:
    """
    调用 qwen-vl 模型识别图片中指定文本的位置，支持重试机制

    Args:
        vlm_client: VLM 模型客户端
        img_path: 图片路径
        text: 要查找的文本
        max_retries: 最大重试次数，默认为 3

    Returns:
        List[Dict[str, Any]]: 包含位置信息的列表，每个元素为 {'x': float, 'y': float, 'width': float, 'height': float}
        所有值都是相对坐标，范围 0-1

    Raises:
        ValueError: 当达到最大重试次数仍无法成功解析时抛出
    """

    def _parse_xml_locations(
            response: str) -> tuple[bool, List[Dict[str, Any]]]:
        """
        解析模型返回的 XML 格式位置信息（相对坐标），并进行校验

        根据提示词要求，解析格式为：
        <location>
            <x>0.5</x>
            <y>0.5</y>
            <width>0.2</width>
            <height>0.125</height>
        </location>

        Args:
            response: 模型返回的原始文本

        Returns:
            tuple[bool, List[Dict[str, Any]]]:
                - 第一个值：是否解析成功（True/False）
                - 第二个值：解析后的位置列表，每个位置包含 x, y, width, height 四个键

        校验规则：
            - 如果没有找到任何 location，返回 (False, [])
            - 如果 location 缺少 x/y/width/height 任一字段，返回 (False, [])
            - 如果坐标值不在 0-1 范围内，返回 (False, [])
            - 只有成功解析到至少一个完整且有效的 location，才返回 (True, locations)
        """
        locations = []

        # 使用正则表达式匹配所有 <location>...</location> 块
        location_pattern = r'<location>(.*?)</location>'
        location_matches = re.findall(location_pattern, response, re.DOTALL)

        if not location_matches:
            print("解析失败：未找到任何 <location> 标签")
            return (False, [])

        # 解析每个 location 块
        for i, location_content in enumerate(location_matches):
            # 提取 x, y, width, height 的值
            x_match = re.search(r'<x>(.*?)</x>', location_content)
            y_match = re.search(r'<y>(.*?)</y>', location_content)
            width_match = re.search(r'<width>(.*?)</width>', location_content)
            height_match = re.search(r'<height>(.*?)</height>',
                                     location_content)

            # 检查是否所有字段都存在
            if not all([x_match, y_match, width_match, height_match]):
                missing_fields = []
                if not x_match:
                    missing_fields.append('x')
                if not y_match:
                    missing_fields.append('y')
                if not width_match:
                    missing_fields.append('width')
                if not height_match:
                    missing_fields.append('height')
                print(f"解析失败：第 {i + 1} 个 location 缺少字段 {missing_fields}")
                return (False, [])

            try:
                # 提取并转换为浮点数
                x = float(x_match.group(1).strip())
                y = float(y_match.group(1).strip())
                width = float(width_match.group(1).strip())
                height = float(height_match.group(1).strip())

                # 校验范围 0-1
                values = {'x': x, 'y': y, 'width': width, 'height': height}
                for name, value in values.items():
                    if not (0 <= value <= 1):
                        print(
                            f"解析失败：第 {i + 1} 个 location 的 {name}={value} 超出 0-1 范围"
                        )
                        return (False, [])

                # 添加到结果列表
                locations.append({
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height
                })

            except (ValueError, AttributeError) as e:
                print(f"解析失败：第 {i + 1} 个 location 的坐标值无法转换为数字: {e}")
                return (False, [])

        # 所有 location 都解析成功且校验通过
        print(f"解析成功：找到 {len(locations)} 个有效位置")
        return (True, locations)

    # 构建提示词，要求模型返回相对坐标（0-1之间的比例）
    system_prompt = f"""
# 角色定位
你是一个文本定位助手，你的任务是：
1. 在图片中找到所有用户指定的文字，并返回每个匹配文字的位置信息。
2. 返回的文字位置信息包含文本的中心点相对坐标和文本的相对宽度和高度。

# 要求
1. 只返回完全匹配或包含用户指定文字的文字位置
2. 每个位置用以下格式输出：
<location>
    <x>中心点x相对坐标</x>
    <y>中心点y相对坐标</y>
    <width>相对宽度</width>
    <height>相对高度</height>
</location>
<location>
    <x>中心点x相对坐标</x>
    <y>中心点y相对坐标</y>
    <width>相对宽度</width>
    <height>相对高度</height>
</location>
...
3. 如果找到多个匹配，要包含多个<location>元素
4. 如果没有找到匹配，返回空
5. **重要**：所有坐标和尺寸都使用相对值（0-1之间的小数）
- x: 中心点x坐标 / 图片宽度
- y: 中心点y坐标 / 图片高度
- width: 文本框宽度 / 图片宽度
- height: 文本框高度 / 图片高度
6. <x>、<y>、<width>、<height>内的值**有且只能**有一个小数值（0-1之间）

# 举例：
假设图片尺寸为 1000x800，文本中心点在 (500, 400)，宽度200，高度100
user prompt: 机器之心
model response:
<location>
    <x>0.5</x>
    <y>0.5</y>
    <width>0.2</width>
    <height>0.125</height>
</location>
    """.strip()

    # 将图片编码为 base64
    img_base64 = encode_img_to_base64(img_path)

    # 构建 messages
    messages: List[Dict[str, Any]] = []
    messages.append({"role": "system", "content": system_prompt})
    messages.append({
        "role":
        "user",
        "content": [{
            "type": "image_url",
            "image_url": {
                "url": img_base64
            },
        }, {
            "type": "text",
            "text": text
        }]
    })

    # 重试循环
    for attempt in range(1, max_retries + 1):
        print(f"正在尝试 OCR 文本定位（第 {attempt}/{max_retries} 次）...")

        try:
            # 调用 VLM 模型（非流式）
            response = await vlm_client.chat.completions.create(
                model=model, messages=messages)

            # 获取模型返回的内容
            full_response = response.choices[0].message.content

            # 解析 XML 格式的位置信息，获取解析状态和结果
            success, locations = _parse_xml_locations(full_response)

            if success:
                print(f"OCR 文本定位成功，找到 {len(locations)} 个匹配位置")
                return locations
            else:
                print(f"第 {attempt} 次尝试解析失败，模型返回的格式不符合要求")
                if attempt < max_retries:
                    print("准备重试...")

        except Exception as e:
            print(f"第 {attempt} 次尝试时发生异常: {e}")
            if attempt < max_retries:
                print("准备重试...")
            else:
                raise ValueError(f"OCR 文本定位失败：在 {max_retries} 次尝试后仍无法成功解析。"
                                 f"请检查图像质量是否清晰，或尝试调整要查找的文本内容。"
                                 f"原始错误: {e}") from e

    # 如果所有重试都失败（解析失败但没有抛出异常）
    raise ValueError(f"OCR 文本定位失败：在 {max_retries} 次尝试后仍无法成功解析位置信息。"
                     f"模型返回的内容不符合预期格式，请检查图像是否包含目标文本 '{text}'，"
                     f"或尝试使用更清晰的图像。")
