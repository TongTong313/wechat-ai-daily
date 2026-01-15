# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Claude code 智能体执行规则

- 始终使用中文与我交流
- 严格遵循我的指示，在没有让你生成或修改代码文件的时候，你不允许修改文件内容
- 在指明修改部分文件时，请只修改我指定的部分，如果你发现其他需要修改的部分，**必须**先征求我的同意，我同意后方可修改
- 除非我明确要求生成这些格式的文档，否则绝对**不允许**生成 markdown、txt、docs 等格式的文档
- 在生成代码时，务必包含详尽的**中文注释**方便我理解代码
- 代码要尽可能简练、易读、具备高可用性，拒绝过度设计
- 你的修改有可能就会导致 README.md、CHANGELOG.md、CLAUDE.md 等文档内容过时，请在修改代码后，检查这些文档内容是否需要更新，如果需要，**必须**先征求我的同意后再进行更新
- 执行过程中有任何不清楚的问题，**必须**先和我讨论确认后，方可进行下一步操作

## 项目概述

这是一个微信公众号文章自动化收集工具，通过 GUI 自动化和网络爬虫技术获取微信公众号的文章信息。

## 开发环境设置

### 包管理器

项目使用 **uv** 作为包管理器（而非 pip）。

### 安装依赖

```bash
uv sync
```

### 激活虚拟环境

```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 环境变量配置

项目需要配置以下环境变量：

```bash
# 必需：阿里云 DashScope API Key（用于 VLM 图像识别）
export DASHSCOPE_API_KEY="your_api_key_here"

# Windows PowerShell
$env:DASHSCOPE_API_KEY="your_api_key_here"
```

### 配置文件

在 `configs/config.yaml` 中配置要采集的公众号文章 URL：

```yaml
article_urls:
  - https://mp.weixin.qq.com/s/xxxxx
  - https://mp.weixin.qq.com/s/yyyyy
```

### 运行主程序

```bash
python main.py
```

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行单个测试文件
python -m pytest tests/test_tt.py

# 运行单个测试（带详细输出）
python -m pytest tests/test_tt.py -v

# 运行完整工作流端到端测试（需要真实微信环境）
python tests/test_complete_workflow.py
```

## 项目架构

### 核心模块结构

```
src/wechat_ai_daily/
├── utils/          # 工具模块
│   ├── extractors.py   # 网页数据提取（biz 参数）
│   ├── wechat.py       # 微信进程管理和窗口控制
│   ├── autogui.py      # GUI 自动化操作（键盘、鼠标、截图、点击）
│   └── vlm.py          # 视觉语言模型（VLM）图像识别
├── workflows/      # 工作流模块
│   └── wechat_autogui.py  # 微信公众号文章收集器（异步工作流）
└── llm/           # LLM 模块（预留）

frontend/          # 前端监控模块（可选，用于测试时实时监控）
├── index.html           # 前端监控页面（显示日志、截图、进度）
├── server.py            # FastAPI + WebSocket 服务器
├── progress_reporter.py # 进度上报器（通过 WebSocket 推送数据）
├── logging_handler.py   # 自定义日志 Handler（拦截 logging 输出）
└── README.md            # 前端集成文档
```

### 前端监控功能（可选）

项目包含一个可选的前端监控系统，用于在测试时实时查看 RPA 执行情况：

- **实时日志同步**：自动拦截所有 logging 输出并推送到前端
- **操作状态识别**：通过正则表达式智能识别当前操作（如"打开微信"、"VLM识别中"）
- **进度统计**：自动提取并显示进度信息（如"处理第 1/2 个公众号"）
- **截图实时推送**：通过 monkey patch 拦截截图函数，自动推送到前端
- **文章链接采集**：实时显示采集到的文章链接

**使用方法：**
```bash
# 运行带前端监控的测试
uv run python tests/test_with_frontend.py

# 浏览器会自动打开 http://localhost:8765
# 点击"开始测试"按钮即可启动
```

**技术特点：**
- 零侵入性：无需修改 `src/` 核心代码
- 自动化：通过自定义 logging Handler 自动转发所有日志
- 智能解析：自动识别日志中的状态、进度、链接等信息

详见 `frontend/README.md` 了解更多技术细节。
```

### 关键技术组件

1. **微信进程管理** (`utils/wechat.py`)

   - 跨平台支持（Windows 使用 tasklist/PowerShell，macOS 使用 pgrep/osascript）
   - 检查微信是否运行：`is_wechat_running(os_name)`
   - 激活微信窗口到前台：`activate_wechat_window(os_name)`

2. **网页数据提取** (`utils/extractors.py`)

   - 从微信文章 URL 提取 biz 参数（公众号唯一标识符）
   - 使用正则表达式从 HTML 中提取数据
   - 模拟浏览器 User-Agent 避免被识别为爬虫

3. **GUI 自动化** (`utils/autogui.py`)

   - 使用 pynput 库进行键盘控制
   - 使用 pyautogui 库进行屏幕截图、图像识别和点击操作
   - `press_keys(*keys)`: 支持组合键操作（如 ctrl+v）
   - `scroll_down(amount)`: 页面滚动
   - `screenshot_current_window(save_path)`: 截取当前屏幕
   - `click_relative_position(rel_x, rel_y)`: 根据相对坐标点击（处理高分辨率显示屏缩放）
   - `click_button_based_on_img(img_path)`: 基于模板图片匹配点击按钮
   - `get_screen_scale_ratio()`: 获取屏幕缩放比例（处理 Retina 等高分屏）

4. **视觉语言模型（VLM）** (`utils/vlm.py`)

   - 使用阿里云 DashScope 的 qwen-vl 模型进行图像识别
   - `get_text_location_from_img(vlm_client, img_path, text)`: 识别图片中指定文本的位置
   - 返回相对坐标（0-1 范围），支持多个匹配位置
   - 内置重试机制和 XML 格式解析校验
   - 用于自动识别公众号页面中的文章日期位置

5. **工作流编排** (`workflows/wechat_autogui.py`)
   - `OfficialAccountArticleCollector`: 公众号文章收集器类（异步工作流）
   - 自动打开/激活微信应用
   - `build_workflow()`: 异步方法，执行完整的文章采集流程
   - `run()`: 同步入口方法，使用 asyncio.run() 调用 build_workflow()
   - 支持多公众号批量采集，自动去重，错误恢复

### 平台兼容性

项目支持 Windows 和 macOS，通过 `sys.platform` 检测操作系统：

- `win32`: Windows 平台
- `darwin`: macOS 平台

不同平台使用不同的系统命令：

- Windows: tasklist, PowerShell, cmd
- macOS: pgrep, osascript, open

## 技术依赖

### 核心依赖

- **pyautogui**: GUI 自动化框架（截图、图像识别、点击）
- **pynput**: 键盘和鼠标控制
- **requests**: HTTP 请求库
- **openai**: OpenAI SDK（用于调用阿里云 DashScope VLM API）
- **pyperclip**: 剪贴板操作
- **pyyaml**: YAML 配置文件解析
- **pillow**: 图像处理
- **opencv-python**: 图像处理（用于模板匹配）
- **pygetwindow**: Windows 窗口管理
- **rich**: 终端美化输出

### 开发依赖

- **pytest**: 测试框架

## 开发注意事项

### 模板图片依赖

项目依赖 `templates/` 目录下的模板图片进行 GUI 自动化：

- `search_website.png` / `search_website_win.png`: "访问网页"按钮（macOS/Windows）
- `three_dots.png`: 右上角三个点菜单按钮
- `turnback.png`: 返回按钮

这些图片用于 `pyautogui.locateOnScreen()` 进行屏幕匹配。如果界面发生变化，需要重新截图更新模板。

### 异步工作流架构

- `OfficialAccountArticleCollector.build_workflow()` 是异步方法（使用 `async def`）
- 内部调用 VLM 识别方法时使用 `await`
- 同步调用入口是 `run()` 方法，内部使用 `asyncio.run(self.build_workflow())`
- 在编写新功能时，如果需要调用 VLM 相关方法，必须使用异步函数

### 屏幕坐标转换

- VLM 返回的是相对坐标（0-1 范围）
- 需要转换为物理像素坐标，再转换为逻辑坐标
- 高分辨率显示屏（如 Retina）的缩放比例需要特殊处理
- `get_screen_scale_ratio()` 和 `click_relative_position()` 已处理此问题

### 微信自动化限制

- 微信公众号文章列表获取受到严格的反爬虫限制
- 仅模拟 User-Agent 不足以绕过验证
- 项目采用 GUI 自动化 + VLM 图像识别的混合方案

### 日志记录

项目使用 Python 标准 logging 模块，关键操作都有日志输出。测试时日志会同时输出到控制台和文件（`logs/` 目录）。

### 工作流执行流程

完整的文章采集流程：

1. 打开/激活微信应用
2. 从配置文件读取文章 URL，提取 biz 参数，构建公众号主页 URL
3. 对每个公众号：
   - 打开微信搜索（ctrl/cmd+f）
   - 输入公众号 URL 并搜索
   - 点击"访问网页"进入公众号主页
   - 循环采集当天文章：
     - 截图当前页面
     - 使用 VLM 识别当天日期的文章位置
     - 点击文章，复制链接，返回主页
     - 滚动页面加载更多文章
     - 检测到昨天日期时停止
   - 保存采集结果到 Markdown 文件
4. 输出采集统计报告
