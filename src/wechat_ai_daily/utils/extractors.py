import requests
import re
import logging
from typing import Optional


def get_biz_from_wechat_article_url(url: str) -> Optional[str]:
    """
    从微信公众号文章页面中提取 biz 参数

    Args:
        url (str): 微信公众号文章的 URL 地址

    Returns:
        biz (str): 公众号的 biz 标识符（字符串），如果提取失败则返回 None
    """

    # 步骤1: 设置请求头，模拟浏览器访问
    # 这样做是为了避免被微信服务器识别为爬虫而拒绝访问
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept':
        'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    try:
        # 步骤2: 发送 HTTP GET 请求获取页面内容
        logging.info(f"正在访问页面: {url}")
        response = requests.get(url, headers=headers, timeout=10)

        # 检查请求是否成功（状态码 200 表示成功）
        if response.status_code != 200:
            logging.error(f"请求失败，状态码: {response.status_code}")
            return None

        # 获取页面的 HTML 源码
        html_content = response.text
        logging.info(f"成功获取页面内容，长度: {len(html_content)} 字符")

    except requests.exceptions.RequestException as e:
        # 捕获网络请求相关的异常（如超时、连接失败等）
        logging.exception(f"网络请求出错: {e}")
        return None

    # 步骤3: 使用正则表达式从 HTML 中提取 biz 参数
    # 正则表达式说明:
    # biz:\s*  - 匹配 "biz:" 后面可能有空格
    # ["\']    - 匹配单引号或双引号
    # ([^"\']+) - 捕获引号内的内容（biz 的值），不包含引号本身
    # ["\']    - 匹配结束的引号
    pattern = r'biz:\s*["\']([^"\']+)["\']'

    # 在 HTML 内容中搜索匹配的模式
    match = re.search(pattern, html_content)

    if match:
        # 如果找到匹配，提取第一个捕获组（即 biz 的值）
        biz = match.group(1)
        logging.info(f"成功提取 biz: {biz}")
        return biz
    else:
        # 如果没有找到匹配
        logging.error("未能在页面中找到 biz 参数")
        return None
