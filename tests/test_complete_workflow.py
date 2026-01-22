"""
完整工作流端到端测试

这个测试会执行完整的 build_workflow() 方法，在真实环境中测试整个自动化流程。

测试内容：
1. 打开/激活微信应用
2. 从配置文件读取并构建公众号 URL 列表
3. 遍历每个公众号，自动采集当天文章
4. 将采集结果保存到文件
5. 输出采集统计报告

运行此测试前请确保：
1. 系统已安装微信客户端并能正常登录
2. configs/config.yaml 文件存在且包含有效的文章 URL
3. 所有模板图片存在于 templates/ 目录：
   - search_website_win.png / search_website.png
   - three_dots.png
   - turnback.png
4. 设置了环境变量 DASHSCOPE_API_KEY（用于 VLM 识别）
5. 微信窗口可以被正常操作（不要锁定屏幕）

⚠️ 警告：
- 这是一个真实环境测试，会实际操作你的微信应用
- 测试过程中请不要手动操作鼠标和键盘
- 测试可能需要几分钟到十几分钟（取决于文章数量）
- 建议在测试时不要使用电脑进行其他工作
"""

import sys
import time
import logging
import asyncio
import os
from pathlib import Path

from wechat_ai_daily.workflows.wechat_autogui import OfficialAccountArticleCollector
from wechat_ai_daily.utils.wechat import is_wechat_running

# 配置日志输出，输出到控制台和文件
log_file = "logs/test_workflow.log"
Path(log_file).parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler(log_file, encoding='utf-8')  # 输出到文件
    ]
)


def check_prerequisites():
    """
    检查测试前置条件是否满足

    Returns:
        tuple: (bool: 是否通过检查, list: 错误信息列表)
    """
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
        print("     请设置后再运行测试")
    else:
        print("  ✓ 环境变量 DASHSCOPE_API_KEY 已设置")

    # 4. 检查微信是否可以连接
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


async def test_complete_workflow():
    """
    测试完整的工作流

    Returns:
        dict: 测试结果
    """
    print("\n" + "=" * 70)
    print("开始完整工作流测试")
    print("=" * 70)

    test_result = {
        'success': False,
        'error': None,
        'results': None,
        'duration': 0
    }

    try:
        # 创建收集器实例
        print("\n[初始化] 创建 OfficialAccountArticleCollector 实例...")
        collector = OfficialAccountArticleCollector()
        print(f"  ✓ 实例创建成功")
        print(f"  - 配置文件: {collector.config}")
        print(f"  - 操作系统: {collector.os_name}")
        print(f"  - 最大滚动次数: {collector.MAX_SCROLL_TIMES}")

        # 记录开始时间
        start_time = time.time()

        # 运行完整工作流
        print("\n" + "=" * 70)
        print("开始执行 build_workflow()")
        print("=" * 70)
        print("\n⚠️  测试过程中请不要操作鼠标和键盘")
        print("⚠️  请让微信窗口保持可见状态\n")

        # 等待5秒让用户准备
        for i in range(5, 0, -1):
            print(f"测试将在 {i} 秒后开始...", end="\r")
            time.sleep(1)
        print("\n")

        # 执行工作流
        output_path, results = await collector.build_workflow()

        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time

        # 保存结果
        test_result['success'] = True
        test_result['output_path'] = output_path
        test_result['results'] = results
        test_result['duration'] = duration

        print("\n" + "=" * 70)
        print("工作流执行完成")
        print("=" * 70)
        print(f"\n输出文件: {output_path}")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断了测试")
        test_result['error'] = "用户中断"

    except Exception as e:
        print(f"\n\n❌ 工作流执行失败: {e}")
        logging.exception("详细错误信息:")
        test_result['error'] = str(e)

    return test_result


def print_test_report(test_result):
    """
    打印测试报告

    Args:
        test_result: 测试结果字典
    """
    print("\n" + "=" * 70)
    print("测试报告")
    print("=" * 70)

    if not test_result['success']:
        print("\n❌ 测试失败")
        if test_result['error']:
            print(f"\n错误信息: {test_result['error']}")
        print("\n请检查日志文件: logs/test_workflow.log")
        return

    print("\n✅ 测试成功完成")

    # 显示执行时间
    duration = test_result['duration']
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    print(f"\n⏱️  执行时间: {minutes} 分 {seconds} 秒")

    # 显示输出文件
    if 'output_path' in test_result:
        print(f"\n📁 输出文件: {test_result['output_path']}")

    # 显示采集结果
    results = test_result['results']

    print("\n" + "=" * 70)
    print("采集结果汇总")
    print("=" * 70)

    # 统计
    total_accounts = len(results)
    success_accounts = sum(1 for r in results if 'error' not in r)
    fail_accounts = total_accounts - success_accounts
    total_articles = sum(r['count'] for r in results)

    print(f"\n📊 总体统计:")
    print(f"  - 公众号总数: {total_accounts}")
    print(f"  - 成功采集: {success_accounts}")
    print(f"  - 失败数量: {fail_accounts}")
    print(f"  - 文章总数: {total_articles}")

    print(f"\n📋 详细结果:")
    for i, result in enumerate(results, 1):
        print(f"\n  公众号 {i}:")
        print(f"    URL: {result['account_url'][:80]}...")

        if 'error' in result:
            print(f"    状态: ❌ 失败")
            print(f"    错误: {result['error']}")
        else:
            print(f"    状态: ✅ 成功")
            print(f"    文章数: {result['count']} 篇")
            print(f"    输出文件: {result['output_file']}")

    print("\n" + "=" * 70)

    # 显示输出文件位置
    if total_articles > 0:
        print("\n📁 采集的文章已保存到以下文件:")
        for result in results:
            if 'output_file' in result:
                print(f"  - {result['output_file']}")

    print("\n📝 详细日志已保存到: logs/test_workflow.log")

    # 最终提示
    print("\n" + "=" * 70)
    if success_accounts == total_accounts:
        print("🎉 测试完全成功！所有公众号文章采集完成")
    elif success_accounts > 0:
        print("⚠️  测试部分成功，部分公众号采集失败")
    else:
        print("❌ 测试失败，所有公众号采集均失败")
    print("=" * 70)


def main():
    """
    主测试函数
    """
    print("\n" + "=" * 70)
    print("完整工作流端到端测试")
    print("=" * 70)

    # 步骤1: 检查前置条件
    passed, errors = check_prerequisites()
    if not passed:
        print("\n❌ 前置条件检查未通过，无法运行测试")
        print("请解决上述问题后重新运行")
        return

    # 步骤2: 用户确认
    print("\n" + "=" * 70)
    print("⚠️  重要提示")
    print("=" * 70)
    print("\n此测试将在真实环境中运行，会：")
    print("  1. 自动打开/操作你的微信应用")
    print("  2. 自动搜索并进入公众号页面")
    print("  3. 自动识别和采集文章内容")
    print("  4. 使用 VLM API（消耗 API 额度）")
    print("\n测试过程可能需要几分钟到十几分钟")
    print("测试期间请不要操作鼠标和键盘")
    print("\n如果不希望运行测试，请按 Ctrl+C 取消\n")

    # 给用户 10 秒时间考虑
    for i in range(10, 0, -1):
        print(f"测试将在 {i} 秒后开始...", end="\r")
        time.sleep(1)
    print("\n")

    # 步骤3: 运行测试
    try:
        test_result = asyncio.run(test_complete_workflow())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户取消了测试")
        return

    # 步骤4: 输出测试报告
    print_test_report(test_result)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试执行失败: {e}")
        logging.exception("详细错误信息:")
