# Changelog

This document records all significant changes to this project.

## v1.2.0 - 2026-01-26

Added WeChat Official Account auto-publishing feature with official API support for draft creation, and optimized environment variable management.

### New Features

- **WeChat Official Account Auto-Publishing** (`workflows/daily_publish.py`)
  - `DailyPublisher` workflow: Create drafts via WeChat official API
  - Auto-convert HTML rich text to WeChat-compatible format
  - Auto-upload cover images with media_id caching to avoid duplicates
  - Support for author, digest and other draft configurations

- **WeChat Official Account API Client** (New `WeChatAPI` class in `utils/wechat.py`)
  - Auto access_token retrieval and caching (using stable API, no IP whitelist required)
  - Draft management: create, get, update, delete, list
  - Publishing management: publish draft, query status, delete published articles
  - Media management: upload permanent media, upload images for articles

- **Environment Variable Management Optimization**
  - Added `.env` file support (`utils/env_loader.py`)
  - Configuration priority: config.yaml > System env vars > .env file
  - Added `.env.example` template file
  - Added `tests/diagnose_env.py` environment diagnostic script

- **Workflow Architecture Optimization**
  - Added `BaseWorkflow` abstract base class (`workflows/base.py`)
  - Unified workflow interface: `build_workflow()` and `run()`

- **Desktop Client Enhancement** (`gui/` module)
  - Main window adds Step 3 "Publish Draft", complete workflow becomes: Collect → Generate → Publish
  - One-click full workflow button now supports complete 3-stage automatic execution
  - New HTML file selector for publishing generated daily reports
  - Action button area changed to scrollable for more options
  - `WorkflowWorker` adds `WorkflowType` enum with 4 workflow types:
    - `COLLECT`: Collect articles only
    - `GENERATE`: Generate daily report only
    - `PUBLISH`: Publish draft only
    - `FULL`: Full workflow (Collect + Generate + Publish)
  - `ConfigPanel` adds publish configuration card for AppID, AppSecret, author, cover image, default title
  - `ConfigManager` adds publish config management methods with credential source status display

### Configuration Updates

- Added `publish_config` section in `config.yaml`:
  - `appid`: Official Account AppID (supports WECHAT_APPID env var)
  - `appsecret`: Official Account AppSecret (supports WECHAT_APPSECRET env var)
  - `cover_path`: Cover image path
  - `media_id`: Cover image media_id (auto-cached)
  - `author`: Author name

### Dependency Updates

- Added `python-dotenv>=1.2.1`: .env file loading
- Added `ruamel-yaml>=0.18.0`: YAML read/write with comment preservation

### Test Updates

- Added `tests/test_daily_publish.py`: Auto-publishing workflow tests
- Added `tests/diagnose_env.py`: Environment variable diagnostic tool
- Cleaned up obsolete test files

## v1.1.0 - 2026-01-25

Enhanced desktop client experience with complete graphical interface application and executable packaging support.

### New Features

- **PyQt6 Desktop Client** (`app.py` and `gui/` module)
  - Main window interface (MainWindow): Integrates configuration, progress, and log panels
  - Configuration panel (ConfigPanel):
    - Date selector (Today/Yesterday/Custom date)
    - Article link management (Add/Delete/Load from config)
    - API Key settings (Support saving to config file)
  - Progress panel (ProgressPanel):
    - Real-time status display (Ready/Running/Completed/Failed)
    - Progress bar feedback
  - Log panel (LogPanel):
    - Real-time log output (Auto-scroll)
    - Log level filtering
  - Background worker thread (WorkflowWorker): Avoid UI blocking

- **Executable Packaging Support**
  - Windows build script (`scripts/build_windows.bat`)
    - Auto-detect and install pyinstaller
    - One-click generate `dist/微信AI日报助手.exe`
  - macOS build script (`scripts/build_macos.sh`)
    - Auto-detect and install pyinstaller
    - One-click generate `dist/微信AI日报助手.app`
  - Run without Python environment after packaging

- **Configuration Management Optimization**
  - ConfigManager class: Unified config file read/write management
  - Automatically select GUI template paths based on OS (Windows/macOS)
  - Support saving config from GUI to `configs/config.yaml`

- **Enhanced Log Handling**
  - QTextEditLogHandler: Redirect logging to Qt signals
  - Support real-time log display and auto-scroll

### Improvements

- Optimized workflow execution logic with background thread support
- Improved error handling and user prompts
- Enhanced cross-platform compatibility

### Documentation Updates

- Updated README.md and docs/README_en.md with desktop client usage instructions
- Updated CLAUDE.md with GUI module architecture documentation
- Added packaging script usage documentation

## v1.0.0 - 2026-01-25

Official open-source release, implementing a complete workflow for automated WeChat Official Account article collection and daily AI content report generation.

### New Features

- **GUI Automated Collection**: Support for automatic WeChat opening, official account search, and article link collection
  - Precise clicking based on template image matching
  - Support for page scrolling and screenshot functionality
  - Automatic WeChat window detection and activation

- **VLM Intelligent Recognition**: Integrated Alibaba Cloud DashScope Vision-Language Model
  - Automatically identify date positions on official account pages to precisely locate today's articles
  - Automatically handle high-resolution display scaling (Retina, etc.)

- **LLM Content Analysis**: Integrated Alibaba Cloud DashScope Large Language Model
  - Automatically extract article metadata (title, author, publish time, content, images, etc.)
  - Generate 100-200 word content overview
  - Evaluate article recommendation score (0-100 points)
  - Generate selection rationale within 100 words

- **Daily Report Generation**: Automatically generate rich-text HTML daily report
  - Automatically collect all articles published today from specified official accounts
  - Filter high-quality articles by score (90+ points or top 3)
  - Support one-click copy and paste to official account editor
  - Support for custom HTML template

- **Cross-Platform Support**: Support for both Windows and macOS systems
  - Automatically detect operating system type
  - Support platform-specific template image configuration

### Configuration Features

- Support for YAML configuration file (`configs/config.yaml`)
- Support for environment variable configuration (DASHSCOPE_API_KEY)
- Support for custom template image paths
- Support for model parameter configuration (model, thinking_budget, enable_thinking, etc.)

### Documentation

- Bilingual README (Chinese `README.md` and English `docs/README_en.md`)
- Developer guide (`CLAUDE.md`)
- Frontend monitoring documentation (`frontend/README.md`)
