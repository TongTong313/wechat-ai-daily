# -*- coding: utf-8 -*-
"""临时测试脚本：测试 _extract_article_metadata 函数"""

from src.wechat_ai_daily.workflows.daily_generate import DailyGenerator

generator = DailyGenerator()

url = 'https://mp.weixin.qq.com/s/H8aS7_QVhS0Who_tJee69Q'

try:
    # 获取 HTML 内容
    html_content = generator._get_html_content(url)
    
    # 提取元数据
    metadata = generator._extract_article_metadata(html_content, url)
    
    # 输出到文件
    with open('tests/output/extract_result.txt', 'w', encoding='utf-8') as f:
        f.write('=== 提取结果 ===\n')
        f.write(f'HTML 长度: {len(html_content)} 字符\n\n')
        f.write(f'标题: {metadata.title}\n')
        f.write(f'作者: {metadata.author}\n')
        f.write(f'发布时间: {metadata.publish_time}\n')
        f.write(f'公众号: {metadata.account_name}\n')
        f.write(f'摘要: {metadata.description}\n')
        f.write(f'封面URL: {metadata.cover_url}\n')
        f.write(f'正文长度: {len(metadata.content)} 字符\n')
        f.write(f'图片数量: {len(metadata.images)} 张\n\n')
        f.write('=== 正文内容 ===\n')
        f.write(metadata.content)
    
    print('结果已保存到 tests/output/extract_result.txt')
    
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()
