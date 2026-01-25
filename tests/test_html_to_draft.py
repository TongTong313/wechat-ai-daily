"""
测试将生成的 HTML 富文本转换为微信公众号草稿

本测试用于验证通过微信公众号 API 创建草稿的功能。

运行方式：
    uv run python -m pytest tests/test_html_to_draft.py -v -s
    
    或直接运行：
    uv run python tests/test_html_to_draft.py

前置条件：
    1. 需要设置环境变量 WECHAT_APPID 和 WECHAT_APPSECRET
    2. 公众号需要具备"发布能力"权限
    3. 需要在 output 目录有生成的 daily_rich_text_*.html 文件
"""

from bs4 import BeautifulSoup
import requests
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


class WeChatDraftAPI:
    """微信公众号草稿箱 API 封装类"""

    def __init__(self, appid: str = None, appsecret: str = None):
        """
        初始化微信 API 客户端

        Args:
            appid: 公众号 AppID（为空时从环境变量读取）
            appsecret: 公众号 AppSecret（为空时从环境变量读取）
        """
        self.appid = appid or os.getenv("WECHAT_APPID")
        self.appsecret = appsecret or os.getenv("WECHAT_APPSECRET")

        if not self.appid or not self.appsecret:
            raise ValueError(
                "未找到 AppID 或 AppSecret，请设置环境变量 WECHAT_APPID 和 WECHAT_APPSECRET"
            )

        self.access_token = None
        self.token_expires_at = 0

    def get_access_token(self) -> str:
        """
        获取 access_token

        token 有效期为 7200 秒，会自动缓存并在过期前刷新。

        Returns:
            access_token 字符串

        Raises:
            Exception: 获取 token 失败时抛出异常
        """
        # 如果 token 还有效，直接返回缓存的 token
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        # 请求新的 token
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.appid,
            "secret": self.appsecret
        }

        response = requests.get(url, params=params)
        result = response.json()

        if "access_token" not in result:
            raise Exception(f"获取 access_token 失败: {result}")

        # 缓存 token，设置过期时间（提前 5 分钟过期以确保安全）
        self.access_token = result["access_token"]
        self.token_expires_at = time.time() + result.get("expires_in", 7200) - 300

        print(f"✓ 成功获取 access_token: {self.access_token[:20]}...")
        return self.access_token

    def create_draft(self, articles: list) -> dict:
        """
        创建草稿

        Args:
            articles: 文章列表，每个文章是一个字典，包含以下字段：
                - title: 标题（必填）
                - author: 作者（选填）
                - digest: 摘要（选填）
                - content: 正文内容，HTML 格式（必填）
                - content_source_url: 原文链接（选填）
                - thumb_media_id: 封面图片 media_id（必填）
                - need_open_comment: 是否打开评论，0不打开，1打开（选填，默认0）
                - only_fans_can_comment: 是否粉丝才可评论，0所有人可评论，1粉丝才可评论（选填，默认0）

        Returns:
            包含 media_id 的字典，示例：{"media_id": "xxx"}

        Raises:
            Exception: 创建草稿失败时抛出异常
        """
        access_token = self.get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"

        data = {"articles": articles}

        # 手动序列化JSON，设置 ensure_ascii=False 避免中文被转义为 \uxxxx 格式
        json_data = json.dumps(data, ensure_ascii=False)
        response = requests.post(
            url,
            data=json_data.encode('utf-8'),
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        result = response.json()

        if result.get("errcode", 0) != 0:
            raise Exception(f"创建草稿失败: {result}")

        return result

    def upload_media(self, media_path: str, media_type: str = "image") -> str:
        """
        上传永久素材（图片）

        Args:
            media_path: 素材文件路径
            media_type: 素材类型，默认为 "image"

        Returns:
            media_id 字符串

        Raises:
            Exception: 上传失败时抛出异常
        """
        access_token = self.get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type={media_type}"

        with open(media_path, "rb") as f:
            files = {"media": f}
            response = requests.post(url, files=files)

        result = response.json()

        if "media_id" not in result:
            raise Exception(f"上传素材失败: {result}")

        print(f"✓ 成功上传素材: {result['media_id']}")
        return result["media_id"]


def html_to_wechat_format(html_content: str) -> str:
    """
    将 HTML 富文本转换为微信公众号支持的格式

    微信公众号对 HTML 格式有严格要求：
    1. 必须使用内联样式（inline style），不支持 <style> 标签
    2. 不支持部分 CSS 属性（如 position、float 等）
    3. 图片必须使用已上传的素材链接
    4. 链接必须使用 <a> 标签，且需要特殊处理
    5. h1-h6 标题标签有特殊限制，需要转换为 p 标签

    Args:
        html_content: 原始 HTML 内容

    Returns:
        转换后的 HTML 字符串
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # 步骤 1: 替换所有标题标签为 p 标签（避免微信 API 的标题限制）
    replaced_count = 0
    for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        for tag in soup.find_all(tag_name):
            # 创建新的 p 标签
            new_tag = soup.new_tag('p')
            # 复制所有属性（包括 style）
            new_tag.attrs = tag.attrs.copy()
            # 复制所有子节点（包括文本和嵌套标签）
            for child in list(tag.children):
                new_tag.append(child)
            # 替换原标签
            tag.replace_with(new_tag)
            replaced_count += 1

    if replaced_count > 0:
        print(f"  ⚠ 自动替换了 {replaced_count} 个标题标签 (h1-h6 → p)")

    # 步骤 2: 提取 body 内的 section 容器
    # 我们的模板已经使用了内联样式，所以直接提取主要内容即可
    main_section = soup.find("section")

    if not main_section:
        raise ValueError("未找到主要内容区域（<section> 标签）")

    # 返回主 section 的 HTML（这已经是微信格式了）
    return str(main_section)


def extract_articles_from_html(html_path: str) -> list:
    """
    从生成的 HTML 文件中提取文章信息

    Args:
        html_path: HTML 文件路径

    Returns:
        文章列表，每个文章包含 title、content、cover_url 等信息
    """
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

    # 查找所有文章卡片（通过注释标记识别）
    articles = []

    # 找到所有文章内容区域（从 ARTICLE_CARD_START 到 ARTICLE_CARD_END）
    content = html_content
    while "<!-- ===== ARTICLE_CARD_START =====" in content:
        start_idx = content.find("<!-- ===== ARTICLE_CARD_START =====")
        end_idx = content.find("<!-- ===== ARTICLE_CARD_END =====")

        if start_idx == -1 or end_idx == -1:
            break

        # 提取单篇文章的 HTML
        article_html = content[start_idx:end_idx +
                               len("<!-- ===== ARTICLE_CARD_END =====")]

        # 解析文章信息
        article_soup = BeautifulSoup(article_html, "html.parser")

        # 提取标题
        title_tag = article_soup.find("p") or article_soup.find("h2")  # 兼容新旧模板
        title = title_tag.get_text(strip=True) if title_tag else "无标题"

        # 提取封面图 URL
        img_tag = article_soup.find("img")
        cover_url = img_tag.get("src") if img_tag else ""

        # 提取摘要
        summary_sections = article_soup.find_all("section")
        summary = ""
        for section in summary_sections:
            text = section.get_text(strip=True)
            if len(text) > 50 and "内容速览" not in text:
                summary = text[:200]
                break

        articles.append({
            "title": title,
            "content": article_html,
            "cover_url": cover_url,
            "digest": summary
        })

        # 继续查找下一篇文章
        content = content[end_idx + len("<!-- ===== ARTICLE_CARD_END ====="):]

    return articles


def truncate_by_bytes(text: str, max_bytes: int, suffix: str = "...") -> str:
    """
    按字节数安全截断字符串（UTF-8编码）

    Args:
        text: 要截断的字符串
        max_bytes: 最大字节数
        suffix: 截断后添加的后缀（默认为"..."）

    Returns:
        截断后的字符串
    """
    # 如果不需要截断，直接返回
    if len(text.encode('utf-8')) <= max_bytes:
        return text

    # 计算后缀的字节数
    suffix_bytes = len(suffix.encode('utf-8'))
    available_bytes = max_bytes - suffix_bytes

    # 逐字符累加，直到超过可用字节数
    result = ""
    current_bytes = 0

    for char in text:
        char_bytes = len(char.encode('utf-8'))
        if current_bytes + char_bytes > available_bytes:
            break
        result += char
        current_bytes += char_bytes

    return result + suffix


def validate_draft_data(draft_article: dict) -> dict:
    """
    验证并修正草稿数据，确保符合微信公众号限制

    注意：微信API的字段限制是按字节数（UTF-8编码）计算的，而不是字符数

    Args:
        draft_article: 草稿文章数据

    Returns:
        修正后的草稿数据
    """
    # 标题限制：最多 32 字节（微信公众号接口限制，UTF-8编码）
    if "title" in draft_article:
        title_bytes = len(draft_article["title"].encode('utf-8'))
        if title_bytes > 32:
            draft_article["title"] = truncate_by_bytes(draft_article["title"], 32)
            print(f"  ⚠ 标题过长（{title_bytes} 字节），已截断至 32 字节")

    # 作者限制：最多 8 字节（微信公众号接口实际限制，UTF-8编码）
    # 注意：文档说16字，但实际限制更严格，只有8字节
    if "author" in draft_article:
        author_bytes = len(draft_article["author"].encode('utf-8'))
        if author_bytes > 8:
            draft_article["author"] = truncate_by_bytes(draft_article["author"], 8, suffix="")
            print(f"  ⚠ 作者名过长（{author_bytes} 字节），已截断至 8 字节")

    # 摘要限制：最多 54 字节（微信公众号接口实际限制，UTF-8编码）
    # 注意：文档说128字，但实际限制更严格，系统自动提取时只取前54字
    if "digest" in draft_article:
        digest_bytes = len(draft_article["digest"].encode('utf-8'))
        if digest_bytes > 54:
            draft_article["digest"] = truncate_by_bytes(draft_article["digest"], 54)
            print(f"  ⚠ 摘要过长（{digest_bytes} 字节），已截断至 54 字节")

    # 正文限制：微信API限制为20000字符或1MB文件大小
    # 用户反馈内容不会超过限制，所以不需要截断
    # if "content" in draft_article and len(draft_article["content"]) > 20000:
    #     original_length = len(draft_article["content"])
    #     draft_article["content"] = draft_article["content"][:20000]
    #     print(f"  ⚠ 正文过长，已从 {original_length} 字符截断至 20000 字符")

    return draft_article


def extract_articles_from_html(html_path: str) -> list:
    """
    从生成的 HTML 文件中提取文章信息

    Args:
        html_path: HTML 文件路径

    Returns:
        文章列表，每个文章包含 title、content、cover_url 等信息
    """
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

    # 查找所有文章卡片（通过注释标记识别）
    articles = []

    # 找到所有文章内容区域（从 ARTICLE_CARD_START 到 ARTICLE_CARD_END）
    content = html_content
    while "<!-- ===== ARTICLE_CARD_START =====" in content:
        start_idx = content.find("<!-- ===== ARTICLE_CARD_START =====")
        end_idx = content.find("<!-- ===== ARTICLE_CARD_END =====")

        if start_idx == -1 or end_idx == -1:
            break

        # 提取单篇文章的 HTML
        article_html = content[start_idx:end_idx +
                               len("<!-- ===== ARTICLE_CARD_END =====")]

        # 解析文章信息
        article_soup = BeautifulSoup(article_html, "html.parser")

        # 提取标题
        title_tag = article_soup.find("h2")
        title = title_tag.get_text(strip=True) if title_tag else "无标题"

        # 提取封面图 URL
        img_tag = article_soup.find("img")
        cover_url = img_tag.get("src") if img_tag else ""

        # 提取摘要
        summary_sections = article_soup.find_all("section")
        summary = ""
        for section in summary_sections:
            text = section.get_text(strip=True)
            if len(text) > 50 and "内容速览" not in text:
                summary = text[:200]
                break

        articles.append({
            "title": title,
            "content": article_html,
            "cover_url": cover_url,
            "digest": summary
        })

        # 继续查找下一篇文章
        content = content[end_idx + len("<!-- ===== ARTICLE_CARD_END ====="):]

    return articles


def test_create_draft_from_html():
    """
    测试将生成的 HTML 转换为微信公众号草稿

    测试流程：
    1. 检查环境变量是否配置
    2. 查找最新生成的 HTML 文件
    3. 解析 HTML 提取文章信息
    4. 转换为微信格式
    5. 上传封面图（如果需要）
    6. 创建草稿
    """
    print("\n" + "=" * 60)
    print("测试：将 HTML 转换为微信公众号草稿")
    print("=" * 60)

    # 步骤 1: 检查环境变量
    print("\n[1/6] 检查环境变量配置...")
    try:
        api = WeChatDraftAPI()
        print(f"✓ AppID: {api.appid[:8]}...")
        print(f"✓ AppSecret: {'*' * 20}")
    except ValueError as e:
        print(f"✗ 错误: {e}")
        print("\n提示：请在环境变量中设置 WECHAT_APPID 和 WECHAT_APPSECRET")
        print("  Windows PowerShell:")
        print("    $env:WECHAT_APPID='your_appid'")
        print("    $env:WECHAT_APPSECRET='your_appsecret'")
        print("\n  Linux/macOS:")
        print("    export WECHAT_APPID='your_appid'")
        print("    export WECHAT_APPSECRET='your_appsecret'")
        return

    # 步骤 2: 查找最新的 HTML 文件
    print("\n[2/6] 查找生成的 HTML 文件...")
    output_dir = project_root / "output"

    if not output_dir.exists():
        print(f"✗ 错误: 输出目录不存在: {output_dir}")
        print("  请先运行工作流生成 HTML 文件")
        return

    html_files = list(output_dir.glob("daily_rich_text_*.html"))

    if not html_files:
        print(f"✗ 错误: 未找到 HTML 文件")
        print(f"  查找路径: {output_dir}/daily_rich_text_*.html")
        return

    # 选择最新的文件
    latest_html = max(html_files, key=lambda p: p.stat().st_mtime)
    print(f"✓ 找到文件: {latest_html.name}")

    # 步骤 3: 解析 HTML
    print("\n[3/6] 解析 HTML 文件...")
    try:
        articles = extract_articles_from_html(str(latest_html))
        print(f"✓ 提取到 {len(articles)} 篇文章")

        for i, article in enumerate(articles, 1):
            print(f"  [{i}] {article['title']}")
    except Exception as e:
        print(f"✗ 解析失败: {e}")
        return

    # 步骤 4: 转换为微信格式
    print("\n[4/6] 转换为微信公众号格式...")
    try:
        # 将整个 HTML 作为一篇图文消息
        with open(latest_html, "r", encoding="utf-8") as f:
            full_html = f.read()

        print(f"  原始 HTML 长度: {len(full_html)} 字符")

        # 转换并清理 HTML（自动替换 h 标签）
        wechat_content = html_to_wechat_format(full_html)
        print(f"✓ 转换后长度: {len(wechat_content)} 字符")

        # 保存转换后的内容供调试
        debug_path = output_dir / "wechat_draft_content_cleaned.html"
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(wechat_content)
        print(f"✓ 已保存清理后的文件: {debug_path.name}")

    except Exception as e:
        print(f"✗ 转换失败: {e}")
        return

    # 步骤 5: 处理封面图（使用默认占位图）
    print("\n[5/6] 准备封面图...")

    # 检查是否有本地封面图
    cover_path = project_root / "templates" / "default_cover.png"

    if cover_path.exists():
        print(f"✓ 找到本地封面图: {cover_path.name}")
        try:
            thumb_media_id = api.upload_media(str(cover_path))
        except Exception as e:
            print(f"✗ 上传封面图失败: {e}")
            print("  使用占位 media_id")
            thumb_media_id = "PLACEHOLDER_MEDIA_ID"
    else:
        print(f"⚠ 未找到本地封面图: {cover_path}")
        print("  使用占位 media_id（实际创建草稿时需要真实图片）")
        thumb_media_id = "PLACEHOLDER_MEDIA_ID"

    # 步骤 6: 创建草稿
    print("\n[6/6] 创建微信公众号草稿...")

    # 构建草稿数据
    today = datetime.now().strftime("%Y年%m月%d日")

    # 标题限制为 32 字节（微信公众号接口限制，UTF-8编码）
    draft_title = f"AI公众号每日导读 - {today}"
    title_bytes = len(draft_title.encode('utf-8'))
    if title_bytes > 32:
        draft_title = truncate_by_bytes(draft_title, 32)
        print(f"  ⚠ 标题过长（{title_bytes} 字节），已截断至 32 字节")

    # 摘要设为空，让微信系统自动提取前54个字
    draft_digest = ""

    draft_articles = [{
        "title": draft_title,
        "author": "Double童发发",
        "digest": draft_digest,
        "content": wechat_content,
        "content_source_url": "",
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0
    }]

    # 验证并修正草稿数据
    print("\n验证草稿数据...")
    draft_articles[0] = validate_draft_data(draft_articles[0])
    print(
        f"  标题: {draft_articles[0]['title'][:50]}... ({len(draft_articles[0]['title'])} 字符)")
    print(
        f"  作者: {draft_articles[0]['author']} ({len(draft_articles[0]['author'])} 字符)")
    print(
        f"  摘要: {draft_articles[0]['digest'][:30]}... ({len(draft_articles[0]['digest'])} 字符)")
    print(f"  正文长度: {len(draft_articles[0]['content'])} 字符")

    try:
        result = api.create_draft(draft_articles)
        print(f"✓ 草稿创建成功!")
        print(f"  media_id: {result.get('media_id')}")
        print(f"\n请前往微信公众号后台查看草稿：")
        print(f"  https://mp.weixin.qq.com/")

    except Exception as e:
        print(f"✗ 创建草稿失败: {e}")

        # 如果是因为占位 media_id 失败，给出提示
        if thumb_media_id == "PLACEHOLDER_MEDIA_ID":
            print("\n提示：需要上传真实的封面图才能创建草稿")
            print("  1. 准备一张 JPG/PNG 图片（推荐尺寸 900x383）")
            print(f"  2. 保存到: {cover_path}")
            print("  3. 重新运行此测试")

        return

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    # 直接运行测试
    test_create_draft_from_html()
