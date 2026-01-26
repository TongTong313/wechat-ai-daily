# 更新日志

本文档记录了本项目的所有重要变更。

## v1.2.0 - 2026-01-26

新增微信公众号自动发布功能，支持通过官方 API 自动创建草稿，优化环境变量管理。

### 新增功能

- **微信公众号自动发布**（`workflows/daily_publish.py`）
  - `DailyPublisher` 工作流：基于微信官方 API 自动创建公众号草稿
  - HTML 富文本自动转换为微信公众号支持的格式
  - 封面图片自动上传并缓存 media_id，避免重复上传
  - 支持配置作者、摘要等草稿信息

- **微信公众号 API 客户端**（`utils/wechat.py` 新增 `WeChatAPI` 类）
  - access_token 自动获取和缓存（使用稳定版接口，无需 IP 白名单）
  - 草稿管理：创建、获取、更新、删除、列表
  - 发布管理：发布草稿、查询发布状态、删除已发布文章
  - 素材管理：上传永久素材、上传图文消息内图片

- **环境变量管理优化**
  - 新增 `.env` 文件支持（`utils/env_loader.py`）
  - 配置优先级：config.yaml > 系统环境变量 > .env 文件
  - 新增 `.env.example` 模板文件
  - 新增 `tests/diagnose_env.py` 环境诊断脚本

- **工作流架构优化**
  - 新增 `BaseWorkflow` 抽象基类（`workflows/base.py`）
  - 统一工作流接口：`build_workflow()` 和 `run()`

- **桌面客户端增强**（`gui/` 模块）
  - 主窗口新增第三步"发布草稿"功能，完整流程变为：采集 → 生成 → 发布
  - 一键全流程按钮现支持完整的3阶段自动执行
  - 新增 HTML 文件选择器，支持选择已生成的日报进行发布
  - 操作按钮区改为可滚动区域，适配更多操作选项
  - `WorkflowWorker` 新增 `WorkflowType` 枚举，支持4种工作流类型：
    - `COLLECT`：仅采集文章
    - `GENERATE`：仅生成日报
    - `PUBLISH`：仅发布草稿
    - `FULL`：完整流程（采集 + 生成 + 发布）
  - `ConfigPanel` 新增发布配置卡片，支持配置 AppID、AppSecret、作者名、封面图片、默认标题
  - `ConfigManager` 新增发布配置管理方法，支持凭证来源状态显示

### 配置更新

- `config.yaml` 新增 `publish_config` 配置项：
  - `appid`：公众号 AppID（支持环境变量 WECHAT_APPID）
  - `appsecret`：公众号 AppSecret（支持环境变量 WECHAT_APPSECRET）
  - `cover_path`：封面图片路径
  - `media_id`：封面图片 media_id（自动缓存）
  - `author`：作者名称

### 依赖更新

- 新增 `python-dotenv>=1.2.1`：.env 文件加载
- 新增 `ruamel-yaml>=0.18.0`：保留 YAML 注释的配置文件读写

### 测试更新

- 新增 `tests/test_daily_publish.py`：自动发布工作流测试
- 新增 `tests/diagnose_env.py`：环境变量诊断工具
- 清理过时测试文件

## v1.1.0 - 2026-01-25

增强桌面客户端体验，提供完整的图形界面应用和可执行文件打包支持。

### 新增功能

- **PyQt6 桌面客户端**（`app.py` 和 `gui/` 模块）
  - 主窗口界面（MainWindow）：整合配置、进度、日志三大面板
  - 配置面板（ConfigPanel）：
    - 日期选择器（今天/昨天/自定义日期）
    - 文章链接管理（添加/删除/从配置文件加载）
    - API Key 设置（支持保存到配置文件）
  - 进度面板（ProgressPanel）：
    - 实时状态显示（就绪/运行中/已完成/失败）
    - 进度条反馈
  - 日志面板（LogPanel）：
    - 实时日志输出（自动滚动）
    - 日志级别过滤
  - 后台工作线程（WorkflowWorker）：避免 UI 阻塞

- **可执行文件打包支持**
  - Windows 打包脚本（`scripts/build_windows.bat`）
    - 自动检测并安装 pyinstaller
    - 一键生成 `dist/微信AI日报助手.exe`
  - macOS 打包脚本（`scripts/build_macos.sh`）
    - 自动检测并安装 pyinstaller
    - 一键生成 `dist/微信AI日报助手.app`
  - 打包后无需 Python 环境即可运行

- **配置管理优化**
  - ConfigManager 类：统一管理配置文件读写
  - 自动根据操作系统选择 GUI 模板路径（Windows/macOS）
  - 支持从 GUI 界面保存配置到 `configs/config.yaml`

- **日志处理增强**
  - QTextEditLogHandler：将 logging 日志重定向到 Qt 信号
  - 支持实时日志显示和自动滚动

### 改进优化

- 优化工作流执行逻辑，支持在后台线程中运行
- 改进错误处理和用户提示
- 增强跨平台兼容性

### 文档更新

- 更新 README.md 和 docs/README_en.md，添加桌面客户端使用说明
- 更新 CLAUDE.md，添加 GUI 模块架构说明
- 添加打包脚本使用文档

## v1.0.0 - 2026-01-25

正式开源发布，实现了微信公众号文章自动化收集和每日 AI 内容日报生成的完整工作流。

### 新增功能

- **GUI 自动化采集**：支持自动打开微信、搜索公众号、采集文章链接
  - 基于模板图片匹配实现精准点击操作
  - 支持页面滚动和截图功能
  - 自动检测并激活微信窗口

- **VLM 智能识别**：集成阿里云 DashScope 视觉语言模型
  - 自动识别公众号页面中的日期位置，精准定位当日文章
  - 自动处理高分辨率显示屏缩放（Retina 等）

- **LLM 内容分析**：集成阿里云 DashScope 大语言模型
  - 自动提取文章元数据（标题、作者、发布时间、正文、图片等）
  - 生成 100-200 字的内容速览
  - 评估文章推荐度（0-100 分）
  - 生成不超过 100 字的精选理由

- **每日日报生成**：自动生成富文本格式的 HTML 日报
  - 自动采集指定公众号当日发布的所有文章
  - 按评分筛选优质文章（90 分以上或前 3 篇）
  - 支持一键复制粘贴到公众号编辑器
  - 支持自定义 HTML 模板

- **跨平台支持**：同时支持 Windows 和 macOS 系统
  - 自动检测操作系统类型
  - 支持平台特定的模板图片配置

### 配置功能

- 支持 YAML 配置文件（`configs/config.yaml`）
- 支持环境变量配置（DASHSCOPE_API_KEY）
- 支持自定义模板图片路径
- 支持模型参数配置（model、thinking_budget、enable_thinking 等）

### 文档更新

- 中英文双语 README（`README.md` 和 `docs/README_en.md`）
- 开发者指南（`CLAUDE.md`）
