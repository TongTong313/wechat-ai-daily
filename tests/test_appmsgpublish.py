"""
测试 /cgi-bin/appmsgpublish 接口

该接口可以获取指定公众号的文章列表，数据更丰富。

使用方法：
    uv run python tests/test_appmsgpublish.py
"""

from dotenv import load_dotenv
import os
import sys
import json
import time
import requests
from pathlib import Path

# 设置 stdout 编码为 UTF-8（Windows 兼容）
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / ".env")


def test_appmsgpublish():
    """
    测试 /cgi-bin/appmsgpublish 接口

    该接口可以获取指定公众号（通过 fakeid）的文章列表。
    fakeid=MzA3MzI4MjgzMw== 是"机器之心"公众号的标识。
    """
    # 从环境变量获取认证信息
    token = os.getenv("WECHAT_API_TOKEN")
    cookie = os.getenv("WECHAT_API_COOKIE")

    if not token or not cookie:
        print("错误：请在 .env 文件中配置 WECHAT_API_TOKEN 和 WECHAT_API_COOKIE")
        return

    print(f"Token: {token}")
    print(f"Cookie: {cookie[:50]}...")
    print("-" * 80)

    # 基础 URL
    base_url = "https://mp.weixin.qq.com/cgi-bin/appmsgpublish"

    # 请求参数
    # fakeid=MzA3MzI4MjgzMw== 是"机器之心"公众号的 fakeid
    params = {
        "sub": "list",
        "search_field": "null",
        "begin": 0,
        "count": 10,  # 获取 10 条记录
        "query": "",
        "fakeid": "MzA3MzI4MjgzMw==",  # 机器之心的 fakeid
        "type": "101_1",
        "free_publish_type": 1,
        "sub_action": "list_ex",
        "token": token,
        "lang": "zh_CN",
        "f": "json",
        "ajax": 1
    }

    # 请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://mp.weixin.qq.com/cgi-bin/appmsg",
        "Cookie": cookie
    }

    print("发送请求到:", base_url)
    print("-" * 80)

    try:
        response = requests.get(base_url, params=params,
                                headers=headers, timeout=30)

        print(f"HTTP 状态码: {response.status_code}")
        print("-" * 80)

        data = response.json()

        # 检查请求是否成功
        base_resp = data.get("base_resp", {})
        if base_resp.get("ret") != 0:
            print(f"请求失败: {base_resp.get('err_msg')}")
            return

        print("请求成功！")
        print("=" * 80)

        # 解析 publish_page（它是一个 JSON 字符串）
        publish_page_str = data.get("publish_page", "{}")
        publish_page = json.loads(publish_page_str)

        # 显示统计信息
        print(f"总文章数: {publish_page.get('total_count')}")
        print(f"发布数量: {publish_page.get('publish_count')}")
        print(f"群发数量: {publish_page.get('masssend_count')}")
        print("=" * 80)

        # 解析文章列表
        publish_list = publish_page.get("publish_list", [])
        print(f"\n获取到 {len(publish_list)} 条发布记录：\n")

        article_count = 0
        for i, item in enumerate(publish_list):
            publish_type = item.get("publish_type")
            type_name = "发布" if publish_type == 1 else "群发" if publish_type == 101 else f"类型{publish_type}"

            # publish_info 也是 JSON 字符串
            publish_info_str = item.get("publish_info", "{}")
            publish_info = json.loads(publish_info_str)

            # 获取文章列表
            appmsgex = publish_info.get("appmsgex", [])

            print(f"[{i+1}] {type_name} - 包含 {len(appmsgex)} 篇文章")

            for article in appmsgex:
                article_count += 1
                title = article.get("title", "无标题")
                link = article.get("link", "")
                create_time = article.get("create_time", 0)
                update_time = article.get("update_time", 0)

                # 转换时间戳
                create_time_str = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(create_time)) if create_time else "未知"

                print(f"    - {title}")
                print(f"       链接: {link}")
                print(f"       时间: {create_time_str}")
                print()

        print("=" * 80)
        print(f"共解析出 {article_count} 篇文章")

    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        print("原始响应:", response.text[:1000])
    except requests.RequestException as e:
        print(f"请求失败: {e}")


def compare_with_appmsg():
    """
    对比 appmsgpublish 和现有 appmsg 接口的区别
    """
    print("\n" + "=" * 80)
    print("对比现有 appmsg 接口")
    print("=" * 80 + "\n")

    token = os.getenv("WECHAT_API_TOKEN")
    cookie = os.getenv("WECHAT_API_COOKIE")

    if not token or not cookie:
        print("错误：请在 .env 文件中配置 WECHAT_API_TOKEN 和 WECHAT_API_COOKIE")
        return

    # 现有的 appmsg 接口
    base_url = "https://mp.weixin.qq.com/cgi-bin/appmsg"

    params = {
        "action": "list_ex",
        "begin": 0,
        "count": 5,
        "fakeid": "MzA3MzI4MjgzMw==",  # 机器之心
        "type": 9,
        "query": "",
        "token": token,
        "lang": "zh_CN",
        "f": "json",
        "ajax": 1
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://mp.weixin.qq.com/cgi-bin/appmsg",
        "Cookie": cookie
    }

    try:
        response = requests.get(base_url, params=params,
                                headers=headers, timeout=30)
        data = response.json()

        base_resp = data.get("base_resp", {})
        if base_resp.get("ret") != 0:
            print(f"appmsg 接口请求失败: {base_resp.get('err_msg')}")
            return

        print("appmsg 接口返回的文章：")
        for article in data.get("app_msg_list", []):
            title = article.get("title", "无标题")
            create_time = article.get("create_time", 0)
            create_time_str = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(create_time)) if create_time else "未知"
            print(f"  - {title}")
            print(f"     时间: {create_time_str}")
            print()

    except Exception as e:
        print(f"请求失败: {e}")


if __name__ == "__main__":
    # 测试 appmsgpublish 接口
    test_appmsgpublish()

    # 对比现有 appmsg 接口
    compare_with_appmsg()
