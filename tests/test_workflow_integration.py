"""
完整工作流集成测试

测试从打开微信到生成公众号URL到打开微信搜索的完整流程。
这是一个真实的集成测试，会实际与系统交互。

运行此测试前请确保：
1. 系统已安装微信客户端
2. configs/config.yaml 文件存在且包含有效的文章 URL
3. templates/search_web_result.png 模板图片存在
4. 允许测试脚本操作微信应用
"""

import sys
import time
import logging
import tkinter as tk
from tkinter import messagebox

from wechat_ai_daily.workflows.wechat_autogui import OfficialAccountArticleCollector
from wechat_ai_daily.utils.wechat import is_wechat_running

# 配置日志输出，方便查看测试过程
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def test_full_workflow():
    """
    完整工作流测试：从打开微信到打开搜索界面的全流程

    测试步骤：
    1. 创建收集器实例
    2. 打开/激活微信应用
    3. 生成公众号 URL 列表
    4. 打开微信搜索界面
    5. 验证每一步的执行结果
    """
    print("\n" + "=" * 70)
    print("完整工作流集成测试")
    print("=" * 70)

    results = []

    # ==================== 步骤1: 创建收集器实例 ====================
    print("\n[步骤1] 创建 OfficialAccountArticleCollector 实例...")
    try:
        collector = OfficialAccountArticleCollector()
        print("✓ 实例创建成功")
        print(f"  配置文件路径: {collector.config}")
        print(f"  操作系统: {collector.os_name}")
        results.append(("创建收集器实例", True))
    except Exception as e:
        print(f"✗ 实例创建失败: {e}")
        results.append(("创建收集器实例", False))
        return results

    # ==================== 步骤2: 打开/激活微信 ====================
    print("\n[步骤2] 打开/激活微信应用...")
    print("  ⚠️  此步骤会实际打开或激活你的微信应用")

    # 记录打开前的状态
    wechat_running_before = is_wechat_running(collector.os_name)
    print(f"  微信打开前状态: {'运行中' if wechat_running_before else '未运行'}")

    try:
        collector._open_wechat()
        print("✓ _open_wechat() 执行完成")

        # 验证微信是否在运行（_open_wechat内部已有延迟，无需额外等待）
        wechat_running_after = is_wechat_running(collector.os_name)
        print(f"  微信打开后状态: {'运行中' if wechat_running_after else '未运行'}")

        if wechat_running_after:
            print("✓ 微信已成功打开/激活")
            results.append(("打开微信", True))
        else:
            print("✗ 微信未能成功打开")
            results.append(("打开微信", False))
            return results

    except Exception as e:
        print(f"✗ 打开微信失败: {e}")
        results.append(("打开微信", False))
        return results

    # ==================== 步骤3: 生成公众号 URL ====================
    print("\n[步骤3] 生成公众号 URL 列表...")
    print("  ⚠️  此步骤会发送网络请求到微信服务器")

    try:
        official_account_urls = collector._build_official_account_url()
        print("✓ _build_official_account_url() 执行完成")
        print(f"  生成的公众号 URL 数量: {len(official_account_urls)}")

        # 显示生成的 URL
        for i, url in enumerate(official_account_urls, 1):
            print(f"  URL {i}: {url}")

        if len(official_account_urls) > 0:
            print("✓ 成功生成公众号 URL")
            results.append(("生成公众号URL", True))
        else:
            print("✗ 未能生成任何公众号 URL")
            results.append(("生成公众号URL", False))
            return results

    except Exception as e:
        print(f"✗ 生成公众号 URL 失败: {e}")
        logging.exception("详细错误信息:")
        results.append(("生成公众号URL", False))
        return results

    # ==================== 步骤4: 打开微信搜索 ====================
    print("\n[步骤4] 打开微信搜索界面...")
    print("  ⚠️  此步骤会使用键盘快捷键操作微信")

    try:
        collector._open_wechat_search()
        print("✓ _open_wechat_search() 执行完成")
        print("✓ 微信搜索界面已打开")
        results.append(("打开微信搜索", True))

    except Exception as e:
        print(f"✗ 打开微信搜索失败: {e}")
        logging.exception("详细错误信息:")
        results.append(("打开微信搜索", False))
        return results

    # ==================== 步骤5: 搜索公众号URL ====================
    print("\n[步骤5] 搜索公众号URL并打开主页...")
    print("  ⚠️  此步骤会使用键盘快捷键和图像识别操作微信")
    print(f"  将搜索第一个公众号: {official_account_urls[0]}")

    try:
        collector._search_official_account_url(official_account_urls[0])
        print("✓ _search_official_account_url() 执行完成")
        print("✓ 公众号主页已打开")
        results.append(("搜索公众号URL", True))

    except Exception as e:
        print(f"✗ 搜索公众号URL失败: {e}")
        logging.exception("详细错误信息:")
        results.append(("搜索公众号URL", False))
        return results

    return results


def show_completion_dialog(passed: int, total: int):
    """
    显示测试完成提示弹窗

    Args:
        passed: 通过的测试数量
        total: 总测试数量
    """
    try:
        # 创建 tkinter 根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口

        # 根据测试结果显示不同的提示
        if passed == total:
            messagebox.showinfo(
                "测试完成",
                f"✅ 所有测试通过！\n\n"
                f"通过率: {passed}/{total} (100%)\n\n"
                f"完整工作流运行正常"
            )
        else:
            messagebox.showwarning(
                "测试完成",
                f"⚠️ 部分测试失败\n\n"
                f"通过率: {passed}/{total} ({passed/total*100:.0f}%)\n\n"
                f"请检查控制台日志"
            )

        # 销毁根窗口
        root.destroy()
    except Exception as e:
        # 如果弹窗失败，至少在控制台输出提示
        logging.warning(f"无法显示弹窗提示: {e}")
        print("\n⚠️ 弹窗提示失败，但测试已完成")


def main():
    """
    主测试函数
    """
    print("\n" + "=" * 70)
    print("开始完整工作流集成测试")
    print("=" * 70)
    print("\n⚠️  警告：此测试会实际操作你的微信应用")
    print("测试内容包括：")
    print("  1. 打开/激活微信")
    print("  2. 发送网络请求获取公众号信息")
    print("  3. 使用键盘快捷键和图像识别操作微信")
    print("\n如果不希望运行测试，请按 Ctrl+C 取消\n")

    # 给用户 5 秒时间取消测试
    for i in range(5, 0, -1):
        print(f"测试将在 {i} 秒后开始...", end="\r")
        time.sleep(1)
    print("\n")

    # 运行测试
    results = test_full_workflow()

    # ==================== 输出测试报告 ====================
    print("\n" + "=" * 70)
    print("测试报告")
    print("=" * 70)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    # 统计通过率
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！完整工作流运行正常")
        print("\n✅ 你现在可以看到微信搜索界面已经打开")
        print("   下一步可以继续实现在搜索框中输入公众号 URL 的功能")
    else:
        print("\n⚠️  部分测试失败，请检查日志输出")
        print("\n常见问题排查：")
        print("  1. 微信是否已正确安装？")
        print("  2. configs/config.yaml 是否包含有效的文章 URL？")
        print("  3. templates/search_web_result.png 模板图片是否存在？")
        print("  4. 微信窗口是否在前台且可见？")
        print("  5. 屏幕分辨率是否与模板图片匹配？")

    # 显示完成提示弹窗
    show_completion_dialog(passed, total)


if __name__ == "__main__":
    main()
