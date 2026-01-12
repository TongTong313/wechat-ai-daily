import requests
import re


def get_biz_from_wechat_article(url: str) -> str:
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
        print(f"正在访问页面: {url}")
        response = requests.get(url, headers=headers, timeout=10)

        # 检查请求是否成功（状态码 200 表示成功）
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return None

        # 获取页面的 HTML 源码
        html_content = response.text
        print(f"成功获取页面内容，长度: {len(html_content)} 字符")

    except requests.exceptions.RequestException as e:
        # 捕获网络请求相关的异常（如超时、连接失败等）
        print(f"网络请求出错: {e}")
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
        print(f"成功提取 biz: {biz}")
        return biz
    else:
        # 如果没有找到匹配
        print("未能在页面中找到 biz 参数")
        return None


def get_article_list_from_profile(biz: str) -> list:
    """
    通过模拟微信客户端访问公众号主页，获取文章列表

    Args:
        biz (str): 公众号的 biz 标识符

    Returns:
        list: 文章列表，每个元素包含文章标题和URL；失败返回空列表
    """

    # 步骤1: 构建公众号主页 URL
    # 这是微信公众号历史消息页面的 URL 格式
    profile_url = f"https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz={biz}&scene=124"
    print(f"公众号主页 URL: {profile_url}")

    # 步骤2: 设置微信客户端的请求头
    # 关键点：User-Agent 必须包含 "MicroMessenger" 来模拟微信内置浏览器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Mobile Safari/537.36 MicroMessenger/8.0.0.1920(0x28000030) NetType/WIFI Language/zh_CN',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://mp.weixin.qq.com/',
    }

    try:
        # 步骤3: 发送请求
        print("正在模拟微信客户端访问公众号主页...")
        response = requests.get(profile_url, headers=headers, timeout=15)

        print(f"响应状态码: {response.status_code}")
        print(f"响应内容长度: {len(response.text)} 字符")

        # 保存响应内容到文件，方便调试分析
        with open("response_debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("响应内容已保存到 response_debug.html，可以打开查看")

        # 检查是否被拦截（显示"请在微信客户端打开"）
        if "请在微信客户端打开链接" in response.text:
            print("访问被拦截：页面要求在微信客户端打开")
            print("方案一失败，微信有更严格的验证机制")
            return []

        # 步骤4: 解析文章列表
        # 微信公众号文章列表通常在 JavaScript 变量中，格式类似：
        # msgList = [{"app_msg_ext_info":{"title":"xxx","content_url":"xxx"}}, ...]
        html_content = response.text

        # 尝试提取文章列表数据
        # 方法1: 查找 msgList 变量
        msg_list_pattern = r'var\s+msgList\s*=\s*(\[.*?\]);'
        match = re.search(msg_list_pattern, html_content, re.DOTALL)

        if match:
            print("找到文章列表数据！")
            # 这里需要进一步解析 JSON 数据
            # 暂时返回原始匹配内容
            return [{"raw_data": match.group(1)}]

        # 方法2: 查找其他可能的文章链接模式
        article_pattern = r'content_url["\']?\s*:\s*["\']([^"\']+)["\']'
        articles = re.findall(article_pattern, html_content)

        if articles:
            print(f"找到 {len(articles)} 篇文章链接")
            return [{"url": url.replace("\\", "")} for url in articles]

        print("未能在页面中找到文章列表")
        return []

    except requests.exceptions.RequestException as e:
        print(f"网络请求出错: {e}")
        return []


def main():
    """
    主函数：测试 biz 提取和文章列表获取功能
    """
    # 测试 URL（你提供的微信公众号文章链接）
    test_url = "https://mp.weixin.qq.com/s/PCFTDO2DlbLaN7As7QIL9A"

    print("=" * 60)
    print("步骤1: 从文章页面提取 biz 参数")
    print("=" * 60)

    # 调用函数提取 biz
    biz = get_biz_from_wechat_article(test_url)

    if not biz:
        print("提取 biz 失败，无法继续")
        return

    print(f"\n提取到的 biz: {biz}")

    print("\n" + "=" * 60)
    print("步骤2: 尝试获取公众号文章列表")
    print("=" * 60)

    # 调用函数获取文章列表
    articles = get_article_list_from_profile(biz)

    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)

    if articles:
        print(f"成功获取 {len(articles)} 条数据")
        for i, article in enumerate(articles[:5], 1):  # 只显示前5条
            print(f"  {i}. {article}")
    else:
        print("未能获取文章列表")
        print("可能原因：微信有更严格的验证机制，仅模拟 User-Agent 不够")
        print("请查看 response_debug.html 文件分析具体响应内容")


if __name__ == "__main__":
    main()
