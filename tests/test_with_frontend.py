"""
带前端监控的完整工作流测试

这个测试脚本集成了前端监控功能，会：
1. 启动前端监控服务器（在后台线程中）
2. 打开浏览器显示监控界面
3. 运行完整的 RPA 工作流，实时推送进度到前端
4. 测试完成后保持服务器运行，方便查看结果

使用方法：
    python tests/test_with_frontend.py

前端监控地址：
    http://localhost:8765

⚠️ 重要提示：
- 建议将浏览器窗口放到副屏查看
- 不要点击或切换浏览器窗口焦点（避免影响微信操作）
- 自动化运行期间请勿操作鼠标/键盘
"""

import sys
import time
import logging
import asyncio
import os
import threading
import webbrowser
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from wechat_ai_daily.workflows.wechat_autogui import OfficialAccountArticleCollector
from wechat_ai_daily.utils.wechat import is_wechat_running
from frontend.progress_reporter import ProgressReporter
from frontend.server import start_server
from frontend.logging_handler import (
    setup_logging_forwarding, 
    remove_logging_forwarding,
    get_latest_articles_file,
    parse_articles_from_markdown
)

# 配置日志
log_file = "logs/test_with_frontend.log"
Path(log_file).parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)


# ==================== 前置条件检查（复用原有逻辑）====================

def check_prerequisites():
    """检查测试前置条件"""
    errors = []
    
    print("\n" + "=" * 70)
    print("检查测试前置条件")
    print("=" * 70)
    
    # 1. 检查配置文件
    print("\n[检查1] 配置文件...")
    config_path = "configs/config.yaml"
    if not os.path.exists(config_path):
        errors.append(f"配置文件不存在: {config_path}")
        print(f"  ✗ 配置文件不存在: {config_path}")
    else:
        print(f"  ✓ 配置文件存在: {config_path}")
    
    # 2. 检查模板图片
    print("\n[检查2] 模板图片...")
    templates = [
        "templates/search_website_win.png",
        "templates/search_website.png",
        "templates/three_dots.png",
        "templates/turnback.png"
    ]
    
    for template in templates:
        if not os.path.exists(template):
            errors.append(f"模板图片不存在: {template}")
            print(f"  ✗ 模板图片不存在: {template}")
        else:
            print(f"  ✓ 模板图片存在: {template}")
    
    # 3. 检查环境变量
    print("\n[检查3] 环境变量...")
    if not os.getenv("DASHSCOPE_API_KEY"):
        errors.append("环境变量 DASHSCOPE_API_KEY 未设置")
        print("  ✗ 环境变量 DASHSCOPE_API_KEY 未设置")
    else:
        print("  ✓ 环境变量 DASHSCOPE_API_KEY 已设置")
    
    # 4. 检查微信
    print("\n[检查4] 微信应用...")
    os_name = sys.platform
    try:
        is_running = is_wechat_running(os_name)
        print(f"  ✓ 微信状态检查成功（当前{'运行中' if is_running else '未运行'}）")
    except Exception as e:
        errors.append(f"微信状态检查失败: {e}")
        print(f"  ✗ 微信状态检查失败: {e}")
    
    # 5. 检查输出目录
    print("\n[检查5] 输出目录...")
    output_dir = "output"
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ 输出目录准备就绪: {output_dir}")
    except Exception as e:
        errors.append(f"无法创建输出目录: {e}")
        print(f"  ✗ 无法创建输出目录: {e}")
    
    # 总结
    print("\n" + "=" * 70)
    if errors:
        print("❌ 前置条件检查失败")
        print("\n错误列表：")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        return False, errors
    else:
        print("✅ 前置条件检查通过，可以开始测试")
        return True, []


# ==================== 主测试流程 ====================

async def monitor_articles_file(reporter: ProgressReporter, stop_event: threading.Event):
    """后台任务：定期监控 output 目录的 markdown 文件，同步文章列表到前端
    
    Args:
        reporter: 进度上报器
        stop_event: 停止事件
    """
    last_article_count = 0
    last_file_mtime = 0
    
    while not stop_event.is_set():
        try:
            # 获取最新的文章文件
            latest_file = get_latest_articles_file("output")
            
            if latest_file:
                # 检查文件是否有更新
                file_mtime = Path(latest_file).stat().st_mtime
                
                if file_mtime > last_file_mtime:
                    # 文件有更新，重新解析
                    articles = parse_articles_from_markdown(latest_file)
                    current_count = len(articles)
                    
                    if current_count > last_article_count:
                        # 有新文章，推送增量部分到前端
                        new_articles = articles[last_article_count:]
                        for article in new_articles:
                            reporter.send_article(
                                link=article['link'],
                                title=f"文章 {article['index']}"
                            )
                        
                        last_article_count = current_count
                    
                    last_file_mtime = file_mtime
            
            # 每 2 秒检查一次
            await asyncio.sleep(2)
            
        except Exception as e:
            logging.warning(f"监控文章文件时出错: {e}")
            await asyncio.sleep(2)


async def run_test_workflow(reporter: ProgressReporter):
    """运行测试工作流"""
    print("\n" + "=" * 70)
    print("等待前端用户点击开始按钮...")
    print("=" * 70)
    print("\n请在浏览器前端页面点击 [▶️ 开始测试] 按钮启动测试\n")
    
    # 等待前端启动信号（使用轮询方式检查 threading.Event）
    from frontend.server import get_start_event, get_stop_event
    
    # 使用轮询方式等待（threading.Event 不支持 async await）
    # 每次循环都获取最新的事件引用，防止事件被重置后仍然等待旧对象
    while True:
        start_event = get_start_event()
        stop_event = get_stop_event()
        
        if start_event.is_set():
            break
        if stop_event.is_set():
            print("\n⚠️  启动前被取消")
            return {
                'success': False,
                'error': '用户取消',
                'results': None,
                'duration': 0
            }
        
        await asyncio.sleep(0.5)
    
    print("\n" + "=" * 70)
    print("收到前端启动信号，开始执行工作流")
    print("=" * 70)
    
    # 获取当前的 stop_event（用于后续检查）
    stop_event = get_stop_event()
    
    test_result = {
        'success': False,
        'error': None,
        'results': None,
        'duration': 0
    }
    
    # 设置日志转发到前端
    logging_handler = None
    original_screenshot_func = None
    original_time_sleep = None
    monitor_task = None  # 后台监控任务
    
    try:
        # 1. 配置日志转发
        print("\n[配置] 设置日志转发到前端...")
        logging_handler = setup_logging_forwarding(reporter)
        print("  ✓ 日志转发已配置")
        
        # 2. 启动文章文件监控任务
        print("\n[配置] 启动文章文件监控...")
        monitor_task = asyncio.create_task(
            monitor_articles_file(reporter, stop_event)
        )
        print("  ✓ 文章文件监控已启动")
        
        # 3. 拦截截图函数，自动推送截图到前端
        print("\n[配置] 设置截图自动推送...")
        from wechat_ai_daily.utils import autogui
        original_screenshot_func = autogui.screenshot_current_window
        
        def monitored_screenshot(save_path):
            """包装后的截图函数，会自动推送到前端"""
            result = original_screenshot_func(save_path)
            # 推送截图到前端
            reporter.send_screenshot(save_path)
            return result
        
        autogui.screenshot_current_window = monitored_screenshot
        print("  ✓ 截图自动推送已配置")
        
        # 4. 拦截 time.sleep，使其可以响应停止信号
        print("\n[配置] 设置可中断的 sleep...")
        original_time_sleep = time.sleep
        
        def interruptible_sleep(seconds):
            """可中断的 sleep，每 0.1 秒检查一次停止信号"""
            end_time = time.time() + seconds
            while time.time() < end_time:
                if stop_event.is_set():
                    # 收到停止信号，立即退出
                    raise KeyboardInterrupt("用户在前端点击停止")
                # 睡眠 0.1 秒或剩余时间（取较小值）
                remaining = end_time - time.time()
                if remaining > 0:
                    original_time_sleep(min(0.1, remaining))
        
        time.sleep = interruptible_sleep
        print("  ✓ 可中断的 sleep 已配置")
        
        # 5. 创建收集器（使用原始的，不需要包装）
        print("\n[初始化] 创建收集器...")
        collector = OfficialAccountArticleCollector("configs/config.yaml")
        print("  ✓ 收集器创建成功")
        
        # 6. 发送工作流启动信号
        official_account_urls = collector._build_official_account_url()
        reporter.send_workflow_start(len(official_account_urls))
        
        print("\n⚠️  测试过程中请不要操作鼠标和键盘")
        print("⚠️  请让微信窗口保持可见状态\n")
        
        # 记录开始时间
        start_time = time.time()
        
        # 7. 执行工作流（支持中断检查）
        results = await run_workflow_with_stop_check(collector, stop_event)
        
        # 检查是否被中断
        if stop_event.is_set():
            raise KeyboardInterrupt("用户在前端点击停止")
        
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        test_result['success'] = True
        test_result['results'] = results
        test_result['duration'] = duration
        
        # 统计结果并发送完成信号
        total_articles = sum(r['count'] for r in results)
        success_count = sum(1 for r in results if 'error' not in r)
        
        reporter.send_workflow_end(
            success=True,
            stats={
                'total_accounts': len(results),
                'success_accounts': success_count,
                'total_articles': total_articles
            }
        )
        
        print("\n" + "=" * 70)
        print("工作流执行完成")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
        test_result['error'] = "用户中断"
        reporter.send_workflow_end(success=False, error="用户中断")
        
    except Exception as e:
        print(f"\n\n❌ 工作流执行失败: {e}")
        logging.exception("详细错误信息:")
        test_result['error'] = str(e)
        reporter.send_workflow_end(success=False, error=str(e))
    
    finally:
        # 清理：移除日志转发、恢复截图函数和 time.sleep、停止监控任务
        
        # 重置事件（为下一次测试做准备）
        from frontend.server import reset_events
        print("\n[清理] 重置控制事件...")
        reset_events()
        print("  ✓ 控制事件已重置")
        
        # 停止后台监控任务
        if monitor_task and not monitor_task.done():
            print("\n[清理] 停止文章文件监控...")
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
            print("  ✓ 文章文件监控已停止")
        
        if logging_handler:
            print("\n[清理] 移除日志转发...")
            remove_logging_forwarding(logging_handler)
            print("  ✓ 日志转发已移除")
        
        if original_screenshot_func:
            print("\n[清理] 恢复截图函数...")
            from wechat_ai_daily.utils import autogui
            autogui.screenshot_current_window = original_screenshot_func
            print("  ✓ 截图函数已恢复")
        
        if original_time_sleep:
            print("\n[清理] 恢复 time.sleep...")
            time.sleep = original_time_sleep
            print("  ✓ time.sleep 已恢复")
    
    return test_result


async def run_workflow_with_stop_check(collector, stop_event):
    """执行工作流，定期检查停止信号
    
    Args:
        collector: OfficialAccountArticleCollector 实例（原始的，非包装的）
        stop_event: 停止事件
        
    Returns:
        工作流结果
        
    Raises:
        KeyboardInterrupt: 如果检测到停止信号
    """
    # 直接运行工作流
    # 由于我们已经 monkey patch 了 time.sleep，它会自动检查 stop_event
    # 如果收到停止信号，interruptible_sleep 会抛出 KeyboardInterrupt
    return await collector.build_workflow()


def start_server_thread(reporter: ProgressReporter):
    """在后台线程启动服务器"""
    def run_server():
        start_server(host="127.0.0.1", port=8765, reporter=reporter)
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    # 等待服务器启动
    time.sleep(2)
    
    return thread


async def main_async():
    """主函数的异步版本（使用单一事件循环）"""
    print("\n" + "=" * 70)
    print("带前端监控的完整工作流测试")
    print("=" * 70)
    
    # 步骤1: 检查前置条件
    passed, errors = check_prerequisites()
    if not passed:
        print("\n❌ 前置条件检查未通过，无法运行测试")
        return
    
    # 步骤2: 创建 ProgressReporter
    print("\n[初始化] 创建进度上报器...")
    reporter = ProgressReporter()
    print("  ✓ 进度上报器创建成功")
    
    # 步骤3: 启动前端服务器
    print("\n[启动] 启动前端监控服务器...")
    server_thread = start_server_thread(reporter)
    frontend_url = "http://localhost:8765"
    print(f"  ✓ 前端监控服务器已启动: {frontend_url}")
    
    # 步骤4: 打开浏览器
    print("\n[打开] 打开浏览器显示监控界面...")
    try:
        webbrowser.open(frontend_url)
        print("  ✓ 浏览器已打开")
        print("\n⚠️  重要提示：")
        print("     - 建议将浏览器窗口移到副屏查看")
        print("     - 准备好后，在前端页面点击 [▶️ 开始测试] 按钮")
        print("     - 测试期间不要点击浏览器或操作鼠标/键盘")
        print("     - 测试完成后可以再次点击 [▶️ 开始测试] 重新测试\n")
    except Exception as e:
        print(f"  ⚠️  自动打开浏览器失败: {e}")
        print(f"     请手动打开: {frontend_url}")
        print(f"     准备好后，在前端页面点击 [▶️ 开始测试] 按钮\n")
    
    # 给用户时间准备
    print("\n等待用户在前端点击开始...")
    print("(如需退出程序，请按 Ctrl+C)\n")
    
    # 步骤5: 循环运行测试（支持多次测试）
    # 使用同一个事件循环，避免重复创建导致的冲突
    test_count = 0
    while True:
        test_count += 1
        print("\n" + "=" * 70)
        print(f"准备执行第 {test_count} 次测试")
        print("=" * 70)
        
        # 直接调用 async 函数，不使用 asyncio.run()
        test_result = await run_test_workflow(reporter)
        
        # 显示本次测试结果
        print("\n" + "=" * 70)
        print(f"第 {test_count} 次测试报告")
        print("=" * 70)
        
        if test_result['success']:
            print("\n✅ 测试成功完成")
            duration = test_result['duration']
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            print(f"⏱️  执行时间: {minutes} 分 {seconds} 秒")
            
            results = test_result['results']
            total_articles = sum(r['count'] for r in results)
            success_count = sum(1 for r in results if 'error' not in r)
            
            print(f"\n📊 统计：")
            print(f"  - 公众号总数: {len(results)}")
            print(f"  - 成功采集: {success_count}")
            print(f"  - 文章总数: {total_articles}")
        else:
            print("\n❌ 测试失败")
            if test_result['error']:
                print(f"错误信息: {test_result['error']}")
        
        # 提示用户可以再次测试
        print("\n" + "=" * 70)
        print("测试已完成，可以在前端再次点击 [▶️ 开始测试] 进行下一次测试")
        print("或按 Ctrl+C 退出程序")
        print("=" * 70)


def main():
    """主函数"""
    try:
        # 使用单一的事件循环运行整个程序
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户退出程序")
    except SystemExit:
        # 捕获 SystemExit，优雅退出
        print("\n\n退出程序")
    except Exception as e:
        # Windows 上 asyncio 有时会在退出时抛出异常
        # 如果是 AssertionError 且在退出过程中，忽略它
        import traceback
        error_msg = str(e)
        if "AssertionError" in error_msg or "_loop_writing" in traceback.format_exc():
            print("\n\n程序已退出")
        else:
            # 其他异常正常抛出
            raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试执行失败: {e}")
        logging.exception("详细错误信息:")
