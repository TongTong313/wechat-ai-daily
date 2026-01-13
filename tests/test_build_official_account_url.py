"""
测试 _build_official_account_url 方法的实际有效性

这是一个集成测试，会实际发送网络请求到微信服务器，提取 biz 参数并生成公众号 URL。
运行此测试前请确保：
1. 网络连接正常
2. configs/config.yaml 文件存在且包含有效的文章 URL
3. 微信服务器可访问
"""

import logging
import re

from wechat_ai_daily.workflows.wechat_autogui import OfficialAccountArticleCollector

# 配置日志输出，方便查看测试过程
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def test_build_official_account_url_basic():
    """
    基础测试：验证 _build_official_account_url 方法能否成功执行

    测试步骤：
    1. 创建收集器实例
    2. 调用 _build_official_account_url 方法
    3. 验证返回结果的格式和内容
    4. 输出测试结果
    """
    print("\n" + "=" * 70)
    print("测试开始：验证 _build_official_account_url 方法的实际有效性")
    print("=" * 70)

    # 步骤1: 创建收集器实例
    print("\n[步骤1] 创建 OfficialAccountArticleCollector 实例...")
    try:
        collector = OfficialAccountArticleCollector()
        print("✓ 实例创建成功")
        print(f"  配置文件路径: {collector.config}")
    except Exception as e:
        print(f"✗ 实例创建失败: {e}")
        print("\n测试结果: 失败 ❌")
        return False

    # 步骤2: 调用 _build_official_account_url 方法
    print("\n[步骤2] 调用 _build_official_account_url 方法...")
    print("  ⚠️  此步骤会发送网络请求到微信服务器，可能需要几秒钟...")

    try:
        official_account_urls = collector._build_official_account_url()
        print("✓ 方法执行完成，未抛出异常")
    except Exception as e:
        print(f"✗ 方法执行失败: {e}")
        print("\n测试结果: 失败 ❌")
        return False

    # 步骤3: 验证返回结果
    print("\n[步骤3] 验证返回结果...")

    # 检查返回类型
    if not isinstance(official_account_urls, list):
        print(f"✗ 返回类型错误: 期望 list，实际 {type(official_account_urls)}")
        print("\n测试结果: 失败 ❌")
        return False

    print(f"✓ 返回类型正确: list")
    print(f"  返回的公众号 URL 数量: {len(official_account_urls)}")

    # 检查是否为空
    if len(official_account_urls) == 0:
        print("✗ 返回的 URL 列表为空")
        print("\n测试结果: 失败 ❌")
        return False

    print(f"✓ 成功生成 {len(official_account_urls)} 个公众号 URL")

    return official_account_urls


def test_url_format_validation(official_account_urls):
    """
    URL 格式验证测试：验证生成的公众号 URL 格式是否正确

    Args:
        official_account_urls: 公众号 URL 列表
    """
    print("\n[步骤4] 验证 URL 格式...")

    # 预期的 URL 格式
    expected_pattern = r'^https://mp\.weixin\.qq\.com/mp/profile_ext\?action=home&__biz=.+&scene=124$'

    all_valid = True
    for i, url in enumerate(official_account_urls, 1):
        print(f"\n  URL {i}: {url}")

        # 检查 URL 格式
        if re.match(expected_pattern, url):
            print(f"    ✓ 格式正确")
        else:
            print(f"    ✗ 格式错误")
            all_valid = False

        # 提取并显示 biz 参数
        biz_match = re.search(r'__biz=([^&]+)', url)
        if biz_match:
            biz = biz_match.group(1)
            print(f"    biz 参数: {biz}")
        else:
            print(f"    ✗ 无法提取 biz 参数")
            all_valid = False

    if all_valid:
        print(f"\n✓ 所有 URL 格式验证通过")
        return True
    else:
        print(f"\n✗ 部分 URL 格式验证失败")
        return False


def test_deduplication(official_account_urls):
    """
    去重测试：验证是否正确去除了重复的 biz

    Args:
        official_account_urls: 公众号 URL 列表
    """
    print("\n[步骤5] 验证去重功能...")

    # 提取所有 biz 参数
    biz_list = []
    for url in official_account_urls:
        biz_match = re.search(r'__biz=([^&]+)', url)
        if biz_match:
            biz_list.append(biz_match.group(1))

    # 检查是否有重复
    unique_biz_count = len(set(biz_list))
    total_biz_count = len(biz_list)

    print(f"  总 biz 数量: {total_biz_count}")
    print(f"  唯一 biz 数量: {unique_biz_count}")

    if unique_biz_count == total_biz_count:
        print(f"✓ 去重功能正常：没有重复的 biz")
        return True
    else:
        print(f"✗ 去重功能异常：存在 {total_biz_count - unique_biz_count} 个重复的 biz")
        return False


def main():
    """
    主测试函数：运行所有测试用例
    """
    print("\n" + "=" * 70)
    print("开始测试 _build_official_account_url 方法")
    print("=" * 70)
    print("\n⚠️  注意：此测试会发送网络请求到微信服务器")
    print("请确保网络连接正常\n")

    # 运行测试用例
    results = []

    # 测试1: 基础功能测试
    official_account_urls = test_build_official_account_url_basic()
    if official_account_urls:
        results.append(("基础功能测试", True))

        # 测试2: URL 格式验证
        result2 = test_url_format_validation(official_account_urls)
        results.append(("URL 格式验证", result2))

        # 测试3: 去重功能验证
        result3 = test_deduplication(official_account_urls)
        results.append(("去重功能验证", result3))
    else:
        results.append(("基础功能测试", False))

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
        print("\n🎉 所有测试通过！_build_official_account_url 方法工作正常")
    else:
        print("\n⚠️  部分测试失败，请检查日志输出")


if __name__ == "__main__":
    main()
