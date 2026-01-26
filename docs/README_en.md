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

## 📖 Introduction

An automated WeChat Official Account article collection tool that uses GUI automation and VLM (Vision Language Model) image recognition to automatically collect daily articles from specified official accounts, and generates daily AI content reports using LLM. The generated HTML file can be opened and copied with one click to directly form the content of your own official account article.

Due to strict anti-crawler restrictions on WeChat Official Account article lists, traditional web scraping solutions are difficult to implement. This project adopts a **GUI Automation + VLM Image Recognition** hybrid approach, simulating real user operations to bypass restrictions and obtain article information.

This project was developed with the assistance of AI Coding tools. Special thanks to [Claude Code](https://claude.ai/code), [Cursor](https://cursor.com/), and other AI Coding tools.

## 🎯 Core Features

### v1.2.0: WeChat Auto-Publishing

- **WeChat Auto-Publishing**: Create drafts via official API
  - Based on WeChat official API, no manual copy-paste needed
  - Auto-convert HTML rich text to WeChat format
  - Auto-upload cover images with caching
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
- **Daily Report Generation**: Aggregates all articles and generates rich-text daily reports ready for publishing
- **One-Click Publishing**: Open the generated HTML file, copy and paste to form your official account content
- **Cross-Platform Support**: Supports both Windows and macOS systems

## 📋 Requirements

- Python >= 3.13
- WeChat Desktop Client (Windows or macOS)
- Alibaba Cloud DashScope API Key (for VLM image recognition and LLM summary generation)
- Only supports Windows and macOS systems

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

**Configuration Priority Note**: When `api_key` is null, the system reads from environment variable `DASHSCOPE_API_KEY`. If a value is specified in the config file, it takes priority.

```yaml
model_config:
  LLM:
    model: qwen-plus
    api_key: null # When null, reads DASHSCOPE_API_KEY from environment; otherwise uses this value
    thinking_budget: 1024
    enable_thinking: true
  VLM:
    model: qwen3-vl-plus
    api_key: null # When null, reads DASHSCOPE_API_KEY from environment; otherwise uses this value
    thinking_budget: 1024
    enable_thinking: true
```

#### Configure WeChat Publishing:

**Configuration Priority Note**: To avoid exposing credentials in the config file, set `appid` and `appsecret` to null, and the system will read from environment variables. If values are specified in the config file, they take priority.

```yaml
publish_config:
  appid: null # When null, reads WECHAT_APPID from environment; otherwise uses this value
  appsecret: null # When null, reads WECHAT_APPSECRET from environment; otherwise uses this value
  cover_path: templates/default_cover.png # Cover image path
  author: Double童发发 # Author name
```

#### Appendix: Environment Variable Setup

As stated above, if some fields in `configs/config.yaml` are `null` or empty, the following environment variables will be used. We strongly recommend storing these sensitive values in environment variables instead of writing them directly in the config file.

Related environment variables:

- `DASHSCOPE_API_KEY`: LLM API key (`model_config.LLM.api_key`, `model_config.VLM.api_key`)
- `WECHAT_APPID`: WeChat publishing (`publish_config.appid`)
- `WECHAT_APPSECRET`: WeChat publishing (`publish_config.appsecret`)

**Configuration Priority: config.yaml > Environment Variables (including system environment variables and .env file)**

Explanation:

- If the corresponding field in `config.yaml` has a value (not null), the config file value takes priority
- If the corresponding field in `config.yaml` is null or empty, the system reads from environment variables
- Environment variable precedence: System environment variables take priority over .env file

##### Method 1: Using .env File (Recommended)

This is the safest and most convenient method, suitable for long-term use:

```bash
# 1. Copy the template file
cp .env.example .env

# 2. Edit the .env file with your actual credentials
# WECHAT_APPID=your_appid_here
# WECHAT_APPSECRET=your_appsecret_here
# DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 3. Verify the configuration
uv run python tests/diagnose_env.py
```

**Advantages:**

- ✅ Sensitive information won't be committed to Git (`.env` is in `.gitignore`)
- ✅ No need to manually export each time, automatically loaded when the project starts
- ✅ Centralized configuration management, easy to maintain

##### Method 2: System Environment Variables

Suitable for global use or sharing configuration across multiple projects.

**macOS/Linux (zsh/bash):**

```bash
# Temporary (current terminal only)
export DASHSCOPE_API_KEY="your_api_key_here"
export WECHAT_APPID="your_wechat_appid_here"
export WECHAT_APPSECRET="your_wechat_appsecret_here"

# Permanent (add to ~/.zshrc or ~/.bashrc)
echo 'export DASHSCOPE_API_KEY="your_api_key_here"' >> ~/.zshrc
echo 'export WECHAT_APPID="your_wechat_appid_here"' >> ~/.zshrc
echo 'export WECHAT_APPSECRET="your_wechat_appsecret_here"' >> ~/.zshrc
source ~/.zshrc
```

**Windows PowerShell:**

```powershell
# Temporary (current session only)
$env:DASHSCOPE_API_KEY="your_api_key_here"
$env:WECHAT_APPID="your_wechat_appid_here"
$env:WECHAT_APPSECRET="your_wechat_appsecret_here"

# Permanent (system environment variable)
[System.Environment]::SetEnvironmentVariable("DASHSCOPE_API_KEY", "your_api_key_here", "User")
[System.Environment]::SetEnvironmentVariable("WECHAT_APPID", "your_wechat_appid_here", "User")
[System.Environment]::SetEnvironmentVariable("WECHAT_APPSECRET", "your_wechat_appsecret_here", "User")
```

**Windows CMD:**

```bat
# Temporary (current session only)
set DASHSCOPE_API_KEY=your_api_key_here
set WECHAT_APPID=your_wechat_appid_here
set WECHAT_APPSECRET=your_wechat_appsecret_here
```

### 4. Start Running and Wait for Results

**Important Note**: Please ensure WeChat is open to the main chat interface, close all other WeChat windows (official accounts, search), and place WeChat on the main screen, otherwise it may cause automation operations to fail.

#### Method 1: Command Line (Stable and Reliable)

```bash
uv run main.py
```

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

1. **Article Collection**: The program automatically opens WeChat, visits configured official account homepages, and collects all article links published today
2. **Content Extraction**: Visits each article page to extract title, author, body text, images, and other metadata
3. **Content Analysis**: Uses LLM to generate content overview, recommendation score, and selection rationale for each article
4. **Report Output**: Aggregates all articles and generates a rich-text daily report HTML file
5. **One-Click Publishing**: Open the generated HTML file, copy the content and paste it into the official account editor
6. **Report Format**:
   - **Content Overview**: 100-200 word summary of core article content
   - **Selection Rationale**: Up to 100 words explaining recommendation reason and value
   - **Scoring Mechanism**: Only articles with 90+ scores are recommended
   - **Attribution**: Footer automatically adds "Generated by Double童发发's wechat-ai-daily"

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
│   │   ├── wechat.py            # WeChat process management and API client
│   │   ├── autogui.py           # GUI automation operations
│   │   ├── vlm.py               # VLM image recognition
│   │   ├── llm.py               # LLM summary generation
│   │   ├── env_loader.py        # Environment variable loader
│   │   └── types.py             # Data type definitions
│   └── workflows/                # Workflow modules
│       ├── base.py              # Workflow base class
│       ├── wechat_autogui.py    # Official account article collector
│       ├── daily_generate.py    # Daily report generator
│       └── daily_publish.py     # Auto-publishing workflow
├── gui/                          # Desktop client module
│   ├── main_window.py           # Main window
│   ├── panels/                  # UI panel components
│   ├── workers/                 # Background worker threads
│   └── utils/                   # Client utility classes
├── scripts/                      # Build scripts
│   ├── build_windows.bat        # Windows build script
│   └── build_macos.sh           # macOS build script
├── configs/                      # Configuration files
├── templates/                    # Template files
├── tests/                        # Test files
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

## 📄 License

MIT License - See [LICENSE](../LICENSE) file for details

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=TongTong313/wechat-ai-daily&type=Date)](https://star-history.com/#TongTong313/wechat-ai-daily&Date)
