# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Claude code 智能体执行规则

- 始终使用中文与我交流
- 严格遵循我的指示，在没有让你生成或修改代码文件的时候，你不允许修改文件内容
- 在指明修改部分文件时，请只修改我指定的部分，如果你发现其他需要修改的部分，**必须**先征求我的同意，我同意后方可修改
- 尽量避免生成 markdown、txt、docs 等格式的文档，除非我明确要求生成这些格式的文档
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
```

## 项目架构

### 核心模块结构

```
src/wechat_ai_daily/
├── utils/          # 工具模块
│   ├── extractors.py   # 网页数据提取（biz 参数、文章列表）
│   ├── wechat.py       # 微信进程管理和窗口控制
│   └── autogui.py      # GUI 自动化操作（键盘控制）
├── workflows/      # 工作流模块
│   └── wechat_autogui.py  # 微信公众号文章收集器
└── llm/           # LLM 模块（预留）
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
   - `press_keys(*keys)`: 支持组合键操作（如 ctrl+v）

4. **工作流编排** (`workflows/wechat_autogui.py`)
   - `OfficialAccountArticleCollector`: 公众号文章收集器类
   - 自动打开/激活微信应用
   - 预留 `build_workflow()` 和 `run()` 方法用于工作流构建

### 平台兼容性

项目支持 Windows 和 macOS，通过 `sys.platform` 检测操作系统：

- `win32`: Windows 平台
- `darwin`: macOS 平台

不同平台使用不同的系统命令：

- Windows: tasklist, PowerShell, cmd
- macOS: pgrep, osascript, open

## 技术依赖

- **pyautogui**: GUI 自动化框架
- **pynput**: 键盘和鼠标控制
- **requests**: HTTP 请求库

## 开发注意事项

### 微信自动化限制

- 微信公众号文章列表获取受到严格的反爬虫限制
- 仅模拟 User-Agent 不足以绕过验证
- 可能需要结合 GUI 自动化和网络请求的混合方案

### 日志记录

项目使用 Python 标准 logging 模块，关键操作都有日志输出。

### 测试文件调试

`tests/test_tt.py` 中的测试会生成 `response_debug.html` 文件用于调试网络请求响应。
