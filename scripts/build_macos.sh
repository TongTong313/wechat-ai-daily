#!/bin/bash

echo "========================================"
echo "  微信 AI 日报助手 - macOS 打包脚本"
echo "========================================"
echo

# 获取脚本所在目录，切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 检查是否在项目根目录
if [ ! -f "app.py" ]; then
    echo "[错误] 请在项目根目录运行此脚本"
    echo "示例: ./scripts/build_macos.sh"
    exit 1
fi

# 检查 pyinstaller 是否安装
echo "[1/3] 检查 pyinstaller..."
if ! uv run python -c "import PyInstaller" 2>/dev/null; then
    echo "[信息] 正在安装 pyinstaller..."
    uv add pyinstaller --dev
    if [ $? -ne 0 ]; then
        echo "[错误] 安装 pyinstaller 失败"
        exit 1
    fi
fi
echo "[√] pyinstaller 已就绪"

# 创建输出目录
echo
echo "[2/3] 准备打包环境..."
mkdir -p dist
mkdir -p build

# 执行打包
echo
echo "[3/3] 开始打包..."
echo
uv run pyinstaller --name "微信AI日报助手" \
    --windowed \
    --onefile \
    --add-data "configs:configs" \
    --add-data "templates:templates" \
    --hidden-import "wechat_ai_daily" \
    --hidden-import "wechat_ai_daily.workflows" \
    --hidden-import "wechat_ai_daily.utils" \
    --distpath dist \
    --workpath build \
    --specpath build \
    app.py

if [ $? -ne 0 ]; then
    echo
    echo "[错误] 打包失败，请检查错误信息"
    exit 1
fi

echo
echo "========================================"
echo "  打包完成！"
echo "========================================"
echo
echo "应用位置: dist/微信AI日报助手.app"
echo
echo "注意事项:"
echo "  1. 首次运行需要配置 configs/config.yaml"
echo "  2. 确保 templates/ 目录中的模板图片正确"
echo "  3. 首次运行需要在「系统偏好设置 → 安全性与隐私 → 辅助功能」中授权"
echo
