# Changelog

This document records all significant changes to this project.

## v2.1.1 - 2026-01-30

Minor update: Improved API time-range workflow, richer HTML normalization, and smoother GUI interactions.

### Enhancements

- **CLI time-range parameters** (`main.py`)
  - Added `--start-date` / `--end-date` for minute-level filtering in API mode
  - Accepts `YYYY-MM-DD` and `YYYY-MM-DD HH:mm`, auto-fills time and validates range

- **HTML normalization for publishing** (`utils/wechat/html_normalizer.py` / `workflows/daily_generate.py` / `workflows/daily_publish.py`)
  - Removes whitespace nodes and resets block margins/padding to avoid spacing anomalies
  - Adds unique separator identifiers to prevent WeChat merging
  - API-mode HTML output filename includes time range

### UX Improvements

- **Output file list refresh** (`gui/main_window.py`)
  - Auto-refresh on dropdown open and window activation to show new files

### Generation Tweaks

- **Article filtering and summary logs** (`workflows/daily_generate.py`)
  - Filters API articles by time range and logs progress per article
  - Refined scoring penalties for unrealistic and marketing-heavy content

---

## v2.1.0 - 2026-01-29

**Enhancement**: API mode now supports time range filtering precise to the minute, improving article collection flexibility.

### New Features

- **API Mode Time Range Filtering** (`workflows/api_article_collector.py`)
  - Added `start_date` and `end_date` configuration options, supporting minute-level precision
  - Configuration format: `YYYY-MM-DD HH:mm` (e.g., `2026-01-28 08:00`)
  - Output file naming format updated to `articles_YYYYMMDD_HHmm_YYYYMMDD_HHmm.md`

- **ArticleClient New Method** (`utils/wechat/article_client.py`)
  - `get_articles_by_range()`: Fetch articles by time range using timestamp comparison

- **GUI Time Range Selector** (`gui/panels/config_panel.py`)
  - API mode: Shows start time and end time selectors (date + time)
  - RPA mode: Keeps the original single date selector
  - Added "Today All Day" and "Yesterday All Day" quick buttons

### Configuration Changes

- **New config.yaml options**:
  - `start_date`: API mode start time (format: `YYYY-MM-DD HH:mm`)
  - `end_date`: API mode end time (format: `YYYY-MM-DD HH:mm`)
  - `target_date`: RPA mode only (format: `YYYY-MM-DD`)

### Documentation Updates

- **README.md**: Updated collection time configuration instructions, distinguishing RPA and API modes
- **CLAUDE.md**: Updated configuration file description and workflow documentation
- **Test cases**: Updated `test_api_full_workflow.py` to use new time range configuration

---

## v2.0.1 - 2026-01-29

Minor update: Fixed startup path issues and optimized article scoring logic.

### Bug Fixes

- **Desktop Client Startup Path Fix** (`app.py`)
  - Fixed relative path failure when starting from non-application directory
  - Fixed log file path issue caused by using relative paths

### Feature Improvements

- **Article Scoring Rules Restructured** (`workflows/daily_generate.py`)
  - Adopted clearer "Base Points + Bonus Points + Penalty Points" scoring structure
  - Base points (max 3): AI domain content, content quality, practical value
  - Bonus points: Notable institutions/figures, trending topics
  - Penalty points: Non-AI content, AI-generated traces, promotional content
  - Overall pass rate controlled under 50% for better recommendation quality

- **LLM Configuration Optimization**
  - Text model options simplified to `qwen-plus` and `qwen3-max`
  - `enable_thinking` default changed to `False` for faster generation

### Documentation Fixes

- **`.env.example`**: Corrected configuration priority description, clarifying .env file takes precedence over system environment variables

---

## v2.0.0 - 2026-01-27

**Major Update**: Added API mode for article collection, providing both RPA and API collection modes, with command-line support for complete Collect → Generate → Publish workflow, and comprehensive optimization of sensitive data configuration management.

### New Features

- **API Mode Article Collection** (`workflows/api_article_collector.py`)
  - `APIArticleCollector` workflow: Collect articles via WeChat MP backend API
  - More efficient and stable compared to RPA mode
  - Search accounts by name, no article URL needed
  - Filter articles by date

- **WeChat MP API Client** (`utils/wechat/article_client.py`)
  - `ArticleClient` class: WeChat MP backend API client
  - `search_account()`: Search official accounts, get fakeid
  - `get_article_list()`: Get article list
  - `get_all_articles()`: Paginated article retrieval
  - `get_articles_by_date()`: Get articles by specific date

- **Command-Line Full Workflow Support** (`main.py`)
  - Support RPA and API collection modes (`--mode rpa/api`)
  - Support four workflow types (`--workflow collect/generate/publish/full`)
    - `collect`: Collect articles only
    - `generate`: Generate official account article content only
    - `publish`: Publish draft only
    - `full`: Full workflow (Collect → Generate → Publish)
  - Support specifying existing files (`--markdown-file`, `--html-file`)
  - Auto-detect intermediate output files for current date
  - Feature parity with desktop client

- **Data Type Optimization** (`utils/types.py`)
  - `ArticleMetadata` supports progressive filling (API phase 1 + HTML parsing phase 2)
  - New `AccountMetadata` data class for account info
  - New `from_api_response()` factory method

- **Unified Sensitive Data Management** (GUI Client)
  - Added global "Sensitive Data Save Mode" settings card
  - Provides "Save to .env file (Recommended)" and "Save to config.yaml" options
  - Unified management of all sensitive data save behavior
  - Added "Open .env file" button for easy direct editing

- **.env File Manager** (`gui/utils/env_file_manager.py`)
  - `EnvFileManager` class: Complete .env file read/write functionality
  - Preserves comments and formatting
  - Provides `update()`, `create()`, `remove()`, `detect_source()` methods
  - Auto-detects configuration source (config.yaml / .env file / system environment variables)

### Feature Improvements

- **Configuration Priority Adjustment** (Breaking Change)
  - **New Sensitive Information Configuration Priority** (High to Low):
    1. **config.yaml file** (Highest priority)
    2. **.env file** (Recommended, automatically added to .gitignore)
    3. **System environment variables** (Lowest priority)
  - **Note**: When config.yaml value is null or empty string, it's treated as unset and will read from environment variables
  - **Impact Scope**: All sensitive configurations (API Key, Token, Cookie, AppID, AppSecret)

- Original `ArticleCollector` in `workflows/wechat_autogui.py` renamed to `RPAArticleCollector`, moved to `workflows/rpa_article_collector.py`
- New `workflows/api_article_collector.py`: `APIArticleCollector` (API mode)
- `DailyGenerator` compatible with output from both collectors
- Original `utils/wechat.py` split into multiple modules:
  - `utils/wechat/process.py`: WeChat process management
  - `utils/wechat/article_client.py`: Article collection API client
  - `utils/wechat/publish_client.py`: Draft publishing API client
  - `utils/wechat/base_client.py`: API client base class
  - `utils/wechat/exceptions.py`: WeChat API exception classes
- New `utils/paths.py`: Path management tool, compatible with PyInstaller packaging environment
- New `gui/theme_manager.py`: Theme manager, supports dark/light theme switching
- New `gui/utils/env_file_manager.py`: .env file manager, supports secure environment variable management

### Security Improvements

- **Prevent Environment Variables from Leaking to Config File**
  - When users select "Save to .env file" mode, sensitive data is only written to .env file
  - Sensitive fields in config.yaml remain null
  - Avoid accidentally committing environment variable values to version control

- **Configuration Source Visualization**
  - GUI interface displays source of each sensitive data item (config.yaml / .env file / system environment variables)
  - Helps users understand current configuration source

### Documentation Updates

- **README.md / docs/README_en.md**
  - Updated command-line instructions with all parameter descriptions
  - Added "One-Click Full Workflow" and "Step-by-Step Execution" examples
  - Added "Command Line Parameters" reference table
  - Restructured "Workflow" section with detailed three-step process
  - Clarified feature parity between command-line and desktop client
  - **Updated configuration priority description**: config.yaml > .env file > system environment variables

- **CLAUDE.md**
  - Updated project overview with dual-mode collection description
  - Updated main program execution section with command-line parameters
  - Updated core module structure reflecting architecture changes
  - Added command-line full workflow documentation
  - **Updated configuration priority description** and environment variable management instructions

### Test Updates

- New `tests/test_api_full_workflow.py`: API mode full workflow test
- New `tests/test_config_priority.py`: Configuration priority and privacy protection test (formerly `test_config_privacy.py`)
- Removed `tests/test_api_daily_workflow.py`, `tests/test_daily_generate_workflow.py`, `tests/test_daily_publish.py`: Cleaned up obsolete test files, unified test structure

---

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
  - New HTML file selector for publishing generated official account article content
  - Action button area changed to scrollable for more options
  - `WorkflowWorker` adds `WorkflowType` enum with 4 workflow types:
    - `COLLECT`: Collect articles only
    - `GENERATE`: Generate official account article content only
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

Official open-source release, implementing a complete workflow for automated WeChat Official Account article collection and official account article content generation.

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
  - Evaluate article recommendation score (0-5 stars)
  - Generate selection rationale within 100 words

- **Official Account Article Content Generation**: Automatically generate rich-text HTML content
  - Automatically collect all articles published today from specified official accounts
  - Filter high-quality articles by score (3+ stars or top 3)
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
