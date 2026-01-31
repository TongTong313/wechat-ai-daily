# 微信公众号富文本标准化工具

import re
from bs4 import BeautifulSoup, NavigableString, Tag

# 样式重置：避免公众号编辑器或接口注入默认边距


def _build_reset_style() -> str:
    """生成统一的重置样式，强制覆盖默认的 padding/margin/text-indent."""
    # 始终重置 margin/padding/text-indent，利用 CSS 覆盖规则（后面的覆盖前面的）
    # 这样可以确保未显式设置的属性被重置为 0，而不是继承微信默认样式
    # 例如：如果原样式只有 margin-top: 10px，
    # 拼接后为 "margin: 0; padding: 0; text-indent: 0; margin-top: 10px"
    # 此时 margin-left/right/bottom 都会被重置为 0，避免了微信默认样式的干扰
    return "margin: 0; padding: 0; text-indent: 0;"


def _prepend_reset_style(tag: Tag) -> None:
    """为块级容器追加样式重置，避免默认间距影响."""
    # 公众号编辑器会为块级标签添加默认 margin/padding
    # 为避免显示间距被放大/缩小，先统一重置，再拼接原有样式
    # 这样原有显式样式仍有效，同时默认样式被覆盖
    original_style = (tag.get("style") or "").strip()
    
    # 获取重置样式
    reset_style = _build_reset_style()
    
    if original_style:
        tag["style"] = f"{reset_style} {original_style}"
    else:
        tag["style"] = reset_style


def _clean_text_nodes(root: Tag) -> None:
    """清理文本节点：移除纯空白节点，去除源码缩进."""
    # HTML 源码的换行/缩进在浏览器中常被忽略
    # 但在公众号编辑器或 API 中会被解析成空段落或可见的缩进
    for text in list(root.descendants):
        if not isinstance(text, NavigableString):
            continue
            
        content = str(text)
        stripped = content.strip()
        
        # 1. 移除纯空白节点
        if not stripped:
            text.extract()
            continue
            
        # 2. 如果文本包含换行符，说明是源码格式化产生的缩进，安全去除首尾空白
        # 这能解决 <section>\n    内容\n</section> 导致的缩进问题
        if '\n' in content:
            # 只有当去除空白后内容确实改变了才替换，避免不必要的操作
            if content != stripped:
                text.replace_with(stripped)


def normalize_wechat_html(html_content: str, return_full_html: bool = False) -> str:
    """统一规范微信公众号富文本HTML，减少间距放大/缩小问题."""
    # 解析 HTML，构建 DOM 树，便于统一处理
    soup = BeautifulSoup(html_content, "html.parser")

    # 优先定位主容器 section，没有则使用 body 或整棵树
    # 这样输出内容更接近公众号编辑器可识别的主体结构
    main_section = soup.find("section") or soup.body or soup

    # 清理主容器内部文本节点（移除空白、去除缩进）
    _clean_text_nodes(main_section)

    # 清理 body 直属文本节点，避免容器前后额外空行
    if soup.body and soup.body is not main_section:
        _clean_text_nodes(soup.body)

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
