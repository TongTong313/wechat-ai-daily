# CLAUDE.md

本文件为 Claude Code 提供项目开发指导规范。

## 项目概述

微信公众号文章自动化收集工具，提供两种采集方案：

- **RPA 模式**：GUI 自动化 + VLM 图像识别
- **API 模式**：微信公众平台后台接口（推荐）

## 法律合规

> 详见 `README.md` 和 `LICENSE` 中的法律声明

开发规范要点：

- 仅供个人学习研究，禁止商业用途
- 不绕过反爬虫机制，不添加高频请求/批量账号功能
- 新增功能需评估法律风险并更新声明

## 开发环境

- 包管理器：**uv**（非 pip）
- 安装依赖：`uv sync`
- 运行测试：`uv run python -m pytest tests/`
- 配置文件：`configs/config.yaml`
- 环境变量：`.env` 文件（推荐）或系统环境变量
- 配置优先级：config.yaml > .env > 系统环境变量

## 常用命令

```bash
# 完整工作流
uv run main.py --mode api --workflow full

# 分步执行
uv run main.py --mode api --workflow collect   # 采集
uv run main.py --workflow generate             # 生成
uv run main.py --workflow publish              # 发布

# 桌面客户端
uv run app.py

# Web 控制台
uv run web_app.py
```

## 项目结构

```
src/wechat_ai_daily/
├── utils/                    # 工具模块
│   ├── wechat/               # 微信 API 客户端
│   ├── autogui.py            # GUI 自动化
│   ├── vlm.py                # VLM 图像识别
│   ├── llm.py                # LLM 摘要生成
│   ├── types.py              # 数据类型定义
│   └── paths.py              # 路径管理
├── workflows/                # 工作流模块
│   ├── rpa_article_collector.py   # RPA 采集（异步）
│   ├── api_article_collector.py   # API 采集（同步）
│   ├── daily_generate.py          # 内容生成（异步）
│   └── daily_publish.py           # 草稿发布（同步）

apps/desktop/                 # 桌面客户端（PyQt6）
apps/web/                     # Web 控制台（FastAPI + 前端）
templates/                    # 模板文件（GUI 按钮图片、HTML 模板）
configs/                      # 配置文件
output/                       # 输出目录
```

## 开发注意事项

### 异步工作流

- `RPAArticleCollector` 和 `DailyGenerator` 的 `build_workflow()` 是异步方法
- `APIArticleCollector` 和 `DailyPublisher` 的 `build_workflow()` 是同步方法
- 涉及 VLM 识别的流程必须使用异步函数

### 屏幕坐标

- VLM 返回相对坐标（0-1），需转换为物理像素再转逻辑坐标
- 高分屏缩放已在 `autogui.py` 中处理

### 模板图片

- 位于 `templates/` 目录，用于 GUI 自动化按钮匹配
- 界面变化时需重新截图更新

### 富文本模板

- 位于 `templates/rich_text_template.html`
- 使用 `<!-- ===== XXX_START/END ===== -->` 标记分隔片段

## 智能体执行规则

### 基本要求

- 始终使用**中文**交流
- 使用 **uv** 管理 Python 环境（`uv run`、`uv add` 等）

### 修改权限（核心）

- 生成方案/计划/设计时，**禁止**直接修改代码或文件，必须先征求同意
- 未明确要求修改时，**禁止**修改任何文件
- 指定修改部分文件时，只改指定部分；发现其他需改处必须先确认
- **每次**修改代码后，必须检查 README/CHANGELOG/CLAUDE 等文档是否需更新，需更新时先确认

### 代码质量

- 包含详尽的**中文注释**
- 简练易读，**拒绝过度设计**

### 沟通原则

- 有疑问必须先讨论确认
- 未明确要求时，**禁止**生成 markdown/txt/docs 等文档
