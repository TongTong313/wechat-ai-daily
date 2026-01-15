"""
测试跨线程消息推送

验证 ProgressReporter 能否从主线程向服务器线程的 WebSocket 推送消息
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
from frontend.logging_handler import setup_logging_forwarding

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(threadName)-12s] - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def simulate_rpa_in_main_thread(reporter):
    """在主线程中模拟 RPA 操作（没有 asyncio 事件循环）"""
    logger.info("=" * 60)
    logger.info("开始在主线程中模拟 RPA 操作")
    logger.info("=" * 60)
    
    # 配置日志转发
    handler = setup_logging_forwarding(reporter)
    
    try:
        # 模拟各种操作
        logger.info("步骤1: 打开微信应用...")
        time.sleep(1)
        reporter.send_status("正在打开微信", "使用 GUI 自动化操作")
        
        logger.info("步骤2: 微信已激活")
        time.sleep(1)
        reporter.send_progress(1, 3)
        
        logger.info("步骤3: 正在搜索公众号...")
        time.sleep(1)
        reporter.send_status("正在搜索公众号", "URL: https://mp.weixin.qq.com/...")
        
        logger.info("步骤4: 使用 VLM 识别文章位置...")
        time.sleep(1)
        reporter.send_progress(2, 3)
        
        logger.info("步骤5: 识别到 3 个文章位置")
        logger.warning("这是一条警告日志")
        time.sleep(1)
        
        logger.info("步骤6: 采集文章链接...")
        reporter.send_article(
            link="https://mp.weixin.qq.com/s/test123abc",
            title="测试文章标题1"
        )
        time.sleep(1)
        reporter.send_progress(3, 3)
        
        logger.info("步骤7: 采集完成")
        time.sleep(1)
        
        # 发送完成信号
        reporter.send_workflow_end(
            success=True,
            stats={
                'total_accounts': 1,
                'success_accounts': 1,
                'total_articles': 1
            }
        )
        
        logger.info("=" * 60)
        logger.info("主线程模拟完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"模拟过程出错: {e}", exc_info=True)
    finally:
        from frontend.logging_handler import remove_logging_forwarding
        remove_logging_forwarding(handler)


def start_server_thread(reporter):
    """在后台线程启动服务器"""
    def run_server():
        logger.info("服务器线程启动")
        start_server(host="127.0.0.1", port=8765, reporter=reporter)
    
    thread = threading.Thread(target=run_server, name="ServerThread", daemon=True)
    thread.start()
    
    # 等待服务器启动并注入事件循环
    time.sleep(3)
    
    # 检查事件循环是否已注入
    if reporter.server_loop is not None:
        logger.info(f"✓ 事件循环已成功注入到 ProgressReporter: {reporter.server_loop}")
    else:
        logger.error("✗ 事件循环未注入到 ProgressReporter")
    
    return thread


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("跨线程消息推送测试")
    print("=" * 70)
    print("\n这个测试验证:")
    print("  1. 主线程（无 asyncio 循环）能否推送消息到服务器线程")
    print("  2. WebSocket 能否正确接收并转发消息到前端")
    print("  3. 日志拦截和转发是否正常工作")
    
    # 1. 创建 ProgressReporter（此时还没有服务器循环）
    print("\n[1] 创建 ProgressReporter...")
    reporter = ProgressReporter()
    print(f"  ✓ 创建成功")
    print(f"  - server_loop: {reporter.server_loop}")
    
    # 2. 启动服务器（在后台线程）
    print("\n[2] 启动前端服务器...")
    start_server_thread(reporter)
    print(f"  ✓ 服务器已启动: http://localhost:8765")
    print(f"  - server_loop: {reporter.server_loop}")
    
    # 3. 提示用户打开浏览器
    print("\n[3] 请在浏览器中打开: http://localhost:8765")
    print("     等待 5 秒让你准备...")
    for i in range(5, 0, -1):
        print(f"     {i}...", end="\r")
        time.sleep(1)
    print("\n")
    
    # 4. 发送启动信号
    print("[4] 发送工作流启动信号...")
    reporter.send_workflow_start(1)
    print("  ✓ 已发送")
    time.sleep(1)
    
    # 5. 在主线程中模拟 RPA 操作
    print("\n[5] 开始在主线程中模拟 RPA 操作...")
    print("     (注意：主线程没有 asyncio 事件循环)")
    print()
    simulate_rpa_in_main_thread(reporter)
    
    # 6. 保持运行
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)
    print("\n请检查浏览器前端页面：")
    print("  ✓ 是否显示了所有日志？")
    print("  ✓ 是否显示了进度条更新？")
    print("  ✓ 是否显示了操作状态？")
    print("  ✓ 是否显示了采集的文章？")
    print("  ✓ 是否显示了完成统计？")
    print("\n服务器将继续运行，按 Ctrl+C 退出...\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n退出程序")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被中断")
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
