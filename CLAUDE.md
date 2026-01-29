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

这是一个微信公众号文章自动化收集工具，提供 **RPA 模式** 和 **API 模式** 两种采集方案：

- **RPA 模式**：通过 GUI 自动化 + VLM 图像识别获取文章，无需公众号账号
- **API 模式**（v2.0.0 新增）：通过微信公众平台后台接口获取文章，高效稳定

## ⚠️ 法律风险与合规性

### 重要提示

本项目涉及以下潜在法律风险，开发者和使用者必须充分了解：

1. **API 模式的法律风险**：
   - 使用微信公众平台的**非公开后台接口**（需通过浏览器开发者工具获取 cookie/token）
   - 可能违反《微信公众平台服务协议》
   - 可能涉及"未经授权访问计算机系统"的法律问题
   - Cookie/token 泄露可能导致账号安全问题

2. **RPA 模式的法律风险**：
   - GUI 自动化操作可能违反微信用户协议
   - 频繁的自动化操作可能触发反作弊机制，导致账号被限制或封禁

3. **数据采集的合规性**：
   - 必须遵守《中华人民共和国数据安全法》《个人信息保护法》
   - 采集的数据仅限个人学习研究使用，不得用于商业目的
   - 不得进行大规模数据抓取或转售

### 开发规范

在开发和维护本项目时，请遵守以下规范：

1. **仅供个人学习研究**：
   - 项目定位为个人学习和研究工具，不得用于商业用途
   - 不得为商业目的添加批量采集、数据转售等功能

2. **用户警告机制**：
   - 在所有入口（命令行、GUI）都必须显示法律声明
   - 在涉及 API 模式的配置说明中必须提示风险
   - 在文档中醒目位置说明使用风险

3. **技术限制**：
   - 不主动绕过微信平台的反爬虫机制
   - 不添加高频请求、批量账号管理等可能被滥用的功能
   - API 模式仅支持本人账号的 cookie/token，不提供多账号管理

4. **文档维护**：
   - LICENSE、README.md、docs/README_en.md 中的法律声明不得删除或弱化
   - 任何新增功能都需要评估法律风险并更新声明

### 免责声明维护要求

在以下情况下必须更新法律声明：

- 新增采集模式或接口
- 新增数据处理功能
- 新增自动化操作功能
- 涉及用户凭证管理的功能变更

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

项目支持三种方式配置敏感信息（推荐使用 .env 文件）：

**配置优先级（从高到低）：**

1. `configs/config.yaml` 文件（最高优先级）
2. `.env` 文件（推荐，自动添加到 .gitignore）
3. 系统环境变量（最低优先级）

**方式一：使用 .env 文件（推荐）**

在项目根目录创建 `.env` 文件：

```bash
# 阿里云 DashScope API Key（用于 VLM 图像识别和 LLM 文章摘要）
DASHSCOPE_API_KEY=your_api_key_here

# 微信公众号凭证（用于发布草稿）
WECHAT_APPID=your_appid_here
WECHAT_APPSECRET=your_appsecret_here

# API 模式凭证（用于文章采集）
WECHAT_API_TOKEN=your_token_here
WECHAT_API_COOKIE=your_cookie_here
```

**方式二：使用系统环境变量**

```bash
# macOS/Linux
export DASHSCOPE_API_KEY="your_api_key_here"

# Windows PowerShell
$env:DASHSCOPE_API_KEY="your_api_key_here"
```

**方式三：在 config.yaml 中直接配置**

详见下方配置文件说明（不推荐，容易泄露）。

### 配置文件

在 `configs/config.yaml` 中配置项目参数：

```yaml
# RPA 模式专用：目标日期（精确到天）
# 格式：YYYY-MM-DD
target_date: "2026-01-28"

# API 模式专用：时间范围配置（精确到分钟，v2.1.1 新增）
# 格式：YYYY-MM-DD HH:mm
start_date: "2026-01-28 00:00"
end_date: "2026-01-28 23:59"

# 公众号文章 URL（每个公众号提供一个文章链接，用于定位公众号，RPA 模式专用）
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
    api_key: null # 为 null 时自动读取（优先级：.env 文件 > 系统环境变量 DASHSCOPE_API_KEY）
    thinking_budget: 1024
    enable_thinking: true
  VLM:
    model: qwen3-vl-plus
    api_key: null
    thinking_budget: 1024
    enable_thinking: true

# API 模式配置（v2.0.0 新增）
api_config:
  cookie: "your_cookie_here" # 从浏览器获取
  token: "your_token_here" # 从浏览器获取
  account_names: # 要采集的公众号名称列表
    - 机器之心
    - 量子位
```

### 运行主程序

命令行支持完整的「采集 → 生成 → 发布」工作流，提供 RPA 和 API 两种采集模式。

#### 一键全流程（推荐）

```bash
# RPA 模式运行（需要微信客户端）
uv run main.py --mode rpa --workflow full

# API 模式运行（推荐，无需微信客户端）
uv run main.py --mode api --workflow full

# 简写形式（--workflow full 是默认值，可省略）
uv run main.py --mode rpa
uv run main.py --mode api
```

#### 分步执行

```bash
# 步骤1：仅采集文章
uv run main.py --mode rpa --workflow collect   # RPA 模式
uv run main.py --mode api --workflow collect   # API 模式

# 步骤2：仅生成公众号文章内容（自动查找当天的文章列表文件）
uv run main.py --workflow generate
# 或指定文件
uv run main.py --workflow generate --markdown-file output/articles_20260126.md

# 步骤3：仅发布草稿（自动查找当天的公众号文章内容 HTML 文件）
uv run main.py --workflow publish
# 或指定文件
uv run main.py --workflow publish --html-file output/daily_rich_text_20260126.html
```

#### 命令行参数说明

| 参数              | 可选值                                   | 默认值   | 说明                                                                                   |
| ----------------- | ---------------------------------------- | -------- | -------------------------------------------------------------------------------------- |
| `--mode`          | `rpa`, `api`                             | `rpa`    | 采集模式。`rpa`：GUI 自动化 + VLM 识别；`api`：微信公众平台后台接口（推荐）            |
| `--workflow`      | `collect`, `generate`, `publish`, `full` | `full`   | 工作流类型。`collect`：仅采集；`generate`：仅生成；`publish`：仅发布；`full`：完整流程 |
| `--markdown-file` | 文件路径                                 | 自动查找 | 指定已有的文章列表文件（用于 `generate` 或 `publish` 工作流）                          |
| `--html-file`     | 文件路径                                 | 自动查找 | 指定已有的公众号文章内容 HTML 文件（用于 `publish` 工作流）                            |

#### 桌面客户端

```bash
# 图形界面方式运行
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
├── utils/                   # 工具模块
│   ├── wechat/              # 微信相关工具（v2.0.0 模块化拆分）
│   │   ├── __init__.py
│   │   ├── process.py       # 微信进程管理和窗口控制
│   │   ├── base_client.py   # API 客户端基类
│   │   ├── article_client.py  # 文章采集 API 客户端（v2.0.0 新增）
│   │   ├── publish_client.py  # 草稿发布 API 客户端
│   │   └── exceptions.py    # 微信 API 异常类
│   ├── autogui.py           # GUI 自动化操作（键盘、鼠标、截图、点击）
│   ├── vlm.py               # 视觉语言模型（VLM）图像识别
│   ├── llm.py               # LLM 调用工具（文章摘要生成）
│   ├── types.py             # 数据类型定义（ArticleMetadata, ArticleSummary）
│   ├── paths.py             # 路径管理工具（项目根目录、输出目录等）
│   └── env_loader.py        # 环境变量加载工具（.env 文件支持）
├── workflows/               # 工作流模块
│   ├── base.py              # 工作流抽象基类
│   ├── rpa_article_collector.py  # RPA 模式文章收集器（异步工作流）
│   ├── api_article_collector.py  # API 模式文章收集器（v2.0.0 新增）
│   ├── daily_generate.py    # 公众号文章内容生成器
│   └── daily_publish.py     # 微信公众号自动发布工作流

gui/                         # 桌面客户端模块（PyQt6）
├── main_window.py           # 主窗口
├── theme_manager.py         # 主题管理器（v2.0.0 新增，支持深色/浅色主题切换）
├── styles.py                # 样式定义
├── panels/                  # UI 面板组件
│   ├── config_panel.py      # 配置面板（日期、链接、API Key）
│   ├── progress_panel.py    # 进度面板（状态、进度条）
│   └── log_panel.py         # 日志面板（实时日志显示）
├── workers/                 # 后台工作线程
│   └── workflow_worker.py   # 工作流执行器（在后台线程运行）
└── utils/                   # 客户端工具类
    ├── config_manager.py    # 配置管理器（读写 config.yaml）
    └── log_handler.py       # 日志处理器（重定向到 UI）

templates/                   # 模板文件目录
├── search_website_mac.png   # macOS "访问网页"按钮模板
├── three_dots_mac.png       # macOS 三个点菜单按钮模板
├── turnback_mac.png         # macOS 返回按钮模板
├── search_website.png       # Windows "访问网页"按钮模板
├── three_dots.png           # Windows 三个点菜单按钮模板
├── turnback.png             # Windows 返回按钮模板
├── rich_text_template.html  # 富文本 HTML 模板（用于生成公众号文章内容）
├── default_cover.png        # 默认封面图片（文章无封面时使用）
└── README_cover.md          # 封面图片使用说明

docs/                        # 英文文档目录
├── README_en.md             # 英文版 README
└── CHANGELOG_en.md          # 英文版更新日志

scripts/                     # 构建脚本目录
├── build_macos.sh           # macOS 应用打包脚本
└── build_windows.bat        # Windows 应用打包脚本

output/                      # 输出目录（自动创建）
├── articles_YYYYMMDD.md           # 采集到的文章链接列表
└── daily_rich_text_YYYYMMDD.html  # 生成的富文本内容

main.py                      # 命令行入口（支持完整工作流）
app.py                       # 桌面客户端入口
```

### 关键技术组件

1. **微信进程管理** (`utils/wechat/process.py`)
   - 跨平台支持（Windows 使用 tasklist/PowerShell，macOS 使用 pgrep/osascript）
   - 检查微信是否运行：`is_wechat_running(os_name)`
   - 激活微信窗口到前台：`activate_wechat_window(os_name)`

2. **微信公众号 API 客户端** (`utils/wechat/`)
   - `PublishClient` 类：微信公众号官方 API 客户端（用于发布）
     - `get_access_token()`: 获取并缓存 access_token（使用稳定版接口）
     - `create_draft()`: 创建草稿
     - `publish_draft()`: 发布草稿
     - `upload_media()`: 上传永久素材
   - `ArticleClient` 类：微信公众平台后台 API 客户端（v2.0.0 新增，用于采集）
     - `search_account()`: 搜索公众号，获取 fakeid
     - `get_article_list()`: 获取文章列表
     - `get_all_articles()`: 分页获取所有文章
     - `get_articles_by_date()`: 获取指定日期的文章

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
   - `get_dates_location_from_img(vlm_client, img_path, dates)`: 识别图片中指定日期的位置
   - 返回相对坐标（0-1 范围），支持多个匹配位置
   - 内置重试机制和 XML 格式解析校验
   - 用于自动识别公众号页面中的文章日期位置

5. **RPA 模式工作流** (`workflows/rpa_article_collector.py`)
   - `RPAArticleCollector`: RPA 模式文章收集器类（异步工作流）
   - 自动打开/激活微信应用
   - `build_workflow()`: 异步方法，执行完整的文章采集流程
   - `run()`: 同步入口方法，使用 asyncio.run() 调用 build_workflow()
   - 支持多公众号批量采集，自动去重，错误恢复

6. **API 模式工作流** (`workflows/api_article_collector.py`)（v2.0.0 新增）
   - `APIArticleCollector`: API 模式文章收集器类（同步工作流）
   - 通过微信公众平台后台接口获取文章列表
   - `build_workflow()`: 执行完整的文章采集流程
   - `run()`: 同步入口方法
   - 支持按公众号名称搜索，按日期筛选文章
   - 输出格式与 RPA 模式兼容，可直接用于 DailyGenerator

7. **数据类型定义** (`utils/types.py`)
   - `ArticleMetadata`: 公众号文章元数据（标题、作者、发布时间、正文、图片等）
   - `ArticleSummary`: 文章分析结果（评分、内容速览、精选理由）
   - 使用 Pydantic BaseModel，便于 JSON 序列化和与大模型框架集成

8. **路径管理工具** (`utils/paths.py`)
   - 提供项目路径获取函数，兼容 PyInstaller 打包环境
   - `get_project_root()`: 获取项目根目录
   - `get_output_dir()`: 获取输出目录
   - `get_templates_dir()`: 获取模板目录
   - `get_configs_dir()`: 获取配置目录
   - 支持开发环境和打包后环境的路径自动切换

9. **LLM 调用工具** (`utils/llm.py`)
   - `generate_article_summary()`: 异步函数，使用大模型生成内容速览、推荐度评分和精选理由
   - `extract_json_from_response()`: 从大模型响应中提取 JSON 字符串
   - 内置重试机制，保持对话上下文让模型修正输出格式

10. **公众号文章内容生成器** (`workflows/daily_generate.py`)
    - `DailyGenerator`: 公众号文章内容生成器类
    - 解析采集器生成的文章链接 Markdown 文件
    - 获取文章 HTML 并提取元数据（标题、作者、正文、图片等）
    - 使用 BeautifulSoup 解析 HTML，提取 JavaScript 变量区的元数据
    - 使用 LLM 为每篇文章生成内容速览（100-200字）、推荐度评分（0-5星）和精选理由（100字以内）
    - 筛选高分文章（3星及以上或前3篇）生成富文本 HTML
    - 输出文件保存到 `output/daily_rich_text_YYYYMMDD.html`

11. **桌面客户端** (`gui/`)

- `MainWindow`: 主窗口类，整合所有面板组件，支持3步工作流（采集 → 生成 → 发布）
- `ThemeManager`: 主题管理器（v2.0.0 新增），支持深色/浅色主题切换
- `ConfigPanel`: 配置面板，管理日期选择、采集模式、敏感数据保存方式、API/RPA 配置、模型配置、发布配置
- 支持统一的敏感数据保存方式选择（.env 文件或 config.yaml）（v2.1.1 新增）
- 显示配置来源状态（config.yaml / .env 文件 / 系统环境变量）（v2.1.1 新增）
- 支持直接打开 .env 文件编辑（v2.1.1 新增）
  - `ProgressPanel`: 进度面板，显示执行状态和进度条
  - `LogPanel`: 日志面板，实时显示运行日志
  - `WorkflowWorker`: 后台工作线程，支持4种工作流类型（`WorkflowType` 枚举）：
    - `COLLECT`：仅采集文章
    - `GENERATE`：仅生成公众号文章内容
    - `PUBLISH`：仅发布草稿
    - `FULL`：完整流程（采集 + 生成 + 发布）
  - `ConfigManager`: 配置管理器，读写 config.yaml，支持发布配置管理和凭证来源状态检测
  - `QTextEditLogHandler`: 日志处理器，将 logging 日志重定向到 Qt 信号
  - 入口文件：`app.py`

11. **环境变量加载工具** (`utils/env_loader.py`)
    - `load_env()`: 加载 .env 文件中的环境变量
    - `get_env()`: 获取环境变量值
    - `has_env()`: 检查环境变量是否存在
    - `diagnose_env()`: 诊断环境变量配置情况
    - 配置优先级：config.yaml > .env 文件 > 系统环境变量

12. **.env 文件管理器** (`gui/utils/env_file_manager.py`)（v2.1.1 新增）
    - `EnvFileManager`: .env 文件读写管理类
    - `update()`: 更新单个环境变量
    - `create()`: 创建 .env 文件
    - `remove()`: 删除环境变量
    - `detect_source()`: 检测配置来源
    - 保留文件中的注释和格式

13. **工作流基类** (`workflows/base.py`)
    - `BaseWorkflow`: 抽象基类，定义工作流统一接口
    - `build_workflow()`: 抽象方法，构建工作流
    - `run()`: 抽象方法，运行工作流

14. **微信公众号自动发布** (`workflows/daily_publish.py`)
    - `DailyPublisher`: 自动发布工作流类
    - `_html_to_wechat_format()`: HTML 转换为微信公众号格式
    - `_upload_cover_img()`: 上传封面图片并缓存 media_id
    - `_create_draft()`: 创建公众号草稿
    - `build_workflow()`: 基于 HTML 文件创建草稿
    - 支持从 config.yaml、.env 文件或系统环境变量读取 AppID/AppSecret
    - 配置优先级：config.yaml > .env 文件 > 系统环境变量

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

`templates/rich_text_template.html` 用于生成微信公众号文章内容的富文本内容：

- 使用特殊注释标记分隔模板片段：`<!-- ===== XXX_START ===== -->` 和 `<!-- ===== XXX_END ===== -->`
- 模板片段包括：HEADER（文档头）、ARTICLE_CARD（文章卡片）、SEPARATOR（分隔符）、FOOTER（底部）
- 文章卡片占位符：
  - `{title}`: 文章标题
  - `{article_url}`: 文章链接
  - `{cover_url}`: 封面图片链接
  - `{summary}`: 内容速览（100-200字）
  - `{score}`: 推荐度评分（0-5星）
  - `{reason}`: 精选理由（100字以内）
- 底部署名：自动添加 "以上内容由 Double童发发 开发的 wechat-ai-daily 自动生成"

### 异步工作流架构

- `RPAArticleCollector.build_workflow()` 与 `DailyGenerator.build_workflow()` 为异步方法（`async def`），需要在异步环境中 `await`
- `APIArticleCollector.build_workflow()` 与 `DailyPublisher.build_workflow()` 为同步方法
- 命令行入口使用 `asyncio.run(main())` 统一调度异步与同步流程
- 在编写新功能时，涉及 VLM 识别的流程必须使用异步函数封装

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

#### RPA 模式文章采集流程

完整的 RPA 模式文章采集流程：

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

#### API 模式文章采集流程（v2.0.0 新增）

完整的 API 模式文章采集流程：

1. 从配置文件读取 cookie、token 和公众号名称列表
2. 对每个公众号：
   - 调用 `/cgi-bin/searchbiz` 接口搜索公众号，获取 fakeid
   - 调用 `/cgi-bin/appmsg` 接口获取文章列表
   - 按目标日期筛选文章
3. 合并所有文章并去重
4. 保存采集结果到 Markdown 文件（格式与 RPA 模式兼容）

### 公众号文章内容生成工作流

完整的公众号文章内容生成流程（`DailyGenerator.build_workflow()`）：

1. 从 Markdown 文件中解析文章链接列表
2. 对每篇文章：
   - 获取文章 HTML 内容
   - 提取元数据（标题、作者、发布时间、封面图、正文等）
3. 使用 LLM 为每篇文章生成内容速览、评分和精选理由
4. 按评分降序排列所有文章
5. 筛选推荐文章（3星及以上，或不足时取前3篇）
6. 使用富文本模板生成 HTML 内容
7. 保存到 `output/daily_rich_text_YYYYMMDD.html`
