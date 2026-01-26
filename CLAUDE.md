# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供项目开发指导规范。

## Claude Code 智能体执行规则

- 始终使用中文与我交流
- 务必使用uv管理和运行项目python环境，例如运行python脚本需要使用uv run，添加依赖需要使用uv add等
- 在让你生成方案、计划、设计等时，**绝对不允许**修改任何代码和文件内容，**必须**先征求我的同意后再进行文件或代码的修改
- 在没有让你生成或修改代码文件的时候，绝对**不允许**修改文件或代码内容
- 在指明修改部分文件时，请只修改我指定的部分，如果你发现其他需要修改的部分，**必须**先征求我的同意，我同意后方可修改
- 除非我明确要求生成这些格式的文档，否则绝对**不允许**生成 markdown、txt、docs 等格式的文档
- 在生成代码时，务必包含详尽的**中文注释**方便我理解代码
- 代码要尽可能简练、易读、具备高可用性，拒绝过度设计
- 你的修改有可能就会导致 README.md（包括英文版 docs/README_en.md）、CHANGELOG.md（包括英文版 docs/CHANGELOG_en.md）、CLAUDE.md 等文档内容过时，请在修改代码后，检查这些文档内容是否需要更新，如果需要，**必须**先征求我的同意后再进行更新
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

在 `configs/config.yaml` 中配置项目参数：

```yaml
# 目标日期配置
# null 或 "today" 表示当天, "yesterday" 表示昨天, 或指定日期如 "2025-01-25"
target_date: null

# 公众号文章 URL（每个公众号提供一个文章链接，用于定位公众号）
article_urls:
  - https://mp.weixin.qq.com/s/xxxxx # 公众号A
  - https://mp.weixin.qq.com/s/yyyyy # 公众号B

# GUI 自动化模板图片路径（区分操作系统）
GUI_config:
  # macOS 系统
  search_website: templates/search_website_mac.png
  three_dots: templates/three_dots_mac.png
  turnback: templates/turnback_mac.png
  # Windows 系统（取消注释并注释掉 macOS 配置）
  # search_website: templates/search_website.png
  # three_dots: templates/three_dots.png
  # turnback: templates/turnback.png

# 模型配置
model_config:
  LLM:
    model: qwen-plus
    api_key: null # 为 null 时读取环境变量 DASHSCOPE_API_KEY
    thinking_budget: 1024
    enable_thinking: true
  VLM:
    model: qwen3-vl-plus
    api_key: null
    thinking_budget: 1024
    enable_thinking: true
```

### 运行主程序

```bash
# 命令行方式运行
uv run main.py

# 桌面客户端方式运行
uv run app.py
```

### 运行测试

```bash
# 运行所有测试
uv run python -m pytest tests/

# 运行单个测试文件
uv run python -m pytest tests/test_tt.py

# 运行单个测试（带详细输出）
uv run python -m pytest tests/test_tt.py -v

# 运行完整工作流端到端测试（需要真实微信环境）
uv run python tests/test_complete_workflow.py
```

## 项目架构

### 核心模块结构

```
src/wechat_ai_daily/
├── utils/          # 工具模块
│   ├── wechat.py       # 微信进程管理、窗口控制和公众号 API 客户端
│   ├── autogui.py      # GUI 自动化操作（键盘、鼠标、截图、点击）
│   ├── vlm.py          # 视觉语言模型（VLM）图像识别
│   ├── llm.py          # LLM 调用工具（文章摘要生成）
│   ├── types.py        # 数据类型定义（ArticleMetadata, ArticleSummary）
│   ├── paths.py        # 路径管理工具（项目根目录、输出目录等）
│   └── env_loader.py   # 环境变量加载工具（.env 文件支持）
├── workflows/      # 工作流模块
│   ├── base.py           # 工作流抽象基类
│   ├── wechat_autogui.py # 微信公众号文章收集器（异步工作流）
│   ├── daily_generate.py # 每日日报生成器
│   └── daily_publish.py  # 微信公众号自动发布工作流

gui/               # 桌面客户端模块（PyQt6）
├── main_window.py      # 主窗口
├── styles.py           # 样式定义
├── panels/             # UI 面板组件
│   ├── config_panel.py     # 配置面板（日期、链接、API Key）
│   ├── progress_panel.py   # 进度面板（状态、进度条）
│   └── log_panel.py        # 日志面板（实时日志显示）
├── workers/            # 后台工作线程
│   └── workflow_worker.py  # 工作流执行器（在后台线程运行）
└── utils/              # 客户端工具类
    ├── config_manager.py   # 配置管理器（读写 config.yaml）
    └── log_handler.py      # 日志处理器（重定向到 UI）

templates/         # 模板文件目录
├── search_website_mac.png   # macOS "访问网页"按钮模板
├── three_dots_mac.png       # macOS 三个点菜单按钮模板
├── turnback_mac.png         # macOS 返回按钮模板
├── search_website.png       # Windows "访问网页"按钮模板
├── three_dots.png           # Windows 三个点菜单按钮模板
├── turnback.png             # Windows 返回按钮模板
├── rich_text_template.html  # 富文本 HTML 模板（用于生成公众号日报）
├── default_cover.png        # 默认封面图片（文章无封面时使用）
└── README_cover.md          # 封面图片使用说明

docs/              # 英文文档目录
├── README_en.md           # 英文版 README
└── CHANGELOG_en.md        # 英文版更新日志

scripts/           # 构建脚本目录
├── build_macos.sh         # macOS 应用打包脚本
└── build_windows.bat      # Windows 应用打包脚本

output/            # 输出目录（自动创建）
├── articles_YYYYMMDD.md           # 采集到的文章链接列表
└── daily_rich_text_YYYYMMDD.html  # 生成的富文本日报
```

### 关键技术组件

1. **微信进程管理和 API 客户端** (`utils/wechat.py`)

   - 跨平台支持（Windows 使用 tasklist/PowerShell，macOS 使用 pgrep/osascript）
   - 检查微信是否运行：`is_wechat_running(os_name)`
   - 激活微信窗口到前台：`activate_wechat_window(os_name)`
   - `WeChatAPI` 类：微信公众号 API 客户端
     - `get_access_token()`: 获取并缓存 access_token（使用稳定版接口）
     - `create_draft()`: 创建草稿
     - `publish_draft()`: 发布草稿
     - `upload_media()`: 上传永久素材
     - 支持草稿管理、发布管理、素材管理等完整 API

2. **GUI 自动化** (`utils/autogui.py`)

   - 使用 pynput 库进行键盘控制
   - 使用 pyautogui 库进行屏幕截图、图像识别和点击操作
   - `press_keys(*keys)`: 支持组合键操作（如 ctrl+v）
   - `scroll_down(amount)`: 页面滚动
   - `screenshot_current_window(save_path)`: 截取当前屏幕
   - `click_relative_position(rel_x, rel_y)`: 根据相对坐标点击（处理高分辨率显示屏缩放）
   - `click_button_based_on_img(img_path)`: 基于模板图片匹配点击按钮
   - `get_screen_scale_ratio()`: 获取屏幕缩放比例（处理 Retina 等高分屏）

3. **视觉语言模型（VLM）** (`utils/vlm.py`)

   - 使用阿里云 DashScope 的 qwen-vl 模型进行图像识别
   - `get_dates_location_from_img(vlm_client, img_path, dates)`: 识别图片中指定日期的位置
   - 返回相对坐标（0-1 范围），支持多个匹配位置
   - 内置重试机制和 XML 格式解析校验
   - 用于自动识别公众号页面中的文章日期位置

4. **工作流编排** (`workflows/wechat_autogui.py`)
   - `ArticleCollector`: 公众号文章收集器类（异步工作流）
   - 自动打开/激活微信应用
   - `build_workflow()`: 异步方法，执行完整的文章采集流程
   - `run()`: 同步入口方法，使用 asyncio.run() 调用 build_workflow()
   - 支持多公众号批量采集，自动去重，错误恢复

5. **数据类型定义** (`utils/types.py`)
   - `ArticleMetadata`: 公众号文章元数据（标题、作者、发布时间、正文、图片等）
   - `ArticleSummary`: 文章分析结果（评分、内容速览、精选理由）
   - 使用 Pydantic BaseModel，便于 JSON 序列化和与大模型框架集成

6. **路径管理工具** (`utils/paths.py`)
   - 提供项目路径获取函数，兼容 PyInstaller 打包环境
   - `get_project_root()`: 获取项目根目录
   - `get_output_dir()`: 获取输出目录
   - `get_templates_dir()`: 获取模板目录
   - `get_configs_dir()`: 获取配置目录
   - 支持开发环境和打包后环境的路径自动切换

7. **LLM 调用工具** (`utils/llm.py`)
   - `generate_article_summary()`: 异步函数，使用大模型生成内容速览、推荐度评分和精选理由
   - `extract_json_from_response()`: 从大模型响应中提取 JSON 字符串
   - 内置重试机制，保持对话上下文让模型修正输出格式

8. **每日日报生成器** (`workflows/daily_generate.py`)
   - `DailyGenerator`: 每日日报生成器类
   - 解析采集器生成的文章链接 Markdown 文件
   - 获取文章 HTML 并提取元数据（标题、作者、正文、图片等）
   - 使用 BeautifulSoup 解析 HTML，提取 JavaScript 变量区的元数据
   - 使用 LLM 为每篇文章生成内容速览（100-200字）、推荐度评分（0-100分）和精选理由（100字以内）
   - 筛选高分文章（90分以上或前3篇）生成富文本 HTML
   - 输出文件保存到 `output/daily_rich_text_YYYYMMDD.html`

9. **桌面客户端** (`gui/`)
   - `MainWindow`: 主窗口类，整合所有面板组件，支持3步工作流（采集 → 生成 → 发布）
   - `ConfigPanel`: 配置面板，管理日期选择、文章链接、API Key 设置、发布配置（AppID、AppSecret、作者、封面、标题）
   - `ProgressPanel`: 进度面板，显示执行状态和进度条
   - `LogPanel`: 日志面板，实时显示运行日志
   - `WorkflowWorker`: 后台工作线程，支持4种工作流类型（`WorkflowType` 枚举）：
     - `COLLECT`：仅采集文章
     - `GENERATE`：仅生成日报
     - `PUBLISH`：仅发布草稿
     - `FULL`：完整流程（采集 + 生成 + 发布）
   - `ConfigManager`: 配置管理器，读写 config.yaml，支持发布配置管理和凭证来源状态检测
   - `QTextEditLogHandler`: 日志处理器，将 logging 日志重定向到 Qt 信号
   - 入口文件：`app.py`

10. **环境变量加载工具** (`utils/env_loader.py`)
    - `load_env()`: 加载 .env 文件中的环境变量
    - `get_env()`: 获取环境变量值
    - `has_env()`: 检查环境变量是否存在
    - `diagnose_env()`: 诊断环境变量配置情况
    - 配置优先级：config.yaml > 系统环境变量 > .env 文件

11. **工作流基类** (`workflows/base.py`)
    - `BaseWorkflow`: 抽象基类，定义工作流统一接口
    - `build_workflow()`: 抽象方法，构建工作流
    - `run()`: 抽象方法，运行工作流

12. **微信公众号自动发布** (`workflows/daily_publish.py`)
    - `DailyPublisher`: 自动发布工作流类
    - `_html_to_wechat_format()`: HTML 转换为微信公众号格式
    - `_upload_cover_img()`: 上传封面图片并缓存 media_id
    - `_create_draft()`: 创建公众号草稿
    - `build_workflow()`: 基于 HTML 文件创建草稿
    - 支持从 config.yaml 或环境变量读取 AppID/AppSecret

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
- **openai**: OpenAI SDK（用于调用阿里云 DashScope VLM/LLM API）
- **pyperclip**: 剪贴板操作
- **pyyaml**: YAML 配置文件解析
- **pillow**: 图像处理
- **opencv-python**: 图像处理（用于模板匹配）
- **pygetwindow**: Windows 窗口管理
- **rich**: 终端美化输出
- **beautifulsoup4**: HTML 解析（用于提取文章正文内容）
- **pydantic**: 数据验证和序列化（用于定义文章元数据结构）
- **PyQt6**: 桌面客户端 GUI 框架
- **python-dotenv**: 环境变量加载（.env 文件支持）
- **ruamel-yaml**: YAML 配置文件读写（保留注释）

### 开发依赖

- **pytest**: 测试框架

## 开发注意事项

### 模板图片依赖

项目依赖 `templates/` 目录下的模板图片进行 GUI 自动化：

**macOS 系统：**
- `search_website_mac.png`: "访问网页"按钮
- `three_dots_mac.png`: 右上角三个点菜单按钮
- `turnback_mac.png`: 返回按钮

**Windows 系统：**
- `search_website.png`: "访问网页"按钮
- `three_dots.png`: 右上角三个点菜单按钮
- `turnback.png`: 返回按钮

这些图片用于 `pyautogui.locateOnScreen()` 进行屏幕匹配。如果界面发生变化，需要重新截图更新模板。

**其他模板资源：**
- `default_cover.png`: 默认封面图片，当文章没有封面时使用
- `README_cover.md`: 封面图片使用说明文档

### 富文本模板

`templates/rich_text_template.html` 用于生成微信公众号日报的富文本内容：

- 使用特殊注释标记分隔模板片段：`<!-- ===== XXX_START ===== -->` 和 `<!-- ===== XXX_END ===== -->`
- 模板片段包括：HEADER（文档头）、ARTICLE_CARD（文章卡片）、SEPARATOR（分隔符）、FOOTER（底部）
- 文章卡片占位符：
  - `{title}`: 文章标题
  - `{article_url}`: 文章链接
  - `{cover_url}`: 封面图片链接
  - `{summary}`: 内容速览（100-200字）
  - `{score}`: 推荐度评分（0-100）
  - `{reason}`: 精选理由（100字以内）
- 底部署名：自动添加 "以上内容由 Double童发发 开发的 wechat-ai-daily 自动生成"

### 异步工作流架构

- `ArticleCollector.build_workflow()` 是异步方法（使用 `async def`）
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

### 日报生成工作流

完整的日报生成流程（`DailyGenerator.build_workflow()`）：

1. 从 Markdown 文件中解析文章链接列表
2. 对每篇文章：
   - 获取文章 HTML 内容
   - 提取元数据（标题、作者、发布时间、封面图、正文等）
3. 使用 LLM 为每篇文章生成内容速览、评分和精选理由
4. 按评分降序排列所有文章
5. 筛选推荐文章（90分以上，或不足时取前3篇）
6. 使用富文本模板生成 HTML 内容
7. 保存到 `output/daily_rich_text_YYYYMMDD.html`
