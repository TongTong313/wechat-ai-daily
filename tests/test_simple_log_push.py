"""
最简单的日志推送测试

验证：从主线程（无事件循环）向服务器线程推送日志是否成功
"""

import sys
import time
import logging
import threading
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend.progress_reporter import ProgressReporter
from frontend.server import start_server

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(threadName)-12s] - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_direct_push(reporter):
    """直接测试推送功能"""
    logger.info("=" * 60)
    logger.info("开始测试直接推送")
    logger.info(f"当前线程: {threading.current_thread().name}")
    logger.info(f"Reporter.server_loop: {reporter.server_loop}")
    logger.info("=" * 60)
    
    # 测试1: 直接调用 send_log
    print("\n[测试1] 直接调用 send_log...")
    reporter.send_log("info", "这是一条测试日志 - 来自主线程")
    print("  ✓ send_log 调用完成（不阻塞）")
    time.sleep(0.5)
    
    # 测试2: 多条日志
    print("\n[测试2] 发送多条不同级别的日志...")
    reporter.send_log("info", "INFO 级别日志")
    reporter.send_log("warning", "WARNING 级别日志")
    reporter.send_log("error", "ERROR 级别日志")
    reporter.send_log("success", "SUCCESS 级别日志")
    print("  ✓ 所有日志已发送")
    time.sleep(1)
    
    # 测试3: 发送状态
    print("\n[测试3] 发送操作状态...")
    reporter.send_status("正在打开微信", "使用 GUI 自动化")
    time.sleep(0.5)
    reporter.send_status("VLM 识别中", "识别文章日期位置")
    print("  ✓ 状态已发送")
    time.sleep(1)
    
    # 测试4: 发送进度
    print("\n[测试4] 发送进度更新...")
    for i in range(1, 6):
        reporter.send_progress(i, 5)
        print(f"  - 进度: {i}/5")
        time.sleep(0.5)
    print("  ✓ 进度已更新")
    
    # 测试5: 发送文章
    print("\n[测试5] 发送文章链接...")
    reporter.send_article(
        link="https://mp.weixin.qq.com/s/test123abc",
        title="测试文章标题"
    )
    print("  ✓ 文章已发送")
    time.sleep(1)
    
    logger.info("=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)


def start_server_thread(reporter):
    """在后台线程启动服务器"""
    def run_server():
        logger.info("服务器线程启动")
        start_server(host="127.0.0.1", port=8765, reporter=reporter)
    
    thread = threading.Thread(target=run_server, name="ServerThread", daemon=True)
    thread.start()
    
    # 等待服务器启动
    print("等待服务器启动（3秒）...")
    time.sleep(3)
    
    return thread


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("简单日志推送测试")
    print("=" * 70)
    
    # 1. 创建 ProgressReporter
    print("\n[步骤1] 创建 ProgressReporter...")
    reporter = ProgressReporter()
    print(f"  ✓ 创建成功")
    print(f"  - server_loop (创建时): {reporter.server_loop}")
    
    # 2. 启动服务器
    print("\n[步骤2] 启动前端服务器...")
    start_server_thread(reporter)
    print(f"  ✓ 服务器已启动: http://localhost:8765")
    print(f"  - server_loop (启动后): {reporter.server_loop}")
    
    # 验证事件循环注入
    if reporter.server_loop is None:
        print("\n  ❌ 错误：事件循环未注入到 ProgressReporter！")
        print("     这会导致跨线程推送失败")
        return
    else:
        print(f"  ✅ 事件循环已成功注入")
    
    # 3. 等待用户打开浏览器
    print("\n[步骤3] 请在浏览器中打开: http://localhost:8765")
    print("        准备好后按 Enter 继续...")
    input()
    
    # 4. 开始测试
    print("\n[步骤4] 开始测试推送功能...")
    print("        请观察浏览器前端页面是否显示日志")
    print()
    test_direct_push(reporter)
    
    # 5. 完成
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)
    print("\n请检查浏览器前端：")
    print("  ✓ 日志区域是否显示了所有测试日志？")
    print("  ✓ 不同级别的日志颜色是否正确？")
    print("  ✓ 操作状态是否更新？")
    print("  ✓ 进度条是否更新到 100%？")
    print("  ✓ 是否显示了采集的文章？")
    print("\n按 Ctrl+C 退出...\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n退出")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被中断")
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
