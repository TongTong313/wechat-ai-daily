 # 视觉语言大模型相关方法类
 
 # 需要使用qwen模型
        self.vlm_client = AsyncOpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        # 临时截图目录（任务完成后会自动清理）
        self._screenshot_dir = Path(".tmp_screenshots")

    def _encode_img_to_base64(self, img_path: str) -> str:
        mime_type, _ = mimetypes.guess_type(img_path)
        if not mime_type or not mime_type.startswith("image/"):
            raise ValueError("不支持或无法识别的图像格式")
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(
                image_file.read()).decode('utf-8')
        return f"data:{mime_type};base64,{encoded_string}"

    async def _get_text_location_from_img(
            self,
            img_path: str,
            text: str,
            max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        调用 qwen-vl 模型识别图片中指定文本的位置，支持重试机制

        Args:
            img_path: 图片路径
            text: 要查找的文本
            max_retries: 最大重试次数，默认为 3

        Returns:
            包含位置信息的列表，每个元素为 {'x': float, 'y': float, 'width': float, 'height': float}
            所有值都是相对坐标，范围 0-1

        Raises:
            ValueError: 当达到最大重试次数仍无法成功解析时抛出
        """
        # 构建提示词，要求模型返回相对坐标（0-1之间的比例）
        system_prompt = f"""
# 角色定位
    你是一个文本定位助手，你的任务是：
    1. 在图片中找到所有用户指定的且颜色为**绿色**的文字，并返回每个匹配文字的位置信息。
    2. 返回的文字位置信息包含文本的中心点相对坐标和文本的相对宽度和高度。

# 要求
1. 只返回完全匹配或包含用户指定**绿色**文字的文字位置
2. 每个位置用以下Json格式输出：
```json
{{
    "location": {{
        "x": 中心点x相对坐标,
        "y": 中心点y相对坐标,
        "width": 相对宽度,
        "height": 相对高度
    }}
}}
```
3. 如果找到多个匹配，Json列表中包含多个location
4. 如果没有找到匹配，返回空
5. **重要**：所有坐标和尺寸都使用相对值（0-1之间的小数）
    - x: 中心点x坐标 / 图片宽度
    - y: 中心点y坐标 / 图片高度
    - width: 文本框宽度 / 图片宽度
    - height: 文本框高度 / 图片高度
6. <x>、<y>、<width>、<height>内的值**有且只能**有一个小数值（0-1之间）
7. 务必确保你找到的字体颜色是绿色！而不是字的背景颜色是绿色。

# 举例：
假设图片尺寸为 1000x800，文本中心点在 (500, 400)，宽度200，高度100
user prompt: 机器之心
model response:
```json
{{
    "location": {{
        "x": 0.5,
        "y": 0.5,
        "width": 0.2,
        "height": 0.125
    }}
}}
```
        """.strip()

        # 将图片编码为 base64
        img_base64 = self._encode_img_to_base64(img_path)

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
                response = await self.vlm_client.chat.completions.create(
                    model="qwen3-vl-plus", messages=messages)

                # 获取模型返回的内容
                full_response = response.choices[0].message.content

                # 解析 XML 格式的位置信息，获取解析状态和结果
                success, locations = self._parse_location(full_response)

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

    def _parse_location(self,
                        response: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        解析模型返回的 JSON 格式位置信息（相对坐标），并进行校验

        Args:
            response (str): 模型返回的原始文本

        Returns:
            Tuple[bool, List[Dict[str, Any]]]:
                - 第一个值：是否解析成功（True/False）
                - 第二个值：解析后的位置列表，包含相对坐标（0-1之间的浮点数），
                           每个位置包含 x, y, width, height 四个键

        校验规则：
            - 如果没有找到任何 location，返回 (False, [])
            - 如果 location 缺少 x/y/width/height 任一字段，返回 (False, [])
            - 如果坐标值不在 0-1 范围内，返回 (False, [])
            - 只有成功解析到至少一个完整且有效的 location，才返回 (True, locations)
        """
        import json
        import re

        locations = []

        # 尝试从响应中提取 JSON
        json_data = self._extract_json_from_response(response)

        if json_data is None:
            print("解析失败：无法从响应中提取有效的 JSON")
            return (False, [])

        # 处理不同的 JSON 结构
        location_list = self._normalize_location_data(json_data)

        if not location_list:
            print("解析失败：未找到任何 location 数据")
            return (False, [])

        # 校验每个 location
        for i, loc in enumerate(location_list):
            valid, result = self._validate_location(loc, i)
            if not valid:
                return (False, [])
            locations.append(result)

        # 所有 location 都解析成功且校验通过
        print(f"解析成功：找到 {len(locations)} 个有效位置")
        return (True, locations)

    def _extract_json_from_response(self, response: str) -> Any:
        """
        从模型响应中提取 JSON 数据

        支持以下格式：
        1. 纯 JSON 字符串
        2. markdown 代码块包裹的 JSON
        3. 混合文本中的 JSON

        Args:
            response: 模型返回的原始文本

        Returns:
            解析后的 JSON 数据，失败返回 None
        """
        import json
        import re

        # 1. 尝试直接解析
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # 2. 尝试从 markdown 代码块中提取
        code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        matches = re.findall(code_block_pattern, response)
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

        # 3. 尝试查找 JSON 对象或数组
        # 查找 JSON 对象 {...}
        obj_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        obj_matches = re.findall(obj_pattern, response)
        for match in obj_matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # 查找 JSON 数组 [...]
        arr_pattern = r'\[[\s\S]*?\]'
        arr_matches = re.findall(arr_pattern, response)
        for match in arr_matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        return None

    def _normalize_location_data(self, json_data: Any) -> List[Dict[str, Any]]:
        """
        将不同格式的 JSON 数据统一转换为 location 列表

        支持的格式：
        1. {"location": {...}}  - 单个 location
        2. [{"location": {...}}, ...]  - location 列表
        3. {"locations": [...]}  - locations 数组
        4. [{"x": ..., "y": ...}, ...]  - 直接的坐标列表

        Args:
            json_data: 解析后的 JSON 数据

        Returns:
            location 字典列表
        """
        result = []

        if isinstance(json_data, dict):
            # 格式1: {"location": {...}}
            if "location" in json_data:
                result.append(json_data["location"])
            # 格式3: {"locations": [...]}
            elif "locations" in json_data:
                for item in json_data["locations"]:
                    if isinstance(item, dict):
                        if "location" in item:
                            result.append(item["location"])
                        else:
                            result.append(item)
            # 直接是坐标字典
            elif "x" in json_data and "y" in json_data:
                result.append(json_data)

        elif isinstance(json_data, list):
            # 格式2: [{"location": {...}}, ...]
            # 格式4: [{"x": ..., "y": ...}, ...]
            for item in json_data:
                if isinstance(item, dict):
                    if "location" in item:
                        result.append(item["location"])
                    elif "x" in item and "y" in item:
                        result.append(item)

        return result

    def _validate_location(self, loc: Dict[str, Any],
                           index: int) -> Tuple[bool, Dict[str, float]]:
        """
        校验单个 location 数据

        Args:
            loc: location 字典
            index: 当前 location 的索引（用于错误提示）

        Returns:
            Tuple[bool, Dict]: (是否有效, 校验后的 location 字典)
        """
        required_fields = ['x', 'y', 'width', 'height']

        # 检查必需字段
        for field in required_fields:
            if field not in loc:
                print(f"解析失败：第 {index + 1} 个 location 缺少字段 '{field}'")
                return (False, {})

        try:
            # 转换为浮点数
            x = float(loc['x'])
            y = float(loc['y'])
            width = float(loc['width'])
            height = float(loc['height'])

            # 校验范围 0-1
            values = {'x': x, 'y': y, 'width': width, 'height': height}
            for name, value in values.items():
                if not (0 <= value <= 1):
                    print(
                        f"解析失败：第 {index + 1} 个 location 的 {name}={value} 超出 0-1 范围"
                    )
                    return (False, {})

            return (True, {'x': x, 'y': y, 'width': width, 'height': height})

        except (ValueError, TypeError) as e:
            print(f"解析失败：第 {index + 1} 个 location 的坐标值无法转换为数字: {e}")
            return (False, {})