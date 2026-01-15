#!/bin/bash

# 前端监控快速启动脚本
# 用法：./start_frontend_test.sh [mode]
#   mode: simulation  - 模拟测试（无需微信）
#   mode: real        - 真实测试（需要微信环境）
#   默认: simulation

MODE=${1:-simulation}

echo "======================================================================"
echo "  微信公众号自动化 - 前端监控测试"
echo "======================================================================"
echo ""

if [ "$MODE" = "simulation" ]; then
    echo "📋 模式：模拟测试（无需微信环境）"
    echo ""
    echo "💡 提示："
    echo "  1. 脚本将启动前端服务器: http://localhost:8765"
    echo "  2. 请在浏览器中打开上述地址"
    echo "  3. 观察前端页面的实时更新"
    echo "  4. 按 Ctrl+C 停止测试"
    echo ""
    echo "启动中..."
    echo ""
    
    uv run python tests/test_frontend_integration.py
    
elif [ "$MODE" = "real" ]; then
    echo "🚀 模式：真实测试（需要微信环境）"
    echo ""
    echo "⚠️  重要提示："
    echo "  1. 确保微信已登录"
    echo "  2. 浏览器将自动打开监控页面"
    echo "  3. 建议将浏览器窗口移到副屏"
    echo "  4. 在前端页面点击 [▶️ 开始测试] 按钮"
    echo "  5. 测试期间不要操作鼠标/键盘"
    echo ""
    echo "启动中..."
    echo ""
    
    uv run python tests/test_with_frontend.py
    
else
    echo "❌ 错误：未知模式 '$MODE'"
    echo ""
    echo "用法："
    echo "  ./start_frontend_test.sh simulation   # 模拟测试"
    echo "  ./start_frontend_test.sh real         # 真实测试"
    exit 1
fi
