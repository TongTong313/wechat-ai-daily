"""
测试 DailyGenerator 的 HTML 内容获取功能

运行方式：
    python -m pytest tests/test_daily_generate.py -v -s
    
    或直接运行：
    python tests/test_daily_generate.py
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, "src"))

from wechat_ai_daily.workflows.daily_generate import DailyGenerator


def test_get_html_content():
    """测试获取公众号文章HTML内容
    
    测试步骤：
    1. 创建 DailyGenerator 实例
    2. 调用 _get_html_content 获取指定 URL 的 HTML
    3. 将 HTML 内容保存到文件供查看
    """
    # 测试用的公众号文章 URL
    test_url = "https://mp.weixin.qq.com/s/yWYBBUc1NzbgVVVWmI0nvQ"
    
    # 创建输出目录（如果不存在）
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 输出文件路径
    output_path = os.path.join(output_dir, "html_content.html")
    
    print(f"\n{'='*60}")
    print(f"测试 URL: {test_url}")
    print(f"{'='*60}")
    
    # 创建 DailyGenerator 实例
    generator = DailyGenerator()
    
    # 获取 HTML 内容
    print("正在获取 HTML 内容...")
    html_content = generator._get_html_content(test_url)
    
    # 保存到文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\n{'='*60}")
    print(f"获取成功！")
    print(f"HTML 内容长度: {len(html_content)} 字符")
    print(f"文件已保存到: {output_path}")
    print(f"{'='*60}")
    
    # 基本断言：确保获取到了内容
    assert html_content is not None
    assert len(html_content) > 0
    
    return html_content


if __name__ == "__main__":
    # 直接运行此文件时执行测试
    test_get_html_content()
