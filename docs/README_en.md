# WeChat AI Daily

<div align="center">

[中文](../README.md) | [English](README_en.md)

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-Package%20Manager-blueviolet.svg)](https://github.com/astral-sh/uv)
[![DashScope](https://img.shields.io/badge/DashScope-VLM%20%26%20LLM-orange.svg)](https://dashscope.aliyun.com/)
[![Bilibili](https://img.shields.io/badge/Bilibili-Double童发发-ff69b4.svg)](https://space.bilibili.com/323109608)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

**Author: Double童发发** · [Bilibili](https://space.bilibili.com/323109608)

</div>

---

## ⚠️ Legal Notice Reminder

Please read the **Important Legal Notice** at the end before using this tool.

---

## 📖 Introduction

**WeChat Official Account Article Smart Publishing Tool** - automatically collects articles from various AI official accounts, uses LLM to intelligently analyze and select daily recommended articles, and publishes them to your official account with one click.

This tool provides a complete automated workflow from **Article Collection** to **Official Account Article Content Generation** to **Draft Publishing**:

1. **Article Collection**: Supports RPA Mode and API Mode, automatically collects daily articles from specified AI official accounts (e.g., Machine Intelligence, Synced, etc.)
2. **Official Account Article Content Generation**: Uses LLM to intelligently analyze article content, generates content overview, recommendation scores, and selection rationale, outputs rich-text official account article content
3. **Draft Publishing**: Automatically creates drafts via WeChat Official Account API, no manual copy-paste needed

Supports both command-line and desktop client usage, with step-by-step execution or one-click full workflow.

**Final Result Preview:**

![Content Preview](../assets/template.png)

### Two Collection Modes Comparison

| Feature           | RPA Mode                         | API Mode (New in v2.0.0)                   |
| ----------------- | -------------------------------- | ------------------------------------------ |
| **Principle**     | GUI Automation + VLM Recognition | WeChat MP Backend API                      |
| **Pros**          | No MP account needed             | Efficient, stable, no WeChat client needed |
| **Cons**          | Requires WeChat client, slower   | Requires MP account, cookie/token expires  |
| **Configuration** | Article URLs                     | Account names + cookie/token               |

This project was developed with the assistance of AI Coding tools. Special thanks to [Claude Code](https://claude.ai/code), [Cursor](https://cursor.com/), and other AI Coding tools.

## 🎯 Core Features

### v2.0.0: API Mode for Article Collection

- **Dual Collection Modes**: Supports both RPA Mode and API Mode
  - RPA Mode: GUI Automation + VLM Recognition, no MP account needed
  - API Mode: WeChat MP Backend API, efficient and stable (Recommended)
- **WeChat Auto-Publishing**: Create drafts via official API
  - Based on WeChat official API, no manual copy-paste needed
  - Auto-convert HTML rich text to WeChat format
  - Auto-upload cover images with caching
  - Drafts still require manual confirmation to publish, official publishing is under development...
- **Environment Variable Optimization**: Support `.env` file for sensitive info
- **PyQt6 Desktop Client**: Graphical interface application
  - Visual configuration management (date selection, link management, API Key settings, publish config)
  - Supports 3-step workflow: Collect → Generate → Publish
  - Supports step-by-step execution or one-click full workflow
  - Real-time log display and progress bar feedback
- **Executable Packaging**: Support for packaging as standalone applications
- **GUI Automated Collection**: Simulates real user operations to automatically open WeChat, search for official accounts, and collect article links
- **VLM Intelligent Recognition**: Uses vision language models to identify date positions on pages, precisely locating today's articles
- **LLM Intelligent Analysis**: Automatically extracts article content and uses large models to generate content overviews and recommendation scores
- **Official Account Article Content Generation**: Aggregates all articles and generates rich-text content ready for publishing
- **One-Click Publishing**: Open the generated HTML file, copy and paste to form your official account content
- **Cross-Platform Support**: Supports both Windows and macOS systems

## 📋 Requirements

- Python >= 3.13
- WeChat Desktop Client (Windows or macOS) **(Required for RPA Mode only)**
- Alibaba Cloud DashScope API Key (for VLM image recognition and LLM summary generation)
- Only supports Windows and macOS systems
- **API Mode Additional Requirements**: WeChat Official Account and backend access permissions

## 🚀 Quick Start

### 1. Clone the Project

```bash
git clone https://github.com/TongTong313/wechat-ai-daily.git
cd wechat-ai-daily
```

### 2. Install Dependencies

```bash
# Install dependencies using uv (recommended)
uv sync
```

### 3. Configure config.yaml File

Edit `configs/config.yaml` according to your actual situation, including:

#### Configure Target Date:

**Important Note**: Configure the target date according to your needs, i.e., **set the date of the articles you want to collect**. Use `null` or `"today"` for today, `"yesterday"` for yesterday, or specify a date like `"2025-01-25"`.

```yaml
target_date: null # null or "today" for today, "yesterday" for yesterday, or specify date like "2025-01-25"
```

#### Configure Official Account Article URLs:

**Important Note**: You can track all articles from an official account by providing any article URL from that account. Therefore, you only need to configure one article URL per official account you want to track. **Do not configure duplicate URLs for the same account**!!!

```yaml
article_urls:
  - https://mp.weixin.qq.com/s/ZrBDFuugPyuoQp4S6wEBWQ # Any article URL from Machine Intelligence
  - https://mp.weixin.qq.com/s/xxxxxxxxxxxxxx # Any article URL from Official Account B
  - https://mp.weixin.qq.com/s/xxxxxxxxxxxxxx # Any article URL from Official Account C
  - ...
```

#### Configure GUI Template Image Paths:

**Important Note**: Your operating system and mine may differ, so you need to capture template images based on your actual WeChat interface (refer to images in the templates directory of the project). GUI automation operations rely on these images for clicking. If the image templates are inaccurate, it may **cause automation operations to fail**.

```yaml
GUI_config:
  search_website: templates/search_website.png
  three_dots: templates/three_dots.png
  turnback: templates/turnback.png
```

#### Configure Models:

**Configuration Priority (High to Low)**: When `api_key` is null, the system automatically reads from: 1) `.env` file, 2) system environment variable `DASHSCOPE_API_KEY`. If a value is specified in config.yaml, it takes highest priority.

```yaml
model_config:
  LLM:
    model: qwen-plus
    api_key: null # When null, reads from .env or environment variable DASHSCOPE_API_KEY; otherwise uses this value
    thinking_budget: 1024
    enable_thinking: true
  VLM:
    model: qwen3-vl-plus
    api_key: null # When null, reads from .env or environment variable DASHSCOPE_API_KEY; otherwise uses this value
    thinking_budget: 1024
    enable_thinking: true
```

#### Configure WeChat Publishing:

**Configuration Priority (High to Low)**: To avoid exposing credentials in the config file, set `appid` and `appsecret` to null, and the system will automatically read from: 1) `.env` file, 2) system environment variables. If values are specified in config.yaml, they take highest priority.

```yaml
publish_config:
  appid: null # When null, reads from .env or WECHAT_APPID environment variable; otherwise uses this value
  appsecret: null # When null, reads from .env or WECHAT_APPSECRET environment variable; otherwise uses this value
  cover_path: templates/default_cover.png # Cover image path
  author: Double童发发 # Author name
```

#### Configure API Mode Collection (New in v2.0.0)

If using API mode for article collection, configure the following:

**Configuration Priority (High to Low)**: To avoid exposing credentials in the config file, leave `token` and `cookie` empty, and the system will automatically read from: 1) `.env` file, 2) system environment variables. If values are specified in config.yaml, they take highest priority.

```yaml
api_config:
  token: "your_token_here" # When empty, reads from .env or WECHAT_API_TOKEN environment variable; otherwise uses this value
  cookie: "your_cookie_here" # When empty, reads from .env or WECHAT_API_COOKIE environment variable; otherwise uses this value
  account_names: # List of official account names to collect
    - 机器之心
    - 量子位
    - 新智元
```

##### How to Get Cookie and Token

1. **Login to WeChat MP Platform**
   - Open browser and visit https://mp.weixin.qq.com
   - Login with your MP account

2. **Navigate to Article Selection**
   - Click **"Content & Interaction"** → **"Drafts"** in the left menu
   - Click **"New Article"**
   - Click the **"Hyperlink"** button in the editor toolbar
   - Select **"Select Other Official Account"**

3. **Open Developer Tools**
   - Press **F12** to open browser developer tools
   - Switch to the **Network** tab
   - Search for any official account name in the search box

4. **Extract Parameters**
   - Find the `searchbiz` request in the Network panel
   - **Token**: Copy the `token=xxxxxx` value from Request URL
   - **Cookie**: Copy the entire Cookie value from Request Headers

**Notes**:

- Cookie and Token expire after a few hours, need to re-obtain
- Do not leak your Cookie, it's equivalent to login credentials

#### Appendix: Environment Variable Quick Reference

The configuration methods for environment variables have been explained in each configuration section above. Here is a unified quick reference table for easy lookup of all sensitive configuration environment variables.

**Environment Variable to Configuration Mapping:**

| Environment Variable | Configuration Item                                       | Purpose             |
| -------------------- | -------------------------------------------------------- | ------------------- |
| `DASHSCOPE_API_KEY`  | `model_config.LLM.api_key`<br>`model_config.VLM.api_key` | LLM/VLM API         |
| `WECHAT_APPID`       | `publish_config.appid`                                   | WeChat Publishing   |
| `WECHAT_APPSECRET`   | `publish_config.appsecret`                               | WeChat Publishing   |
| `WECHAT_API_TOKEN`   | `api_config.token`                                       | API Mode Collection |
| `WECHAT_API_COOKIE`  | `api_config.cookie`                                      | API Mode Collection |

**Configuration Methods:**

All environment variables can be configured via **`.env` file** or **system environment variables**. For detailed steps, please refer to the instructions in **Section 3.3**.

**Quick Start (Recommended):**

```bash
# 1. Copy the template file
cp .env.example .env

# 2. Edit the .env file and fill in the environment variables according to the table above

# 3. Verify configuration (optional)
uv run python tests/diagnose_env.py
```

### 4. Start Running and Wait for Results

#### Method 1: Command Line

The command line supports both **RPA Mode** and **API Mode** for collection, as well as **Full Workflow** (Collect → Generate → Publish) and **Step-by-Step Execution**.

##### One-Click Full Workflow (Recommended)

Execute the complete workflow of「Collect → Generate → Publish」, the most convenient usage:

**RPA Mode** (Requires WeChat client):

```bash
# Ensure WeChat is open to main chat interface, close all other WeChat windows
uv run main.py --mode rpa --workflow full
```

**API Mode** (New in v2.0.0, Recommended):

```bash
# No WeChat client needed, but requires cookie and token configuration
uv run main.py --mode api --workflow full
```

> **Tip**: `--workflow full` is the default value and can be omitted. i.e., `uv run main.py --mode api` is equivalent to `uv run main.py --mode api --workflow full`

##### Step-by-Step Execution

If you need to execute the workflow step by step (e.g., collect first, check results, then generate and publish), use these commands:

**Step 1: Collect Articles Only**

```bash
# RPA mode collection
uv run main.py --mode rpa --workflow collect

# API mode collection (Recommended)
uv run main.py --mode api --workflow collect
```

After collection, the article list will be saved to `output/articles_YYYYMMDD.md`.

**Step 2: Generate Report Only** (Requires collection first)

```bash
# Automatically find today's article list file
uv run main.py --workflow generate

# Or specify a specific article list file
uv run main.py --workflow generate --markdown-file output/articles_20260126.md
```

After generation, the official account article content HTML will be saved to `output/daily_rich_text_YYYYMMDD.html`.

**Step 3: Publish Draft Only** (Requires generation first)

```bash
# Automatically find today's official account article content HTML file
uv run main.py --workflow publish

# Or specify a specific official account article content HTML file
uv run main.py --workflow publish --html-file output/daily_rich_text_20260126.html
```

After publishing, the draft will appear in the WeChat MP draft box and requires manual confirmation to publish.

##### Command Line Parameters

| Parameter         | Values                                   | Default     | Description                                                                                                                                  |
| ----------------- | ---------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `--mode`          | `rpa`, `api`                             | `rpa`       | Collection mode selection. `rpa`: GUI automation + VLM recognition; `api`: WeChat MP backend API (Recommended)                               |
| `--workflow`      | `collect`, `generate`, `publish`, `full` | `full`      | Workflow type. `collect`: Collection only; `generate`: Generation only; `publish`: Publishing only; `full`: Full workflow                    |
| `--markdown-file` | File path                                | Auto-detect | Specify existing article list file (for `generate` or `publish` workflow). If not specified, will automatically find today's file            |
| `--html-file`     | File path                                | Auto-detect | Specify existing official account article content HTML file (for `publish` workflow). If not specified, will automatically find today's file |

#### Method 2: Desktop Client (Early Access, Under Optimization...)

The desktop client provides a visual interface with support for:

- Date selection (Today/Yesterday/Custom)
- Article link management (Add/Delete/Load from config)
- API Key settings
- Real-time log display and progress bar
- One-click full workflow execution

**Run the Client**:

```bash
uv run app.py
```

**Package as Executable**:

**Warning**: Running the executable file may have bugs. It's fine for testing, but not recommended for production use!!!

The project supports packaging as standalone executable files that can run without a Python environment. Use the one-click build scripts:

#### Windows Packaging

```bash
# Run from project root directory
scripts\build_windows.bat
```

After packaging, the executable is located at `dist/微信AI日报助手.exe`.

#### macOS Packaging

```bash
# Run from project root directory
chmod +x scripts/build_macos.sh
./scripts/build_macos.sh
```

After packaging, the application is located at `dist/微信AI日报助手.app`.

#### Packaging Notes

1. **Auto-install Dependencies**: The script will automatically detect and install pyinstaller
2. **First Run**: After packaging, the first run requires configuring API Key and article links in `configs/config.yaml`
3. **Template Images**: Ensure template images in the `templates/` directory match your system
4. **macOS Permissions**: First run requires authorization in "System Preferences → Security & Privacy → Accessibility"
5. **Windows Antivirus**: Some antivirus software may report false positives, please add to trusted list

## 📝 Workflow

This tool provides a complete automated workflow from article collection to draft publishing, supporting both **RPA Mode** and **API Mode** for collection.

### Complete Workflow (Three-Step Process)

Regardless of which collection mode is used, the complete workflow includes the following three steps:

1. **Article Collection**: Collect today's article links from specified official accounts
2. **Official Account Article Content Generation**: Visit article pages, extract metadata, analyze with LLM and generate official account article content
3. **Draft Publishing**: Create drafts via WeChat Official Account API

#### Command Line Method

```bash
# One-click full workflow (RPA mode)
uv run main.py --mode rpa --workflow full

# One-click full workflow (API mode, Recommended)
uv run main.py --mode api --workflow full
```

#### Desktop Client Method

Use `uv run app.py` to open the desktop client, then click「Collect Articles」→「Generate Report」→「Publish Draft」buttons in sequence.

---

### Step 1: Article Collection

#### RPA Mode Collection Workflow

RPA mode collects articles via GUI automation + VLM image recognition, no MP account needed:

1. Automatically open/activate WeChat application
2. Read article URLs from config, extract biz parameter, build official account homepage URLs
3. For each official account:
   - Open WeChat search (ctrl/cmd+f)
   - Enter official account URL and search
   - Click "Visit Website" to enter official account homepage
   - Loop to collect today's articles:
     - Screenshot current page
     - Use VLM to identify today's date article positions
     - Click article, copy link, return to homepage
     - Scroll page to load more articles
     - Stop when yesterday's date is detected
4. Save collection results to `output/articles_YYYYMMDD.md`

**Command Line**:

```bash
uv run main.py --mode rpa --workflow collect
```

#### API Mode Collection Workflow (New in v2.0.0)

API mode collects articles via WeChat MP backend API, efficient and stable (Recommended):

1. Read cookie, token and official account name list from config
2. For each official account:
   - Call `/cgi-bin/searchbiz` API to search account, get fakeid
   - Call `/cgi-bin/appmsg` API to get article list
   - Filter articles by target date
3. Merge all articles and deduplicate
4. Save collection results to `output/articles_YYYYMMDD.md`

**Command Line**:

```bash
uv run main.py --mode api --workflow collect
```

**Output Example**:

```markdown
# 2026-01-26 AI Official Account Articles

## Machine Intelligence

- [Article Title 1](https://mp.weixin.qq.com/s/xxxxx)
- [Article Title 2](https://mp.weixin.qq.com/s/yyyyy)

## Synced

- [Article Title 3](https://mp.weixin.qq.com/s/zzzzz)
```

---

### Step 2: Official Account Article Content Generation

The official account article content generator reads the article list generated by the collector, visits each article page, extracts metadata and analyzes with LLM:

1. Parse the Markdown file generated by collector
2. For each article:
   - Get article HTML content
   - Extract metadata (title, author, publish time, cover image, body text, etc.)
   - Use LLM to generate content overview (100-200 words), recommendation score (0-5 stars), and selection rationale (within 100 words)
3. Sort all articles by score in descending order
4. Filter recommended articles (3+ stars, or top 3 if insufficient)
5. Generate HTML content using rich-text template
6. Save to `output/daily_rich_text_YYYYMMDD.html`

**Command Line**:

```bash
# Automatically find today's article list file
uv run main.py --workflow generate

# Or specify a specific article list file
uv run main.py --workflow generate --markdown-file output/articles_20260126.md
```

**Report Format**:

- **Content Overview**: 100-200 word summary of core article content
- **Selection Rationale**: Up to 100 words explaining recommendation reason and value
- **Scoring Mechanism**: Only articles with 3+ stars are recommended
- **Attribution**: Footer automatically adds "Generated by Double童发发's wechat-ai-daily"

---

### Step 3: Draft Publishing

Automatically create drafts via WeChat Official Account API, no manual copy-paste needed:

1. Read generated official account article content HTML file
2. Convert HTML to WeChat Official Account format
3. Upload cover image and cache media_id
4. Call WeChat official API to create draft
5. After successful creation, draft can be viewed in WeChat MP draft box

**Command Line**:

```bash
# Automatically find today's official account article content HTML file
uv run main.py --workflow publish

# Or specify a specific official account article content HTML file
uv run main.py --workflow publish --html-file output/daily_rich_text_20260126.html
```

**Note**:

- After draft creation, manual confirmation is still required in WeChat MP
- Official auto-publishing feature is under development...

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run a single test file
uv run pytest tests/test_tt.py -v
```

## 📁 Project Structure

```
wechat-ai-daily/
├── src/wechat_ai_daily/
│   ├── utils/                    # Utility modules
│   │   ├── wechat/              # WeChat related tools (v2.0.0 modularization)
│   │   │   ├── __init__.py
│   │   │   ├── process.py       # WeChat process management and window control
│   │   │   ├── base_client.py   # API client base class
│   │   │   ├── article_client.py  # Article collection API client
│   │   │   ├── publish_client.py  # Draft publishing API client
│   │   │   └── exceptions.py    # WeChat API exception classes
│   │   ├── autogui.py           # GUI automation operations
│   │   ├── vlm.py               # VLM image recognition
│   │   ├── llm.py               # LLM summary generation
│   │   ├── env_loader.py        # Environment variable loader
│   │   ├── types.py             # Data type definitions
│   │   └── paths.py             # Path management tool
│   └── workflows/                # Workflow modules
│       ├── base.py              # Workflow base class
│       ├── rpa_article_collector.py    # RPA mode collector
│       ├── api_article_collector.py    # API mode collector (New in v2.0.0)
│       ├── daily_generate.py    # Official account article content generator
│       └── daily_publish.py     # Auto-publishing workflow
├── gui/                          # Desktop client module
│   ├── main_window.py           # Main window
│   ├── theme_manager.py         # Theme manager (New in v2.0.0)
│   ├── styles.py                # Style definitions
│   ├── panels/                  # UI panel components
│   │   ├── config_panel.py      # Configuration panel
│   │   ├── progress_panel.py    # Progress panel
│   │   └── log_panel.py         # Log panel
│   ├── workers/                 # Background worker threads
│   │   └── workflow_worker.py   # Workflow executor
│   └── utils/                   # Client utility classes
│       ├── config_manager.py    # Configuration manager
│       └── log_handler.py       # Log handler
├── scripts/                      # Build scripts
│   ├── build_windows.bat        # Windows build script
│   └── build_macos.sh           # macOS build script
├── configs/                      # Configuration files
│   └── config.yaml              # Main configuration file
├── templates/                    # Template files
│   ├── rich_text_template.html  # Rich text HTML template
│   ├── default_cover.png        # Default cover image
│   └── ...                      # GUI template images
├── tests/                        # Test files
│   ├── test_api_full_workflow.py  # API mode full workflow test
│   └── ...
├── main.py                       # Command line entry
└── app.py                        # Desktop client entry
```

## 🛠️ Tech Stack

- **GUI Automation**: pyautogui, pynput
- **Image Processing**: Pillow, OpenCV
- **VLM/LLM**: Alibaba Cloud DashScope (Qwen)
- **HTML Parsing**: BeautifulSoup4
- **Data Validation**: Pydantic
- **Desktop Client**: PyQt6
- **Environment Variables**: python-dotenv
- **Configuration Management**: ruamel-yaml

## ⚠️ Notes

- Make sure the WeChat desktop client is logged in before running
- Do not operate the mouse and keyboard during the collection process
- Different systems require corresponding template images (`templates/` directory)
- High-resolution display scaling (e.g., Retina) is automatically handled

## 📞 Support

If you encounter any issues or have suggestions, please submit feedback via [GitHub Issues](https://github.com/TongTong313/wechat-ai-daily/issues).

## ⚠️ IMPORTANT LEGAL NOTICE

**This project is for PERSONAL, EDUCATIONAL, AND NON-COMMERCIAL USE ONLY.**

### Risk Disclaimer

1. **API Mode Risks**:
   - API mode uses **unofficial WeChat MP backend interfaces**
   - Requires obtaining cookie and token via browser developer tools (F12)
   - These operations may **violate WeChat Platform Service Agreement**
   - Cookie/token should only be used for your own official account, not for others' accounts

2. **RPA Mode Risks**:
   - RPA mode's GUI automation operations may violate WeChat user agreements
   - Frequent automated operations may lead to account restrictions or bans

3. **User Responsibility**:
   - Users assume all consequences arising from using this tool
   - The author is NOT liable for any damages or legal issues caused by using this tool
   - Ensure you have legal access rights to the relevant official accounts before use
   - Comply with WeChat platform service terms and applicable laws

4. **Data Usage Guidelines**:
   - Collected data is for personal use only, NOT for resale or commercial purposes
   - Respect original authors' copyrights; collected content is for personal learning reference only

**IF YOU DO NOT AGREE TO THE ABOVE TERMS, STOP USING THIS TOOL IMMEDIATELY. Continued use indicates that you have read, understood, and agreed to comply with these terms.**

## 📄 License

MIT License - See [LICENSE](../LICENSE) file for details

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=TongTong313/wechat-ai-daily&type=Date)](https://star-history.com/#TongTong313/wechat-ai-daily&Date)
