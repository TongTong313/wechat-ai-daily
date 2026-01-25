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

### v1.1.0: Enhanced Desktop Client Experience

- **PyQt6 Desktop Client**: Brand new graphical interface application
  - Visual configuration management (date selection, link management, API Key settings)
  - Real-time log display and progress bar feedback
  - One-click full workflow execution
- **Executable Packaging**: Support for packaging as standalone applications
  - Windows one-click build script (build_windows.bat)
  - macOS one-click build script (build_macos.sh)
  - Run without Python environment
- **Configuration Management Optimization**: Automatically select GUI template paths based on OS
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
  - https://mp.weixin.qq.com/s/ZrBDFuugPyuoQp4S6wEBWQ  # Any article URL from Machine Intelligence
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

```yaml
model_config:
  LLM:
    model: qwen-plus
    api_key: null # When null, reads DASHSCOPE_API_KEY from environment variable
    thinking_budget: 1024
    enable_thinking: true
  VLM:
    model: qwen3-vl-plus
    api_key: null
    thinking_budget: 1024
    enable_thinking: true
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
│   │   ├── wechat.py            # WeChat process management
│   │   ├── autogui.py           # GUI automation operations
│   │   ├── vlm.py               # VLM image recognition
│   │   ├── llm.py               # LLM summary generation
│   │   └── types.py             # Data type definitions
│   └── workflows/                # Workflow modules
│       ├── wechat_autogui.py    # Official account article collector
│       └── daily_generate.py    # Daily report generator
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
