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

---

## ⚠️ 法律声明提示

使用前请先阅读文末**重要法律声明**。

---

## 📖 项目简介

**微信公众号文章智能发布工具**，自动搜集各类 AI 公众号的文章内容，通过 LLM 智能分析筛选出当日推荐文章，并一键发布到你的公众号。

本工具提供从**文章采集**到**公众号文章内容生成**再到**草稿发布**的完整自动化工作流：

1. **文章采集**：支持 RPA 模式和 API 模式，自动采集指定 AI 公众号（如机器之心、量子位等）的当日文章
2. **公众号文章内容生成**：使用 LLM 智能分析文章内容，生成内容速览、推荐评分和精选理由，输出富文本格式的公众号文章内容
3. **草稿发布**：通过微信公众号官方 API 自动创建草稿，无需手动复制粘贴

支持命令行和桌面客户端两种使用方式，可分步执行或一键完成全流程。

**最终效果展示：**

![内容效果](docs/assets/template.png)

### 两种采集模式对比

| 特性         | RPA 模式                           | API 模式（v2.0.0 新增）             |
| ------------ | ---------------------------------- | ----------------------------------- |
| **原理**     | GUI 自动化 + VLM 图像识别          | 微信公众平台后台接口                |
| **优点**     | 无需公众号账号                     | 高效稳定，无需微信客户端，文章全    |
| **缺点**     | 需要微信客户端，速度较慢，文章不全 | 需要公众号账号，cookie/token 会过期 |
| **配置方式** | 配置文章 URL                       | 配置公众号名称 + cookie/token       |

本项目使用了 AI Coding 技术辅助编程，在此感谢 [Claude Code](https://claude.ai/code)、[Cursor](https://cursor.com/) 等 AI Coding 工具，让我的效率提升了100%。

## 🎯 核心特性

### v2.0.0：新增 API 模式文章采集

- **双模式采集**：支持 RPA 模式和 API 模式两种采集方案
  - RPA 模式：GUI 自动化 + VLM 图像识别，无需公众号账号
  - API 模式：微信公众平台后台接口，高效稳定（推荐）
- **微信公众号自动发布**：通过官方 API 自动创建草稿
  - 基于微信官方 API，无需手动复制粘贴
  - HTML 富文本自动转换为微信格式
  - 封面图片自动上传并缓存
  - **目前草稿仍需手动确认发布，正式发布还在疯狂开发中**……
- **环境变量管理优化**：支持 `.env` 文件配置敏感信息
- **PyQt6 桌面客户端**：图形界面应用
  - 可视化配置管理（日期选择、链接管理、API Key 设置、发布配置）
  - 支持3步工作流：采集 → 生成 → 发布
  - 支持分步执行或一键全流程
  - 实时日志显示和进度条反馈
- **可执行文件打包**：支持打包为独立应用
- **GUI 自动化采集**：模拟真实用户操作，自动打开微信、搜索公众号、采集文章链接
- **VLM 智能识别**：使用视觉语言模型识别页面中的日期位置，精准定位当日文章
- **LLM 智能分析**：自动提取文章内容，使用大模型生成内容速览和推荐度评分
- **公众号文章内容生成**：汇总所有文章，生成可直接发布的富文本内容
- **一键粘贴发布**：生成的 HTML 文件打开后复制粘贴即可形成公众号正文
- **跨平台支持**：同时支持 Windows 和 macOS 系统

## 📋 环境要求

- Python >= 3.13
- 微信桌面客户端（Windows 或 macOS）**（仅 RPA 模式需要）**
- 阿里云 DashScope API Key（用于 VLM 图像识别和 LLM 摘要生成）
- 仅支持 Windows 和 macOS 系统
- **API 模式额外要求**：微信公众号账号及后台访问权限

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

### 3. 各种配置（重要！！！）

本项目配置参数较多，请大家务必耐心看完本节，保证代码的顺利执行。根据配置的特性，我在这里将其分为**敏感配置**与**非敏感配置**两大类。其中，敏感配置包括 api_key、appsecret、token 等，剩余配置都认为是非敏感配置。非敏感配置直接在 `configs/config.yaml` 中配置即可，敏感配置同时兼容 `configs/config.yaml`、`.env` 文件和系统环境变量三种方式。在这里，我**强烈建议大家使用 .env 文件配置敏感信息，而不是直接写在配置文件中**。

**敏感信息配置优先级（从高到低）：**

1. **config.yaml 文件**（最高优先级）：对应字段有值时优先使用
2. **.env 文件**（推荐）：项目根目录下的 `.env` 文件，自动添加到 `.gitignore`，不会提交到版本控制
3. **系统环境变量**（最低优先级）：如 `~/.zshrc` 或 Windows 环境变量中设置的变量

**说明**：

- 如果 `config.yaml` 中对应字段有值（非空），优先使用配置文件中的值
- 如果 `config.yaml` 中对应字段为空，系统会先读取 `.env` 文件，再读取系统环境变量
- 使用 `.env` 文件可以避免敏感信息泄露到版本控制系统中（已自动添加到 `.gitignore`）

由于所有的配置参数在配置文件`configs/config.yaml`中都有对应的字段，为了让大家更清晰的了解配置规则，将按照配置文件中的顺序逐一介绍。对于敏感配置，会有特殊说明！！！

#### 3.1 target_date（目标日期）

指定要采集文章的日期，**你要采集哪一天的文章，就配置哪一天**。

**配置示例**：

```yaml
target_date: "2026-01-26" # 必须是YYYY-MM-DD格式
```

#### 3.2 article_urls（RPA模式专属）

公众号文章URL列表，用于RPA模式采集。一个公众号只需提供**任意一篇文章的URL**即可定位该公众号。

**配置示例**：

```yaml
article_urls:
  - https://mp.weixin.qq.com/s/ZrBDFuugPyuoQp4S6wEBWQ # 公众号A任意一篇文章
  - https://mp.weixin.qq.com/s/2Bs7ldBM-DKTjjyAcMvopA # 公众号B任意一篇文章
  - https://mp.weixin.qq.com/s/3ylI_kgbB-mRAWnAslRE0Q # 公众号C任意一篇文章
```

**注意事项**：

- 每个公众号只需配置一篇文章URL，**不要重复配置**
- 仅在使用 RPA 模式采集时需要此配置
- API 模式不使用此配置项（API 模式使用 `api_config.account_names`）

#### 3.3 api_config（API模式专属配置）

v2.0.0 新增的 API 模式采集配置，通过微信公众平台后台接口获取文章列表。

**配置示例**：

```yaml
api_config:
  token: # 留空时从环境变量 WECHAT_API_TOKEN 读取，填写则优先使用此值
  cookie: # 留空时从环境变量 WECHAT_API_COOKIE 读取，填写则优先使用此值
  account_names: # 要采集的公众号名称列表
    - 机器之心
    - 量子位
    - 新智元
```

**字段说明**：

- `token`：微信公众平台后台 Token（**敏感配置**）
- `cookie`：微信公众平台后台 Cookie（**敏感配置**）
- `account_names`：要采集的公众号名称列表（精确匹配）

**敏感配置说明**：

`token` 和 `cookie` 为敏感信息且会定期失效，建议使用环境变量配置：

1. **获取方式**：
   - 登录 https://mp.weixin.qq.com
   - 点击左侧菜单 **"内容与互动"** → **"草稿箱"** → **"新建图文"**
   - 在编辑器中点击工具栏的 **"超链接"** → 选择 **"选择其他公众号"**
   - 按 **F12** 打开开发者工具 → 切换到 **Network（网络）** 标签
   - 在搜索框中输入任意公众号名称并搜索
   - 在 Network 面板中找到 `searchbiz` 请求：
     - **Token**：从 Request URL 中复制 `token=xxxxxx` 的值
     - **Cookie**：从 Request Headers 中复制整个 Cookie 值

2. **环境变量配置**：
   - 在 `.env` 文件中添加：
     ```bash
     WECHAT_API_TOKEN=your_token_here
     WECHAT_API_COOKIE=your_cookie_here
     ```
   - 或设置系统环境变量（macOS/Linux）：
     ```bash
     export WECHAT_API_TOKEN="your_token_here"
     export WECHAT_API_COOKIE="your_cookie_here"
     ```
   - Windows PowerShell：
     ```powershell
     $env:WECHAT_API_TOKEN="your_token_here"
     $env:WECHAT_API_COOKIE="your_cookie_here"
     ```

**注意事项**：

- Cookie 和 Token 有时效性，通常几小时后过期，需要重新获取
- 不要泄露你的 Cookie，它相当于登录凭证

#### 3.4 GUI_config（RPA模式专属，GUI自动化配置）

用于RPA模式的GUI自动化操作，指定模板图片路径。

**配置示例**：

```yaml
GUI_config:
  search_website: templates/search_website.png # "访问网页"按钮模板
  three_dots: templates/three_dots.png # 三点菜单按钮模板
  turnback: templates/turnback.png # 返回按钮模板
```

**字段说明**：

- `search_website`：微信中"访问网页"按钮的模板图片
- `three_dots`：右上角三点菜单按钮的模板图片
- `turnback`：返回按钮的模板图片

**重要提示**：

- 不同操作系统的微信界面不同，需要根据**你的系统**截取对应的模板图片
- macOS 用户使用 `templates/search_website_mac.png` 等模板
- Windows 用户使用 `templates/search_website.png` 等模板
- 可参考项目 `templates/` 目录下的示例图片
- 如果图片模板不准确，可能会**导致自动化操作失败**

#### 3.5 model_config（模型配置）

用于生成公众号文章摘要（LLM）和RPA流程图像定位（VLM）。

**配置示例**：

```yaml
model_config:
  LLM:
    model: qwen-plus
    api_key: # 留空时自动读取（优先级：.env 文件 > 系统环境变量 DASHSCOPE_API_KEY），填写则优先使用此值
    thinking_budget: 1024
    enable_thinking: true
  VLM:
    model: qwen3-vl-plus
    api_key: # 留空时自动读取（优先级：.env 文件 > 系统环境变量 DASHSCOPE_API_KEY），填写则优先使用此值
    thinking_budget: 1024
    enable_thinking: true
```

**字段说明**：

- `model`：模型名称（使用阿里云DashScope模型）
- `api_key`：阿里云DashScope API密钥（**敏感配置**）
- `thinking_budget`：思考预算（token数量）
- `enable_thinking`：是否启用思考模式

**敏感配置说明**：

`api_key` 为敏感信息，配置方式与 3.3 节类似。在 `.env` 文件中添加或设置系统环境变量（方法参考 3.3 节）：

```bash
DASHSCOPE_API_KEY=your_dashscope_api_key_here
```

**API Key 获取方式**：访问 https://dashscope.console.aliyun.com/apiKey

#### 3.6 publish_config（微信公众号发布配置）

用于自动化发布公众号文章到草稿箱。

**配置示例**：

```yaml
publish_config:
  appid: # 留空时从环境变量 WECHAT_APPID 读取
  appsecret: # 留空时从环境变量 WECHAT_APPSECRET 读取
  media_id: Nrbr4jsf-IL2M6L2LYAu_0quiwqrzmrS-l251mHazbBfCYmw0PxMNiWGtAGZe3Aw # 封面图片的media_id（可选）
  cover_path: templates/default_cover.png # 封面图片路径
  author: Double童发发 # 公众号作者
```

**字段说明**：

- `appid`：公众号AppID/开发者ID（**敏感配置**）
- `appsecret`：公众号AppSecret/开发者密码（**敏感配置**）
- `media_id`：封面图片的media_id（可选）
  - 如果已有media_id，直接填写可跳过封面上传步骤
  - 优先级高于 `cover_path`
  - 第一次上传封面后建议保存media_id以便复用
- `cover_path`：封面图片本地路径
  - 当 `media_id` 为空时，会根据此路径上传封面
- `author`：文章作者名称

**敏感配置说明**：

`appid` 和 `appsecret` 为敏感信息，配置方式与 3.3 节类似：

```bash
WECHAT_APPID=your_appid_here
WECHAT_APPSECRET=your_appsecret_here
```

**AppID/AppSecret 获取方式**：

1. 登录微信开放平台：https://open.weixin.qq.com
2. 进入 **我的业务与服务** → **公众号**
3. 查看 **开发者ID(AppID)** 和 **开发者密码(AppSecret)**

#### 附：环境变量配置速查

前面各配置项中已经分别说明了环境变量的配置方法，这里提供一个统一的速查表，方便快速查找所有敏感配置对应的环境变量。

**环境变量与配置项对应关系：**

| 环境变量            | 对应配置项                                               | 用途         |
| ------------------- | -------------------------------------------------------- | ------------ |
| `DASHSCOPE_API_KEY` | `model_config.LLM.api_key`<br>`model_config.VLM.api_key` | 大模型调用   |
| `WECHAT_APPID`      | `publish_config.appid`                                   | 公众号发布   |
| `WECHAT_APPSECRET`  | `publish_config.appsecret`                               | 公众号发布   |
| `WECHAT_API_TOKEN`  | `api_config.token`                                       | API 模式采集 |
| `WECHAT_API_COOKIE` | `api_config.cookie`                                      | API 模式采集 |

**配置方法：**

所有环境变量均可通过 **`.env` 文件** 或 **系统环境变量** 进行配置，详细步骤请参考 **3.3 节** 中的说明。

**快速开始（推荐）：**

```bash
# 1. 复制模板文件
cp .env.example .env

# 2. 编辑 .env 文件，根据上表填写对应的环境变量

# 3. 验证配置（可选）
uv run python tests/diagnose_env.py
```

### 4. 开始运行，坐等结果

#### 方式一：命令行运行

命令行支持 **RPA 模式** 和 **API 模式** 两种采集方式，以及 **完整流程**（采集→生成→发布）和 **分步执行** 两种运行方式。

##### 一键全流程（推荐）

执行「采集 → 生成 → 发布」完整流程，最省心的使用方式：

**RPA 模式**（需要微信客户端）：

```bash
# 请保证微信打开到聊天主界面，关闭所有微信其他界面
uv run main.py --mode rpa --workflow full
```

**API 模式**（v2.0.0 新增，推荐）：

```bash
# 无需微信客户端，但需要配置 cookie 和 token
uv run main.py --mode api --workflow full
```

> **提示**：`--workflow full` 是默认值，可以省略。即 `uv run main.py --mode api` 等价于 `uv run main.py --mode api --workflow full`

##### 分步执行

如果需要分步执行工作流（例如先采集，检查结果后再生成和发布），可以使用以下命令：

**步骤1：仅采集文章**

```bash
# RPA 模式采集
uv run main.py --mode rpa --workflow collect

# API 模式采集（推荐）
uv run main.py --mode api --workflow collect
```

采集完成后，文章列表会保存到 `output/articles_YYYYMMDD.md`。

**步骤2：仅生成公众号文章内容**（需要先执行采集）

```bash
# 自动查找当天的文章列表文件
uv run main.py --workflow generate

# 或指定特定的文章列表文件
uv run main.py --workflow generate --markdown-file output/articles_20260126.md
```

生成完成后，公众号文章内容 HTML 会保存到 `output/daily_rich_text_YYYYMMDD.html`。

**步骤3：仅发布草稿**（需要先执行生成）

```bash
# 自动查找当天的公众号文章内容 HTML 文件
uv run main.py --workflow publish

# 或指定特定的公众号文章内容 HTML 文件
uv run main.py --workflow publish --html-file output/daily_rich_text_20260126.html
```

发布完成后，草稿会出现在微信公众平台的草稿箱中，需要手动确认发布。

##### 命令行参数说明

| 参数              | 可选值                                   | 默认值   | 说明                                                                                          |
| ----------------- | ---------------------------------------- | -------- | --------------------------------------------------------------------------------------------- |
| `--mode`          | `rpa`, `api`                             | `rpa`    | 采集模式选择。`rpa`：GUI 自动化 + VLM 识别；`api`：微信公众平台后台接口（推荐）               |
| `--workflow`      | `collect`, `generate`, `publish`, `full` | `full`   | 工作流类型。`collect`：仅采集；`generate`：仅生成；`publish`：仅发布；`full`：完整流程        |
| `--markdown-file` | 文件路径                                 | 自动查找 | 指定已有的文章列表文件（用于 `generate` 或 `publish` 工作流）。如不指定，将自动查找当天的文件 |
| `--html-file`     | 文件路径                                 | 自动查找 | 指定已有的公众号文章内容 HTML 文件（用于 `publish` 工作流）。如不指定，将自动查找当天的文件   |

#### 方式二：桌面客户端（尝鲜体验，正在优化中……）

桌面客户端提供可视化界面，支持：

- 日期选择（今天/昨天/自定义）
- 文章链接管理（添加/删除/从配置加载）
- API Key 设置
- 实时日志显示和进度条
- 一键执行全流程

**运行客户端（这里是稳定的）**：

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

本工具提供从文章采集到草稿发布的完整自动化工作流，支持 **RPA 模式** 和 **API 模式** 两种采集方式。

### 完整工作流（三步流程）

无论使用哪种采集模式，完整工作流都包括以下三个步骤：

1. **文章采集**：采集指定公众号的当日文章链接
2. **公众号文章内容生成**：访问文章页面，提取元数据，使用 LLM 分析并生成公众号文章内容
3. **草稿发布**：通过微信公众号官方 API 创建草稿

#### 命令行方式

```bash
# 一键全流程（RPA 模式）
uv run main.py --mode rpa --workflow full

# 一键全流程（API 模式，推荐）
uv run main.py --mode api --workflow full
```

#### 桌面客户端方式

使用 `uv run app.py` 打开桌面客户端，依次点击「采集文章」→「公众号文章内容生成」→「发布草稿」按钮。

---

### 步骤1：文章采集

#### RPA 模式采集流程

RPA 模式通过 GUI 自动化 + VLM 图像识别获取文章，无需公众号账号：

1. 自动打开/激活微信应用
2. 从配置文件读取文章 URL，提取 biz 参数，构建公众号主页 URL
3. 对每个公众号：
   - 打开微信搜索（ctrl/cmd+f）
   - 输入公众号 URL 并搜索
   - 点击「访问网页」进入公众号主页
   - 循环采集当天文章：
     - 截图当前页面
     - 使用 VLM 识别当天日期的文章位置
     - 点击文章，复制链接，返回主页
     - 滚动页面加载更多文章
     - 检测到昨天日期时停止
4. 保存采集结果到 `output/articles_YYYYMMDD.md`

**命令行运行**：

```bash
uv run main.py --mode rpa --workflow collect
```

#### API 模式采集流程（v2.0.0 新增）

API 模式通过微信公众平台后台接口获取文章，高效稳定（推荐）：

1. 从配置文件读取 cookie、token 和公众号名称列表
2. 对每个公众号：
   - 调用 `/cgi-bin/searchbiz` 接口搜索公众号，获取 fakeid
   - 调用 `/cgi-bin/appmsg` 接口获取文章列表
   - 按目标日期筛选文章
3. 合并所有文章并去重
4. 保存采集结果到 `output/articles_YYYYMMDD.md`

**命令行运行**：

```bash
uv run main.py --mode api --workflow collect
```

**输出示例**：

```markdown
# 2026-01-26 AI公众号文章汇总

## 机器之心

- [文章标题1](https://mp.weixin.qq.com/s/xxxxx)
- [文章标题2](https://mp.weixin.qq.com/s/yyyyy)

## 量子位

- [文章标题3](https://mp.weixin.qq.com/s/zzzzz)
```

---

### 步骤2：公众号文章内容生成

公众号文章内容生成器会读取采集器生成的文章列表，访问每篇文章页面，提取元数据并使用 LLM 分析：

1. 解析采集器生成的 Markdown 文件
2. 对每篇文章：
   - 获取文章 HTML 内容
   - 提取元数据（标题、作者、发布时间、封面图、正文等）
   - 使用 LLM 生成内容速览（100-200字）、推荐度评分（0-5星）和精选理由（100字以内）
3. 按评分降序排列所有文章
4. 筛选推荐文章（3星及以上，或不足时取前3篇）
5. 使用富文本模板生成 HTML 内容
6. 保存到 `output/daily_rich_text_YYYYMMDD.html`

**命令行运行**：

```bash
# 自动查找当天的文章列表文件
uv run main.py --workflow generate

# 或指定特定的文章列表文件
uv run main.py --workflow generate --markdown-file output/articles_20260126.md
```

**公众号文章内容格式说明**：

- **内容速览**：100-200字的文章核心内容概述
- **精选理由**：不超过100字的推荐理由和价值说明
- **评分机制**：3星及以上的文章才会被推荐
- **署名信息**：底部自动添加「由 Double童发发 开发的 wechat-ai-daily 自动生成」

---

### 步骤3：草稿发布

通过微信公众号官方 API 自动创建草稿，无需手动复制粘贴：

1. 读取生成的公众号文章内容 HTML 文件
2. HTML 转换为微信公众号格式
3. 上传封面图片并缓存 media_id
4. 调用微信官方 API 创建草稿
5. 草稿创建成功后，可在微信公众平台草稿箱中查看

**命令行运行**：

```bash
# 自动查找当天的公众号文章内容 HTML 文件
uv run main.py --workflow publish

# 或指定特定的公众号文章内容 HTML 文件
uv run main.py --workflow publish --html-file output/daily_rich_text_20260126.html
```

**注意**：

- 草稿创建后仍需手动在微信公众平台确认发布
- 正式自动发布功能正在疯狂开发中……

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
│   │   ├── wechat/              # 微信相关工具（v2.0.0 模块化拆分）
│   │   │   ├── __init__.py
│   │   │   ├── process.py       # 微信进程管理和窗口控制
│   │   │   ├── base_client.py   # API 客户端基类
│   │   │   ├── article_client.py  # 文章采集 API 客户端
│   │   │   ├── publish_client.py  # 草稿发布 API 客户端
│   │   │   └── exceptions.py    # 微信 API 异常类
│   │   ├── autogui.py           # GUI 自动化操作
│   │   ├── vlm.py               # VLM 图像识别
│   │   ├── llm.py               # LLM 摘要生成
│   │   ├── env_loader.py        # 环境变量加载工具
│   │   ├── types.py             # 数据类型定义
│   │   └── paths.py             # 路径管理工具
│   └── workflows/                # 工作流模块
│       ├── base.py              # 工作流基类
│       ├── rpa_article_collector.py    # RPA 模式采集器
│       ├── api_article_collector.py    # API 模式采集器（v2.0.0 新增）
│       ├── daily_generate.py    # 公众号文章内容生成器
│       └── daily_publish.py     # 公众号自动发布
├── gui/                          # 桌面客户端模块
│   ├── main_window.py           # 主窗口
│   ├── theme_manager.py         # 主题管理器（v2.0.0 新增）
│   ├── styles.py                # 样式定义
│   ├── panels/                  # UI 面板组件
│   │   ├── config_panel.py      # 配置面板
│   │   ├── progress_panel.py    # 进度面板
│   │   └── log_panel.py         # 日志面板
│   ├── workers/                 # 后台工作线程
│   │   └── workflow_worker.py   # 工作流执行器
│   └── utils/                   # 客户端工具类
│       ├── config_manager.py    # 配置管理器
│       └── log_handler.py       # 日志处理器
├── scripts/                      # 构建脚本
│   ├── build_windows.bat        # Windows 打包脚本
│   └── build_macos.sh           # macOS 打包脚本
├── configs/                      # 配置文件
│   └── config.yaml              # 主配置文件
├── templates/                    # 模板文件
│   ├── rich_text_template.html  # 富文本 HTML 模板
│   ├── default_cover.png        # 默认封面图片
│   └── ...                      # GUI 模板图片
├── tests/                        # 测试文件
│   ├── test_api_full_workflow.py  # API 模式完整工作流测试
│   └── ...
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
- **环境变量**：python-dotenv
- **配置管理**：ruamel-yaml

## ⚠️ 注意事项

- 运行前请确保微信桌面客户端已登录
- 采集过程中请勿操作鼠标和键盘
- 不同系统需要使用对应的模板图片（`templates/` 目录）
- 高分辨率显示屏（如 Retina）的缩放比例已自动处理

## 📞 帮助支持

如果您在使用过程中遇到任何问题或建议，欢迎通过 [GitHub Issues](https://github.com/TongTong313/wechat-ai-daily/issues) 提交反馈。

## ⚠️ 重要法律声明

**本项目仅供个人学习和研究使用，请勿用于商业用途。**

### 使用风险提示

1. **API 模式风险**：
   - API 模式使用了微信公众平台的**非公开后台接口**
   - 需要通过浏览器开发者工具（F12）获取 cookie 和 token
   - 这些操作可能**违反微信公众平台服务协议**
   - cookie/token 仅限本人公众号使用，请勿用于他人账号

2. **RPA 模式风险**：
   - RPA 模式的 GUI 自动化操作可能违反微信用户协议
   - 频繁的自动化操作可能导致账号被限制或封禁

3. **使用责任**：
   - 使用本工具产生的一切后果由使用者自行承担
   - 作者不对任何因使用本工具产生的损失或法律问题负责
   - 使用前请确保您拥有相关公众号的合法访问权限
   - 请遵守微信平台相关服务条款和法律法规

4. **数据使用规范**：
   - 采集的数据仅限个人使用，不得转售或用于商业目的
   - 尊重原作者版权，采集的内容仅用于个人学习参考

**如果您不同意以上声明，请立即停止使用本工具。继续使用即表示您已阅读、理解并同意遵守上述条款。**

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=TongTong313/wechat-ai-daily&type=Date)](https://star-history.com/#TongTong313/wechat-ai-daily&Date)
