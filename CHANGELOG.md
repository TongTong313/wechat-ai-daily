# 更新日志

本文档记录了本项目的所有重要变更。

## v2.2.0 - 2026-01-30

大版本更新：新增 Web 控制台，统一应用层结构，完善版本与文档标识。

### 新增功能

- **Web 控制台**（`apps/web/` / `web_app.py`）
  - FastAPI 提供配置与工作流控制 API
  - WebSocket 实时日志与进度推送
  - 原生前端页面与静态资源

### 工程调整

- **应用层结构统一**（`apps/desktop/` + `apps/web/`）
  - 桌面端从 `gui/` 迁移至 `apps/desktop/`
  - Web 端入口独立为 `web_app.py`
- **遗留目录清理**：移除旧 `gui/` 目录（缓存文件）

### 体验优化

- **桌面端日志命名**（`apps/desktop/main_window.py`）
  - GUI 日志统一为 `logs/desktop.log`

### 文档更新

- **README / CHANGELOG / CLAUDE**：补充 Web 控制台与新目录结构说明

---

## v2.1.1 - 2026-01-30

小版本更新：完善 API 模式时间范围体验，优化富文本发布稳定性与 GUI 交互。

### 功能增强

- **命令行时间范围参数**（`main.py`）

  - 新增 `--start-date` / `--end-date`，支持 API 模式按分钟筛选
  - 支持 `YYYY-MM-DD` 与 `YYYY-MM-DD HH:mm` 两种格式，自动补齐时间并校验范围

- **富文本标准化与间距稳定性**（`utils/wechat/html_normalizer.py` / `workflows/daily_generate.py` / `workflows/daily_publish.py`）
  - 统一清理空白节点并重置块级 margin/padding，避免发布时空行/间距异常
  - 分隔符追加唯一标识，避免微信接口合并导致间距丢失
  - API 模式生成的 HTML 文件名包含时间范围

### 体验优化

- **输出文件列表刷新**（`gui/main_window.py`）
  - 下拉框展开与窗口激活时自动刷新，保证外部生成文件可见

### 生成逻辑优化

- **文章筛选与摘要日志**（`workflows/daily_generate.py`）
  - API 模式按时间范围过滤文章，日志显示摘要生成进度
  - 评分规则细化，补充不切实际与营销内容的扣分项

---

## v2.1.0 - 2026-01-29

**功能增强**：API 模式支持精确到分钟的时间范围筛选，提升文章采集的灵活性。

### 新增功能

- **API 模式时间范围筛选**（`workflows/api_article_collector.py`）

  - 新增 `start_date` 和 `end_date` 配置项，支持精确到分钟的时间范围
  - 配置格式：`YYYY-MM-DD HH:mm`（如 `2026-01-28 08:00`）
  - 输出文件命名格式更新为 `articles_YYYYMMDD_HHmm_YYYYMMDD_HHmm.md`

- **ArticleClient 新增方法**（`utils/wechat/article_client.py`）

  - `get_articles_by_range()`: 按时间范围获取文章，使用时间戳精确比较

- **GUI 时间范围选择器**（`gui/panels/config_panel.py`）
  - API 模式：显示开始时间和结束时间选择器（日期 + 时间）
  - RPA 模式：保持原有的单日期选择器
  - 新增「今天全天」和「昨天全天」快捷按钮

### 配置变更

- **config.yaml 新增配置项**：
  - `start_date`: API 模式开始时间（格式：`YYYY-MM-DD HH:mm`）
  - `end_date`: API 模式结束时间（格式：`YYYY-MM-DD HH:mm`）
  - `target_date`: 仅用于 RPA 模式（格式：`YYYY-MM-DD`）

### 文档更新

- **README.md**：更新采集时间配置说明，区分 RPA 和 API 模式
- **CLAUDE.md**：更新配置文件说明和工作流描述
- **测试用例**：更新 `test_api_full_workflow.py` 以使用新的时间范围配置

---

## v2.0.1 - 2026-01-29

小版本更新：修复启动路径问题，优化文章评分逻辑。

### Bug 修复

- **桌面客户端启动路径修复**（`app.py`）
  - 修复从非应用目录启动时相对路径失效的问题
  - 修复日志文件路径使用相对路径导致的写入失败问题

### 功能优化

- **文章评分规则重构**（`workflows/daily_generate.py`）

  - 采用更清晰的「基本得分点 + 加分项 + 扣分项」评分结构
  - 基本得分点（最高 3 分）：AI 领域干货、内容质量、实用价值
  - 额外加分项：知名机构/人物、热点话题
  - 额外扣分项：非 AI 内容、AI 生成痕迹、营销软文
  - 整体通过率控制在 50%以内，提升推荐质量

- **LLM 配置优化**
  - 文本模型选项精简为 `qwen-plus` 和 `qwen3-max`
  - `enable_thinking` 默认值改为 `False`，提升生成速度

### 文档修正

- **`.env.example`**：修正配置优先级说明，明确 .env 文件优先于系统环境变量

---

## v2.0.0 - 2026-01-27

**重大更新**：新增 API 模式文章采集，提供 RPA 和 API 两种采集方案，命令行支持完整的采集 → 生成 → 发布工作流，全面优化敏感数据配置管理。

### 新增功能

- **API 模式文章采集**（`workflows/api_article_collector.py`）

  - `APIArticleCollector` 工作流：通过微信公众平台后台接口获取文章列表
  - 相比 RPA 模式更高效、更稳定
  - 支持按公众号名称搜索，无需提供文章 URL
  - 支持按日期筛选文章

- **微信公众平台 API 客户端**（`utils/wechat/article_client.py`）

  - `ArticleClient` 类：微信公众平台后台 API 客户端
  - `search_account()`: 搜索公众号，获取 fakeid
  - `get_article_list()`: 获取文章列表
  - `get_all_articles()`: 分页获取所有文章
  - `get_articles_by_date()`: 获取指定日期的文章

- **命令行完整工作流支持**（`main.py`）

  - 支持 RPA 和 API 两种采集模式（`--mode rpa/api`）
  - 支持四种工作流类型（`--workflow collect/generate/publish/full`）
    - `collect`：仅采集文章
    - `generate`：仅生成公众号文章内容
    - `publish`：仅发布草稿
    - `full`：完整流程（采集 → 生成 → 发布）
  - 支持指定已有文件（`--markdown-file`、`--html-file`）
  - 自动查找当天的中间输出文件
  - 与桌面客户端功能保持一致

- **数据类型优化**（`utils/types.py`）

  - `ArticleMetadata` 支持渐进式填充（API 第一阶段 + HTML 解析第二阶段）
  - 新增 `AccountMetadata` 公众号信息数据类
  - 新增 `from_api_response()` 工厂方法

- **敏感数据统一管理**（GUI 客户端）

  - 新增"敏感数据保存方式"全局设置卡片
  - 提供"保存到 .env 文件（推荐）"和"保存到 config.yaml"两个选项
  - 统一管理所有敏感数据的保存行为
  - 添加"打开 .env 文件"按钮，方便直接编辑

- **.env 文件管理器**（`gui/utils/env_file_manager.py`）
  - `EnvFileManager` 类：完整的 .env 文件读写功能
  - 支持保留注释和格式
  - 提供 `update()`, `create()`, `remove()`, `detect_source()` 等方法
  - 自动检测配置来源（config.yaml / .env 文件 / 系统环境变量）

### 功能优化

- **配置优先级调整**（破坏性变更）

  - **新的敏感信息配置优先级**（从高到低）：
    1. **config.yaml 文件**（最高优先级）
    2. **.env 文件**（推荐，自动添加到 .gitignore）
    3. **系统环境变量**（最低优先级）
  - **注意**：config.yaml 中值为 null 或空字符串时，视为未设置，会读取环境变量
  - **影响范围**：所有敏感配置（API Key、Token、Cookie、AppID、AppSecret）

- **数据类型系统增强**（`utils/types.py`）

  - `ArticleMetadata` 支持渐进式填充（API 第一阶段 + HTML 解析第二阶段）
  - 新增 `from_api_response()` 工厂方法，简化数据创建流程
  - 优化数据验证和序列化逻辑

- **公众号文章内容生成器兼容性优化**（`workflows/daily_generate.py`）

  - `DailyGenerator` 同时兼容 RPA 和 API 两种采集器的输出格式
  - 优化文章元数据提取逻辑，提升解析准确性
  - 改进错误处理机制，增强容错能力

- **GUI 主题系统**（`gui/theme_manager.py`）

  - 新增主题管理器，支持深色/浅色主题动态切换
  - 优化界面配色方案，提升用户体验
  - 支持主题配置持久化

- **路径管理优化**（`utils/paths.py`）

  - 统一项目路径获取逻辑，兼容 PyInstaller 打包环境
  - 自动处理开发环境和打包后环境的路径差异
  - 提供 `get_project_root()`、`get_output_dir()` 等便捷方法

- **命令行工作流优化**（`main.py`）

  - 优化参数解析逻辑，支持更灵活的工作流组合
  - 改进文件自动查找机制，智能匹配当天的中间输出文件
  - 增强错误提示和用户引导信息

- **代码结构重构**
  - 模块化拆分 `utils/wechat.py`，提升代码可维护性
  - 统一异常处理机制（`utils/wechat/exceptions.py`）
  - 优化类继承结构，引入 `BaseClient` 基类

### 架构调整

- 原 `workflows/wechat_autogui.py` 中的 `ArticleCollector` 重命名为 `RPAArticleCollector`，移至 `workflows/rpa_article_collector.py`
- 新增 `workflows/api_article_collector.py`：`APIArticleCollector`（API 模式）
- `DailyGenerator` 同时兼容两种采集器的输出格式
- 原 `utils/wechat.py` 拆分为多个模块：
  - `utils/wechat/process.py`：微信进程管理
  - `utils/wechat/article_client.py`：文章采集 API 客户端
  - `utils/wechat/publish_client.py`：草稿发布 API 客户端
  - `utils/wechat/base_client.py`：API 客户端基类
  - `utils/wechat/exceptions.py`：微信 API 异常类
- 新增 `utils/paths.py`：路径管理工具，兼容 PyInstaller 打包环境
- 新增 `gui/theme_manager.py`：主题管理器，支持深色/浅色主题切换
- 新增 `gui/utils/env_file_manager.py`：.env 文件管理器，支持安全的环境变量管理

### 安全改进

- **防止环境变量泄露到配置文件**

  - 用户选择"保存到 .env 文件"模式时，敏感数据只会写入 .env 文件
  - config.yaml 中的敏感字段保持为 null
  - 避免误将环境变量的值提交到版本控制

- **配置来源可视化**
  - GUI 界面显示每个敏感数据的来源（config.yaml / .env 文件 / 系统环境变量）
  - 帮助用户了解当前使用的配置来源

### 文档更新

- **README.md / docs/README_en.md**

  - 更新命令行运行说明，添加所有参数说明
  - 新增「一键全流程」和「分步执行」使用示例
  - 新增「命令行参数说明」表格
  - 重构「工作流程」章节，详细说明三步流程
  - 明确标注命令行和桌面客户端的功能一致性
  - **更新配置优先级说明**：config.yaml > .env 文件 > 系统环境变量

- **CLAUDE.md**
  - 更新项目概述，添加双模式采集说明
  - 更新运行主程序章节，添加命令行参数说明
  - 更新核心模块结构，反映架构调整
  - 新增命令行完整工作流说明
  - **更新配置优先级说明**和环境变量管理说明

### 测试更新

- 新增 `tests/test_api_full_workflow.py`：API 模式完整工作流测试
- 新增 `tests/test_config_priority.py`：配置优先级和隐私保护测试（原 `test_config_privacy.py`）
- 删除 `tests/test_api_daily_workflow.py`、`tests/test_daily_generate_workflow.py`、`tests/test_daily_publish.py`：清理过时测试文件，统一测试结构

---

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
  - 一键全流程按钮现支持完整的 3 阶段自动执行
  - 新增 HTML 文件选择器，支持选择已生成的公众号文章内容进行发布
  - 操作按钮区改为可滚动区域，适配更多操作选项
  - `WorkflowWorker` 新增 `WorkflowType` 枚举，支持 4 种工作流类型：
    - `COLLECT`：仅采集文章
    - `GENERATE`：仅生成公众号文章内容
    - `PUBLISH`：仅发布草稿
    - `FULL`：完整流程（采集 + 生成 + 发布）
  - `ConfigPanel` 新增发布配置卡片，支持配置 AppID、AppSecret、作者名、封面图片、默认标题
  - `ConfigManager` 新增发布配置管理方法，支持凭证来源状态显示

### 功能优化

- **环境变量管理系统重构**（`utils/env_loader.py`）

  - 新增 `.env` 文件支持，简化环境配置流程
  - 实现配置优先级机制：config.yaml > 系统环境变量 > .env 文件
  - 新增 `diagnose_env()` 诊断功能，快速定位配置问题
  - 提供 `.env.example` 模板文件，降低配置门槛

- **工作流架构统一**（`workflows/base.py`）

  - 引入 `BaseWorkflow` 抽象基类，统一工作流接口
  - 规范 `build_workflow()` 和 `run()` 方法签名
  - 提升代码复用性和可扩展性

- **桌面客户端功能增强**（`gui/` 模块）

  - 主窗口新增第三步"发布草稿"功能，完整流程变为：采集 → 生成 → 发布
  - 一键全流程按钮支持完整的 3 阶段自动执行
  - 新增 HTML 文件选择器，支持选择已生成的公众号文章内容进行发布
  - 操作按钮区改为可滚动区域，适配更多操作选项
  - `ConfigPanel` 新增发布配置卡片，支持凭证来源状态显示
  - `ConfigManager` 优化配置管理逻辑，支持发布配置持久化

- **文章评分系统优化**

  - 推荐度评分从 0-100 分制改为 0-5 星制，更符合用户认知习惯
  - 优质文章筛选规则从"90 分以上"调整为"3 星及以上"
  - 优化评分算法，提升推荐准确性

- **公众号文章内容生成效果优化**

  - 改进内容速览生成逻辑，提升摘要质量
  - 优化精选理由生成，更准确地提炼文章价值
  - 调整富文本模板样式，提升视觉效果

- **公众号模板效果优化**（`templates/rich_text_template.html`）
  - 优化文章卡片布局，提升可读性
  - 改进封面图片显示效果
  - 调整字体大小和行间距，适配移动端阅读

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

### 功能优化

- **工作流执行逻辑优化**

  - 支持在后台线程中运行，避免 UI 阻塞
  - 引入 `WorkflowWorker` 线程类，实现异步执行
  - 优化进度反馈机制，实时更新执行状态

- **配置管理系统优化**（`gui/utils/config_manager.py`）

  - 新增 `ConfigManager` 类，统一管理配置文件读写
  - 自动根据操作系统选择 GUI 模板路径（Windows/macOS）
  - 支持从 GUI 界面保存配置到 `configs/config.yaml`
  - 优化配置验证逻辑，提前发现配置错误

- **日志处理系统增强**（`gui/utils/log_handler.py`）

  - 新增 `QTextEditLogHandler` 类，将 logging 日志重定向到 Qt 信号
  - 支持实时日志显示和自动滚动
  - 优化日志格式，提升可读性
  - 支持日志级别过滤

- **错误处理和用户提示改进**

  - 增强异常捕获机制，避免程序崩溃
  - 优化错误提示信息，提供更明确的解决方案
  - 改进用户引导流程，降低使用门槛

- **跨平台兼容性增强**
  - 优化 Windows 和 macOS 平台的路径处理
  - 改进操作系统检测逻辑
  - 统一不同平台的 GUI 模板配置方式

### 文档更新

- 更新 README.md 和 docs/README_en.md，添加桌面客户端使用说明
- 更新 CLAUDE.md，添加 GUI 模块架构说明
- 添加打包脚本使用文档

## v1.0.0 - 2026-01-25

正式开源发布，实现了微信公众号文章自动化收集和公众号文章内容生成的完整工作流。

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

- **公众号文章内容生成**：自动生成富文本格式的 HTML 内容

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
