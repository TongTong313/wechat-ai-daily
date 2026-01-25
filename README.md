# Wechat AI Daily

<div align="center">

[中文](README.md) | [English](docs/README_en.md)

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-Package%20Manager-blueviolet.svg)](https://github.com/astral-sh/uv)
[![DashScope](https://img.shields.io/badge/DashScope-VLM%20%26%20LLM-orange.svg)](https://dashscope.aliyun.com/)
[![Bilibili](https://img.shields.io/badge/Bilibili-Double童发发-ff69b4.svg)](https://space.bilibili.com/323109608)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**作者：Double童发发** · [B站主页](https://space.bilibili.com/323109608)

</div>

## 📖 项目简介

微信公众号文章自动化收集工具，通过 GUI 自动化和 VLM 图像识别技术，自动采集指定公众号的当日文章，并使用 LLM 生成每日 AI 内容日报。生成的 HTML 文件打开后可一键复制粘贴，直接形成公众号正文内容。

**拒绝爬虫**！！！由于微信公众号文章列表获取受到严格的反爬虫限制，传统的网络爬虫方案难以实现，或者很容易被封号。本项目采用 **GUI 自动化 + VLM 图像识别** 的混合方案，模拟真实用户操作，突破限制获取文章信息。

本项目使用了 AI Coding 技术辅助编程，在此感谢 [Claude Code](https://claude.ai/code)、[Cursor](https://cursor.com/) 等 AI Coding 工具。

## 🎯 核心特性

### v1.1.0：增强桌面客户端体验

- **PyQt6 桌面客户端**：全新的图形界面应用
  - 可视化配置管理（日期选择、链接管理、API Key 设置）
  - 实时日志显示和进度条反馈
  - 一键执行完整工作流
- **可执行文件打包**：支持打包为独立应用
  - Windows 一键打包脚本（build_windows.bat）
  - macOS 一键打包脚本（build_macos.sh）
  - 无需 Python 环境即可运行
- **配置管理优化**：自动根据操作系统选择 GUI 模板路径
- **GUI 自动化采集**：模拟真实用户操作，自动打开微信、搜索公众号、采集文章链接
- **VLM 智能识别**：使用视觉语言模型识别页面中的日期位置，精准定位当日文章
- **LLM 智能分析**：自动提取文章内容，使用大模型生成内容速览和推荐度评分
- **每日日报生成**：汇总所有文章，生成可直接发布的富文本日报
- **一键粘贴发布**：生成的 HTML 文件打开后复制粘贴即可形成公众号正文
- **跨平台支持**：同时支持 Windows 和 macOS 系统

## 📋 环境要求

- Python >= 3.13
- 微信桌面客户端（Windows 或 macOS）
- 阿里云 DashScope API Key（用于 VLM 图像识别和 LLM 摘要生成）
- 仅支持 Windows 和 macOS 系统

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/TongTong313/wechat-ai-daily.git
cd wechat-ai-daily
```

### 2. 安装依赖

```bash
# 使用 uv 安装依赖（推荐）
uv sync
```

### 3. 配置 config.yaml 文件

根据实际情况编辑 `configs/config.yaml` 文件，主要包括：

#### 配置目标日期：

**注意事项**：请根据实际情况配置目标日期，也即**你要采集哪一天的文章，就配置哪一天**，如果配置为 null 或 "today" 表示当天, "yesterday" 表示昨天, 或指定日期如 "2025-01-25"

```yaml
target_date: null # null 或 "today" 表示当天, "yesterday" 表示昨天, 或指定日期如 "2025-01-25"
```

#### 配置公众号文章 URL：

**注意事项**：随便找一个公众号的文章的url，就可以跟踪到这个公众号的所有文章，因此你只需要配置你想要跟踪的公众号的文章url即可，一个公众号只需随意配置一篇文章的url即可，**不要重复配置**！！！

```yaml
article_urls:
  - https://mp.weixin.qq.com/s/ZrBDFuugPyuoQp4S6wEBWQ  # 机器之心任意一篇文章url
  - https://mp.weixin.qq.com/s/xxxxxxxxxxxxxx # 微信公众号B任意一篇文章url
  - https://mp.weixin.qq.com/s/xxxxxxxxxxxxxx # 微信公众号C任意一篇文章url
  - ...
```
#### 配置 GUI 模板图片路径：

**注意事项**：你的操作系统和我的操作系统不一样，所以需要根据你微信的实际情况截取模板图片（可参考项目中templates目录下的图片）。GUI自动化操作会依赖这些图片进行点击操作，如果图片模板不准确，可能会**导致自动化操作失败**。

```yaml
GUI_config:
  search_website: templates/search_website.png
  three_dots: templates/three_dots.png
  turnback: templates/turnback.png
```

#### 配置模型：

```yaml
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
### 4. 开始运行，坐等结果

**注意事项**：请保证微信打开到聊天主界面，关闭所有微信其他界面（公众号、搜一搜），将微信放置到主屏幕中，否则可能会导致自动化操作失败。

#### 方式一：命令行运行（稳定可靠）

```bash
uv run main.py
```

#### 方式二：桌面客户端（尝鲜体验，正在优化中……）

桌面客户端提供可视化界面，支持：
- 日期选择（今天/昨天/自定义）
- 文章链接管理（添加/删除/从配置加载）
- API Key 设置
- 实时日志显示和进度条
- 一键执行全流程

**运行客户端**：

```bash
uv run app.py
```

**打包为可执行文件**：

**警告**：运行可执行文件可能存在bug，玩一玩可以，正式使用不推荐！！！

项目支持打包为独立可执行文件，**无需 Python 环境即可运行**。使用一键打包脚本：

#### Windows 打包

```bash
# 在项目根目录运行
scripts\build_windows.bat
```

打包完成后，可执行文件位于 `dist/微信AI日报助手.exe`。

#### macOS 打包

```bash
# 在项目根目录运行
chmod +x scripts/build_macos.sh
./scripts/build_macos.sh
```

打包完成后，应用位于 `dist/微信AI日报助手.app`。

#### 打包注意事项

1. **自动安装依赖**：脚本会自动检测并安装 pyinstaller
2. **首次运行**：打包后首次运行需要在 `configs/config.yaml` 中配置 API Key 和文章链接
3. **模板图片**：确保 `templates/` 目录中的模板图片与你的系统匹配
4. **macOS 权限**：首次运行需要在「系统偏好设置 → 安全性与隐私 → 辅助功能」中授权
5. **Windows 杀软**：部分杀毒软件可能误报，请添加信任

## 📝 工作流程

1. **文章采集**：程序自动打开微信，依次访问配置的公众号主页，采集当日发布的所有文章链接
2. **内容提取**：访问每篇文章页面，提取标题、作者、正文、图片等元数据
3. **内容分析**：使用 LLM 为每篇文章生成内容速览、推荐度评分和精选理由
4. **日报输出**：汇总所有文章，生成富文本格式的每日日报 HTML 文件
5. **一键发布**：打开生成的 HTML 文件，复制内容粘贴到公众号编辑器即可
6. **日报格式**：
   - **内容速览**：100-200字的文章核心内容概述
   - **精选理由**：不超过100字的推荐理由和价值说明
   - **评分机制**：90分以上的文章才会被推荐
   - **署名信息**：底部自动添加 "由 Double童发发 开发的 wechat-ai-daily 自动生成"

### 运行测试

```bash
# 运行所有测试
uv run pytest tests/

# 运行单个测试文件
uv run pytest tests/test_tt.py -v
```

## 📁 项目结构

```
wechat-ai-daily/
├── src/wechat_ai_daily/
│   ├── utils/                    # 工具模块
│   │   ├── wechat.py            # 微信进程管理
│   │   ├── autogui.py           # GUI 自动化操作
│   │   ├── vlm.py               # VLM 图像识别
│   │   ├── llm.py               # LLM 摘要生成
│   │   └── types.py             # 数据类型定义
│   └── workflows/                # 工作流模块
│       ├── wechat_autogui.py    # 公众号文章采集器
│       └── daily_generate.py    # 每日日报生成器
├── gui/                          # 桌面客户端模块
│   ├── main_window.py           # 主窗口
│   ├── panels/                  # UI 面板组件
│   ├── workers/                 # 后台工作线程
│   └── utils/                   # 客户端工具类
├── scripts/                      # 构建脚本
│   ├── build_windows.bat        # Windows 打包脚本
│   └── build_macos.sh           # macOS 打包脚本
├── configs/                      # 配置文件
├── templates/                    # 模板文件
├── tests/                        # 测试文件
├── main.py                       # 命令行入口
└── app.py                        # 桌面客户端入口
```

## 🛠️ 技术栈

- **GUI 自动化**：pyautogui、pynput
- **图像处理**：Pillow、OpenCV
- **VLM/LLM**：阿里云 DashScope（通义千问）
- **HTML 解析**：BeautifulSoup4
- **数据验证**：Pydantic
- **桌面客户端**：PyQt6
## ⚠️ 注意事项

- 运行前请确保微信桌面客户端已登录
- 采集过程中请勿操作鼠标和键盘
- 不同系统需要使用对应的模板图片（`templates/` 目录）
- 高分辨率显示屏（如 Retina）的缩放比例已自动处理

## 📞 帮助支持

如果您在使用过程中遇到任何问题或建议，欢迎通过 [GitHub Issues](https://github.com/TongTong313/wechat-ai-daily/issues) 提交反馈。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=TongTong313/wechat-ai-daily&type=Date)](https://star-history.com/#TongTong313/wechat-ai-daily&Date)
