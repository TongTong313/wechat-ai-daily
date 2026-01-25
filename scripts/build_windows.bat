@echo off
chcp 65001 >nul
echo ========================================
echo   微信 AI 日报助手 - Windows 打包脚本
echo ========================================
echo.

:: 检查是否在项目根目录
if not exist "app.py" (
    echo [错误] 请在项目根目录运行此脚本
    echo 示例: scripts\build_windows.bat
    pause
    exit /b 1
)

:: 检查 pyinstaller 是否安装
echo [1/3] 检查 pyinstaller...
uv run python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [信息] 正在安装 pyinstaller...
    uv add pyinstaller --dev
    if errorlevel 1 (
        echo [错误] 安装 pyinstaller 失败
        pause
        exit /b 1
    )
)
echo [√] pyinstaller 已就绪

:: 创建输出目录
echo.
echo [2/3] 准备打包环境...
if not exist "dist" mkdir dist
if not exist "build" mkdir build

:: 执行打包
echo.
echo [3/3] 开始打包...
echo.
uv run pyinstaller --name "微信AI日报助手" ^
    --windowed ^
    --onefile ^
    --add-data "%cd%\configs;configs" ^
    --add-data "%cd%\templates;templates" ^
    --hidden-import "wechat_ai_daily" ^
    --hidden-import "wechat_ai_daily.workflows" ^
    --hidden-import "wechat_ai_daily.utils" ^
    --distpath "%cd%\dist" ^
    --workpath "%cd%\build" ^
    --specpath "%cd%\build" ^
    app.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo ========================================
echo   打包完成！
echo ========================================
echo.
echo 可执行文件位置: dist\微信AI日报助手.exe
echo.
echo 注意事项:
echo   1. 首次运行需要配置 configs\config.yaml
echo   2. 确保 templates\ 目录中的模板图片正确
echo   3. 部分杀毒软件可能误报，请添加信任
echo.
pause
