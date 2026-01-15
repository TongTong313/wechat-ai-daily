"""
最小化测试：验证前端接口是否打通

测试内容：
1. WebSocket 连接
2. 日志推送
3. 状态识别
4. 进度统计
5. 截图推送（模拟）
"""

import sys
import asyncio
import logging
import threading
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend.progress_reporter import ProgressReporter
from frontend.server import start_server
from frontend.logging_handler import setup_logging_forwarding, remove_logging_forwarding


async def simulate_workflow(reporter):
    """模拟工作流，测试前端接口"""
    print("\n开始模拟工作流...")
    
    # 配置日志转发
    handler = setup_logging_forwarding(reporter)
    test_logger = logging.getLogger("test_workflow")
    
    try:
        # 发送工作流启动信号
        reporter.send_workflow_start(2)
        test_logger.info("开始执行公众号文章采集工作流")
        
        await asyncio.sleep(1)
        
        # 模拟打开微信
        test_logger.info("正在打开微信...")
        await asyncio.sleep(0.5)
        test_logger.info("微信应用已就绪")
        reporter.send_progress(1, 5)
        
        await asyncio.sleep(1)
        
        # 模拟打开搜索
        test_logger.info("正在打开微信搜索...")
        await asyncio.sleep(0.5)
        test_logger.info("微信搜索界面已打开")
        reporter.send_progress(2, 5)
        
        await asyncio.sleep(1)
        
        # 模拟处理公众号
        test_logger.info("正在处理第 1/2 个公众号")
        await asyncio.sleep(0.5)
        test_logger.info("已成功进入公众号主页")
        reporter.send_progress(3, 5)
        
        await asyncio.sleep(1)
        
        # 模拟 VLM 识别
        test_logger.info("使用 VLM 识别中...")
        await asyncio.sleep(1)
        test_logger.info("识别到 3 个当天日期位置")
        reporter.send_progress(4, 5)
        
        await asyncio.sleep(1)
        
        # 模拟文章采集
        test_logger.info("处理第 1/3 个文章位置")
        await asyncio.sleep(0.5)
        test_logger.info("文章链接已复制: https://mp.weixin.qq.com/s/test123abc")
        reporter.send_article(link="https://mp.weixin.qq.com/s/test123abc")
        
        await asyncio.sleep(1)
        
        test_logger.info("处理第 2/3 个文章位置")
        await asyncio.sleep(0.5)
        test_logger.info("文章链接已复制: https://mp.weixin.qq.com/s/test456def")
        reporter.send_article(link="https://mp.weixin.qq.com/s/test456def")
        
        await asyncio.sleep(1)
        
        # 模拟完成
        test_logger.info("文章链接采集完成")
        test_logger.info("所有公众号采集任务完成")
        reporter.send_progress(5, 5)
        
        await asyncio.sleep(1)
        
        # 发送完成信号
        reporter.send_workflow_end(
            success=True,
            stats={
                'total_accounts': 2,
                'success_accounts': 2,
                'total_articles': 2
            }
        )
        
        test_logger.info("工作流模拟完成")
        
    finally:
        remove_logging_forwarding(handler)


def start_server_thread(reporter):
    """在后台线程启动服务器"""
    def run_server():
        start_server(host="127.0.0.1", port=8765, reporter=reporter)
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(2)
    return thread


async def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("前端接口测试 - 模拟工作流")
    print("=" * 70)
    
    # 1. 创建 ProgressReporter
    print("\n[1] 创建 ProgressReporter...")
    reporter = ProgressReporter()  # 此时 server_loop 为 None
    print("  ✓ 完成")
    
    # 2. 启动服务器
    print("\n[2] 启动前端服务器...")
    start_server_thread(reporter)
    print("  ✓ 服务器已启动: http://localhost:8765")
    print("  💡 请在浏览器中打开上述地址")
    
    # 验证事件循环是否注入
    if reporter.server_loop is not None:
        print(f"  ✓ 事件循环已注入到 ProgressReporter")
    else:
        print(f"  ⚠️  事件循环尚未注入（服务器可能还在启动）")
    
    # 3. 等待用户准备
    print("\n[3] 等待 5 秒，给你时间打开浏览器...")
    await asyncio.sleep(5)
    
    # 4. 运行模拟工作流
    print("\n[4] 开始模拟工作流...")
    await simulate_workflow(reporter)
    
    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)
    print("\n前端页面应该已显示：")
    print("  - 实时日志（带颜色）")
    print("  - 操作状态更新")
    print("  - 进度条更新")
    print("  - 采集的文章链接（2篇）")
    print("  - 工作流完成统计")
    
    print("\n按 Ctrl+C 退出...\n")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n退出")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已中断")
