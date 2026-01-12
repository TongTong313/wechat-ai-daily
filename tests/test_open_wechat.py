"""
测试 _open_wechat 函数的实际有效性

这是一个集成测试，会实际与系统交互，打开或激活微信应用。
运行此测试前请确保：
1. 你的系统已安装微信客户端
2. 你允许测试脚本打开微信应用
"""

import sys
import time
import logging

# 添加项目根目录到 Python 路径，以便导入项目模块
sys.path.insert(0, "d:\\code\\wechat-ai-daily")

from src.wechat_ai_daily.workflows.wechat_autogui import OfficialAccountArticleCollector
from src.wechat_ai_daily.utils.wechat import is_wechat_running

# 配置日志输出，方便查看测试过程
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def test_open_wechat_basic():
    """
    基础测试：验证 _open_wechat 函数能否成功执行

    测试步骤：
    1. 记录测试开始前微信的运行状态
    2. 调用 _open_wechat 函数
    3. 验证函数执行后微信是否在运行
    4. 输出测试结果
    """
    print("\n" + "=" * 70)
    print("测试开始：验证 _open_wechat 函数的实际有效性")
    print("=" * 70)

    # 步骤1: 检查测试前微信的运行状态
    print("\n[步骤1] 检查测试前微信的运行状态...")
    os_name = sys.platform
    print(f"当前操作系统: {os_name}")

    wechat_running_before = is_wechat_running(os_name)
    if wechat_running_before:
        print("✓ 微信当前正在运行")
    else:
        print("✗ 微信当前未运行")

    # 步骤2: 创建收集器实例并调用 _open_wechat
    print("\n[步骤2] 调用 _open_wechat 函数...")
    try:
        # 创建收集器实例，不指定路径，让它自动查找
        # Windows: 会自动尝试查找常见的安装路径
        # macOS: 使用系统默认方式启动
        collector = OfficialAccountArticleCollector()
        print(f"  {os_name} 系统，使用自动查找方式")

        collector._open_wechat()
        print("✓ _open_wechat 函数执行完成，未抛出异常")
    except Exception as e:
        print(f"✗ _open_wechat 函数执行失败: {e}")
        print("\n测试结果: 失败 ❌")
        return False

    # 步骤3: 等待一小段时间，确保微信完全启动
    print("\n[步骤3] 等待 2 秒，确保微信完全启动...")
    time.sleep(2)

    # 步骤4: 检查测试后微信的运行状态
    print("\n[步骤4] 检查测试后微信的运行状态...")
    wechat_running_after = is_wechat_running(os_name)

    if wechat_running_after:
        print("✓ 微信现在正在运行")
    else:
        print("✗ 微信现在未运行")

    # 步骤5: 输出测试结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    print(f"测试前微信状态: {'运行中' if wechat_running_before else '未运行'}")
    print(f"测试后微信状态: {'运行中' if wechat_running_after else '未运行'}")

    # 判断测试是否通过
    if wechat_running_after:
        print("\n✓ 测试通过：_open_wechat 函数成功打开/激活了微信 ✅")
        return True
    else:
        print("\n✗ 测试失败：执行后微信仍未运行 ❌")
        return False


def test_open_wechat_idempotent():
    """
    幂等性测试：验证多次调用 _open_wechat 是否安全

    测试目的：
    确保即使微信已经在运行，再次调用 _open_wechat 也不会出错
    """
    print("\n" + "=" * 70)
    print("幂等性测试：多次调用 _open_wechat")
    print("=" * 70)

    # 创建收集器实例，使用自动查找方式
    collector = OfficialAccountArticleCollector()

    try:
        # 第一次调用
        print("\n[第1次调用] 调用 _open_wechat...")
        collector._open_wechat()
        print("✓ 第1次调用成功")

        time.sleep(2)

        # 第二次调用（此时微信应该已经在运行）
        print("\n[第2次调用] 再次调用 _open_wechat...")
        collector._open_wechat()
        print("✓ 第2次调用成功")

        # 验证微信仍在运行
        if is_wechat_running(sys.platform):
            print("\n✓ 幂等性测试通过：多次调用不会出错，微信正常运行 ✅")
            return True
        else:
            print("\n✗ 幂等性测试失败：微信未在运行 ❌")
            return False

    except Exception as e:
        print(f"\n✗ 幂等性测试失败：{e} ❌")
        return False


def main():
    """
    主测试函数：运行所有测试用例
    """
    print("\n" + "=" * 70)
    print("开始测试 _open_wechat 函数")
    print("=" * 70)
    print("\n⚠️  注意：此测试会实际打开你的微信应用")
    print("如果不希望打开微信，请按 Ctrl+C 取消测试\n")

    # 给用户 3 秒时间取消测试
    for i in range(3, 0, -1):
        print(f"测试将在 {i} 秒后开始...", end="\r")
        time.sleep(1)
    print("\n")

    # 运行测试用例
    results = []

    # 测试1: 基础功能测试
    result1 = test_open_wechat_basic()
    results.append(("基础功能测试", result1))

    time.sleep(2)

    # 测试2: 幂等性测试
    result2 = test_open_wechat_idempotent()
    results.append(("幂等性测试", result2))

    # 输出最终测试报告
    print("\n" + "=" * 70)
    print("最终测试报告")
    print("=" * 70)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    # 统计通过率
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！_open_wechat 函数工作正常")
    else:
        print("\n⚠️  部分测试失败，请检查日志输出")


if __name__ == "__main__":
    main()
