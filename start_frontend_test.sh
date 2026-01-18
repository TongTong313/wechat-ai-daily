#!/bin/bash

# 前端监控快速启动脚本
# 用法：
#   ./start_frontend_test.sh                # 不自动打开浏览器
#   ./start_frontend_test.sh --open-browser # 自动打开浏览器

echo "======================================================================"
echo "  微信公众号自动化 - 前端监控测试"
echo "======================================================================"
echo ""
echo "🚀 启动带前端监控的真实测试"
echo ""
echo "⚠️  重要提示："
echo "  1. 确保微信已登录"
echo "  2. 监控页面地址: http://localhost:8765"
echo "  3. 如需自动打开浏览器，请使用: ./start_frontend_test.sh --open-browser"
echo "  4. 建议将浏览器窗口移到副屏"
echo "  5. 在前端页面点击 [▶️ 开始测试] 按钮启动测试"
echo "  6. 测试期间不要操作鼠标/键盘"
echo "  7. 可以在前端点击 [⏹️ 停止] 按钮中断测试"
echo ""
echo "启动中..."
echo ""

# 将所有命令行参数传递给 Python 脚本
uv run python tests/test_with_frontend.py "$@"
