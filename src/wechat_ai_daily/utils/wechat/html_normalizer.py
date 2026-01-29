# 微信公众号富文本标准化工具

import re
from bs4 import BeautifulSoup, NavigableString, Tag

# 样式重置：避免公众号编辑器或接口注入默认边距


def _style_has_property(style: str, prop: str) -> bool:
    """判断 style 中是否已经显式声明了指定属性或其子属性."""
    # 例如：padding / padding-top / padding-left 都算显式声明
    style_lower = style.lower()
    return bool(
        re.search(rf"\\b{prop}\\s*:", style_lower)
        or re.search(rf"\\b{prop}-[a-z]+\\s*:", style_lower)
    )


def _build_reset_style(original_style: str) -> str:
    """根据原样式生成最小化的重置样式，避免覆盖已有 padding/margin."""
    reset_parts = []
    # 如果已经显式设置 margin，就不再重复注入 margin:0
    if not _style_has_property(original_style, "margin"):
        reset_parts.append("margin:0;")
    # 如果已经显式设置 padding，就不再重复注入 padding:0
    if not _style_has_property(original_style, "padding"):
        reset_parts.append("padding:0;")
    return " ".join(reset_parts).strip()


def _prepend_reset_style(tag: Tag) -> None:
    """为块级容器追加样式重置，避免默认间距影响."""
    # 公众号编辑器会为块级标签添加默认 margin/padding
    # 为避免显示间距被放大/缩小，先统一重置，再拼接原有样式
    # 这样原有显式样式仍有效，同时默认样式被覆盖
    original_style = (tag.get("style") or "").strip()
    # 为避免覆盖已显式设置的 padding/margin，按需生成最小化重置样式
    reset_style = _build_reset_style(original_style)
    if not reset_style:
        return
    if original_style:
        tag["style"] = f"{reset_style} {original_style}"
    else:
        tag["style"] = reset_style


def _remove_blank_text_nodes(root: Tag) -> None:
    """移除空白文本节点，避免复制/发布时产生多余空行."""
    # HTML 源码的换行/缩进在浏览器中常被忽略
    # 但在公众号编辑器或 API 中会被解析成空段落
    # 这里只移除纯空白节点，不影响实际内容文字
    for text in list(root.descendants):
        if isinstance(text, NavigableString) and str(text).strip() == "":
            text.extract()


def normalize_wechat_html(html_content: str, return_full_html: bool = False) -> str:
    """统一规范微信公众号富文本HTML，减少间距放大/缩小问题."""
    # 解析 HTML，构建 DOM 树，便于统一处理
    soup = BeautifulSoup(html_content, "html.parser")

    # 优先定位主容器 section，没有则使用 body 或整棵树
    # 这样输出内容更接近公众号编辑器可识别的主体结构
    main_section = soup.find("section") or soup.body or soup

    # 清理主容器内部空白文本节点
    _remove_blank_text_nodes(main_section)

    # 清理 body 直属空白文本节点，避免容器前后额外空行
    if soup.body and soup.body is not main_section:
        _remove_blank_text_nodes(soup.body)

    # 为块级容器统一补充 margin/padding 重置，防止默认样式影响间距
    for tag in main_section.find_all(["section", "div", "p"]):
        _prepend_reset_style(tag)

    # 输出主容器 HTML，移除标签间空白，避免微信误判为段落
    # 使用 "><" 方式清理标签间空白，避免破坏文本内容
    normalized_main = str(main_section)
    normalized_main = re.sub(r">\s+<", "><", normalized_main)

    if not return_full_html:
        return normalized_main

    # 输出完整 HTML，便于本地浏览器预览和复制
    # 同样去除标签间空白，保证复制到公众号时不引入空行
    full_html = str(soup)
    full_html = re.sub(r">\s+<", "><", full_html)
    return full_html
