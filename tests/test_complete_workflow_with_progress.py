"""
完整工作流端到端测试（带实时进度显示）

这个测试会执行完整的 build_workflow() 方法，在真实环境中测试整个自动化流程，
并使用 rich 库实时显示进度和状态。

测试内容：
1. 打开/激活微信应用
2. 从配置文件读取并构建公众号 URL 列表
3. 遍历每个公众号，自动采集当天文章
4. 将采集结果保存到文件
5. 输出采集统计报告

运行此测试前请确保：
1. 系统已安装微信客户端并能正常登录
2. configs/config.yaml 文件存在且包含有效的文章 URL
3. 所有模板图片存在于 templates/ 目录
4. 设置了环境变量 DASHSCOPE_API_KEY（用于 VLM 识别）
5. 微信窗口可以被正常操作（不要锁定屏幕）
"""

import sys
import time
import logging
import asyncio
import os
from pathlib import Path
from datetime import datetime

# Rich 库用于美化输出
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich import box
from rich.text import Text

from wechat_ai_daily.workflows.wechat_autogui import OfficialAccountArticleCollector
from wechat_ai_daily.utils.wechat import is_wechat_running

# 创建 Rich Console
console = Console()

# 配置日志输出到文件
log_file = "logs/test_workflow.log"
Path(log_file).parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)


class ProgressTracker:
    """进度跟踪器，用于实时显示工作流执行状态"""
    
    def __init__(self):
        self.current_step = ""
        self.current_account = 0
        self.total_accounts = 0
        self.current_article = 0
        self.articles_collected = 0
        self.start_time = None
        self.accounts_status = []
        
    def generate_layout(self) -> Table:
        """生成实时状态表格"""
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("项目", style="cyan", width=20)
        table.add_column("状态", style="yellow")
        
        # 执行时间
        if self.start_time:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            table.add_row("⏱️  执行时间", f"{minutes} 分 {seconds} 秒")
        
        # 当前步骤
        table.add_row("📍 当前步骤", self.current_step)
        
        # 公众号进度
        if self.total_accounts > 0:
            progress_text = f"{self.current_account}/{self.total_accounts}"
            table.add_row("📱 公众号进度", progress_text)
        
        # 已采集文章数
        table.add_row("📝 已采集文章", str(self.articles_collected))
        
        return table
    
    def generate_accounts_table(self) -> Table:
        """生成公众号状态表格"""
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold green")
        table.add_column("序号", justify="center", width=6)
        table.add_column("公众号", width=40)
        table.add_column("状态", justify="center", width=15)
        table.add_column("文章数", justify="center", width=10)
        
        for status in self.accounts_status:
            icon = "⏳" if status['status'] == 'pending' else \
                   "▶️" if status['status'] == 'running' else \
                   "✅" if status['status'] == 'success' else "❌"
            
            table.add_row(
                str(status['index']),
                status['url'][:35] + "..." if len(status['url']) > 35 else status['url'],
                f"{icon} {status['status_text']}",
                str(status['articles'])
            )
        
        return table


def check_prerequisites():
    """检查测试前置条件"""
    console.print("\n[bold cyan]检查测试前置条件[/bold cyan]", justify="center")
    console.print("=" * 70 + "\n")
    
    errors = []
    
    # 1. 检查配置文件
    console.print("[cyan]检查配置文件...[/cyan]")
    config_path = "configs/config.yaml"
    if not os.path.exists(config_path):
        errors.append(f"配置文件不存在: {config_path}")
        console.print(f"  [red]✗[/red] 配置文件不存在: {config_path}")
    else:
        console.print(f"  [green]✓[/green] 配置文件存在")
    
    # 2. 检查模板图片
    console.print("\n[cyan]检查模板图片...[/cyan]")
    templates = [
        "templates/search_website_win.png",
        "templates/search_website.png",
        "templates/three_dots.png",
        "templates/turnback.png"
    ]
    
    for template in templates:
        if not os.path.exists(template):
            errors.append(f"模板图片不存在: {template}")
            console.print(f"  [red]✗[/red] {template}")
        else:
            console.print(f"  [green]✓[/green] {template}")
    
    # 3. 检查环境变量
    console.print("\n[cyan]检查环境变量...[/cyan]")
    if not os.getenv("DASHSCOPE_API_KEY"):
        errors.append("环境变量 DASHSCOPE_API_KEY 未设置")
        console.print("  [red]✗[/red] DASHSCOPE_API_KEY 未设置")
    else:
        console.print("  [green]✓[/green] DASHSCOPE_API_KEY 已设置")
    
    # 4. 检查微信
    console.print("\n[cyan]检查微信应用...[/cyan]")
    os_name = sys.platform
    try:
        is_running = is_wechat_running(os_name)
        status_text = "运行中" if is_running else "未运行"
        console.print(f"  [green]✓[/green] 微信状态: {status_text}")
    except Exception as e:
        errors.append(f"微信检查失败: {e}")
        console.print(f"  [red]✗[/red] 微信检查失败")
    
    # 5. 检查输出目录
    console.print("\n[cyan]检查输出目录...[/cyan]")
    try:
        Path("output").mkdir(parents=True, exist_ok=True)
        console.print("  [green]✓[/green] 输出目录准备就绪")
    except Exception as e:
        errors.append(f"无法创建输出目录: {e}")
        console.print(f"  [red]✗[/red] 无法创建输出目录")
    
    console.print("\n" + "=" * 70)
    
    if errors:
        console.print("[bold red]❌ 前置条件检查失败[/bold red]\n")
        for error in errors:
            console.print(f"  • {error}")
        return False
    else:
        console.print("[bold green]✅ 前置条件检查通过[/bold green]")
        return True


async def test_workflow_with_progress():
    """带进度显示的工作流测试"""
    
    tracker = ProgressTracker()
    tracker.start_time = time.time()
    tracker.current_step = "正在初始化..."
    
    test_result = {
        'success': False,
        'error': None,
        'results': None,
        'duration': 0
    }
    
    try:
        # 创建收集器实例
        console.print("\n[bold cyan]初始化收集器[/bold cyan]")
        collector = OfficialAccountArticleCollector()
        
        console.print(f"  • 配置文件: {collector.config}")
        console.print(f"  • 操作系统: {collector.os_name}")
        console.print(f"  • 最大滚动次数: {collector.MAX_SCROLL_TIMES}")
        
        # 获取公众号列表以初始化进度跟踪
        console.print("\n[bold cyan]读取公众号列表...[/bold cyan]")
        urls = collector._build_official_account_url()
        tracker.total_accounts = len(urls)
        
        # 初始化公众号状态列表
        for i, url in enumerate(urls, 1):
            tracker.accounts_status.append({
                'index': i,
                'url': url,
                'status': 'pending',
                'status_text': '等待中',
                'articles': 0
            })
        
        console.print(f"  • 找到 {len(urls)} 个公众号\n")
        
        # 倒计时
        console.print("[bold yellow]⚠️  测试即将开始，请不要操作鼠标和键盘[/bold yellow]\n")
        for i in range(5, 0, -1):
            console.print(f"[yellow]倒计时: {i} 秒...[/yellow]", end="\r")
            time.sleep(1)
        console.print(" " * 50, end="\r")  # 清除倒计时
        
        # 创建实时显示的布局
        with Live(console=console, refresh_per_second=2) as live:
            # 包装原始的 build_workflow 方法以添加进度更新
            original_workflow = collector.build_workflow
            
            async def wrapped_workflow():
                """包装的工作流，添加进度更新"""
                tracker.current_step = "正在打开微信..."
                live.update(Panel(tracker.generate_layout(), title="[bold]执行进度[/bold]", border_style="green"))
                
                # 调用原始工作流
                # 由于我们无法直接hook到内部步骤，我们通过定时更新来模拟进度
                async def update_progress():
                    """后台更新进度显示"""
                    while True:
                        layout = Layout()
                        layout.split_column(
                            Layout(tracker.generate_layout(), size=8),
                            Layout(tracker.generate_accounts_table())
                        )
                        live.update(Panel(layout, title="[bold]执行进度[/bold]", border_style="green"))
                        await asyncio.sleep(1)
                
                # 启动进度更新任务
                progress_task = asyncio.create_task(update_progress())
                
                try:
                    results = await original_workflow()
                    
                    # 更新最终状态
                    for i, result in enumerate(results):
                        tracker.accounts_status[i]['status'] = 'success' if 'error' not in result else 'failed'
                        tracker.accounts_status[i]['status_text'] = '成功' if 'error' not in result else '失败'
                        tracker.accounts_status[i]['articles'] = result.get('count', 0)
                    
                    tracker.current_step = "✅ 执行完成"
                    tracker.articles_collected = sum(r.get('count', 0) for r in results)
                    
                    return results
                finally:
                    progress_task.cancel()
                    try:
                        await progress_task
                    except asyncio.CancelledError:
                        pass
            
            # 执行包装后的工作流
            results = await wrapped_workflow()
            
            # 显示最终状态
            layout = Layout()
            layout.split_column(
                Layout(tracker.generate_layout(), size=8),
                Layout(tracker.generate_accounts_table())
            )
            live.update(Panel(layout, title="[bold green]执行完成[/bold green]", border_style="green"))
        
        # 记录结果
        end_time = time.time()
        test_result['success'] = True
        test_result['results'] = results
        test_result['duration'] = end_time - tracker.start_time
        
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]⚠️  用户中断了测试[/bold yellow]")
        test_result['error'] = "用户中断"
    except Exception as e:
        console.print(f"\n\n[bold red]❌ 测试失败: {e}[/bold red]")
        logging.exception("详细错误信息:")
        test_result['error'] = str(e)
    
    return test_result


def print_final_report(test_result):
    """打印最终测试报告"""
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]测试报告[/bold cyan]", justify="center")
    console.print("=" * 70 + "\n")
    
    if not test_result['success']:
        console.print(Panel(
            f"[bold red]测试失败[/bold red]\n\n错误: {test_result.get('error', '未知错误')}",
            title="结果",
            border_style="red"
        ))
        return
    
    results = test_result['results']
    duration = test_result['duration']
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    
    # 统计数据
    total_accounts = len(results)
    success_count = sum(1 for r in results if 'error' not in r)
    fail_count = total_accounts - success_count
    total_articles = sum(r.get('count', 0) for r in results)
    
    # 创建统计表格
    stats_table = Table(box=box.ROUNDED, show_header=False)
    stats_table.add_column("指标", style="cyan bold", width=20)
    stats_table.add_column("数值", style="yellow bold", width=15)
    
    stats_table.add_row("⏱️  执行时间", f"{minutes} 分 {seconds} 秒")
    stats_table.add_row("📱 公众号总数", str(total_accounts))
    stats_table.add_row("✅ 成功采集", str(success_count))
    stats_table.add_row("❌ 失败数量", str(fail_count))
    stats_table.add_row("📝 文章总数", str(total_articles))
    
    console.print(Panel(stats_table, title="[bold]统计数据[/bold]", border_style="green"))
    
    # 详细结果表格
    console.print("\n[bold cyan]详细结果:[/bold cyan]\n")
    
    results_table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    results_table.add_column("序号", justify="center", width=6)
    results_table.add_column("公众号URL", width=50)
    results_table.add_column("状态", justify="center", width=10)
    results_table.add_column("文章数", justify="center", width=10)
    
    for i, result in enumerate(results, 1):
        url = result['account_url']
        if 'error' in result:
            results_table.add_row(
                str(i),
                url[:45] + "..." if len(url) > 45 else url,
                "[red]失败[/red]",
                "0"
            )
        else:
            results_table.add_row(
                str(i),
                url[:45] + "..." if len(url) > 45 else url,
                "[green]成功[/green]",
                str(result['count'])
            )
    
    console.print(results_table)
    
    # 输出文件列表
    if total_articles > 0:
        console.print("\n[bold cyan]📁 输出文件:[/bold cyan]\n")
        for result in results:
            if 'output_file' in result:
                console.print(f"  • {result['output_file']}")
    
    console.print(f"\n[dim]📝 详细日志: {log_file}[/dim]")
    
    # 最终状态
    console.print("\n" + "=" * 70)
    if success_count == total_accounts:
        console.print(Panel(
            "[bold green]🎉 测试完全成功！所有公众号文章采集完成[/bold green]",
            border_style="green"
        ))
    elif success_count > 0:
        console.print(Panel(
            "[bold yellow]⚠️  测试部分成功，部分公众号采集失败[/bold yellow]",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            "[bold red]❌ 测试失败，所有公众号采集均失败[/bold red]",
            border_style="red"
        ))


def main():
    """主测试函数"""
    
    # 显示欢迎界面
    console.print(Panel.fit(
        "[bold cyan]完整工作流端到端测试[/bold cyan]\n"
        "[dim]带实时进度显示[/dim]",
        border_style="cyan"
    ))
    
    # 检查前置条件
    if not check_prerequisites():
        console.print("\n[bold red]请解决上述问题后重新运行[/bold red]")
        return
    
    # 用户确认
    console.print("\n" + "=" * 70)
    console.print(Panel(
        "[bold yellow]⚠️  重要提示[/bold yellow]\n\n"
        "此测试将在真实环境中运行，会：\n"
        "  1. 自动打开/操作你的微信应用\n"
        "  2. 自动搜索并进入公众号页面\n"
        "  3. 自动识别和采集文章内容\n"
        "  4. 使用 VLM API（消耗 API 额度）\n\n"
        "[bold]测试过程中请不要操作鼠标和键盘[/bold]\n\n"
        "按 Ctrl+C 可随时取消",
        border_style="yellow"
    ))
    
    console.print("\n[yellow]测试将在 10 秒后开始...[/yellow]\n")
    
    try:
        for i in range(10, 0, -1):
            console.print(f"[yellow]倒计时: {i} 秒...[/yellow]", end="\r")
            time.sleep(1)
        console.print(" " * 50, end="\r")
        
        # 运行测试
        test_result = asyncio.run(test_workflow_with_progress())
        
        # 输出报告
        print_final_report(test_result)
        
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]⚠️  测试被用户取消[/bold yellow]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]⚠️  测试被用户中断[/bold yellow]")
    except Exception as e:
        console.print(f"\n\n[bold red]❌ 测试执行失败: {e}[/bold red]")
        logging.exception("详细错误信息:")
