"""测试每日日报生成器工作流

这个测试文件用于测试 DailyGenerator 的 build_workflow 是否能正常运行。
使用 output/articles_20260119.md 作为测试数据。

运行方式:
    uv run pytest tests/test_daily_generate_workflow.py -v -s
    
或直接运行:
    uv run python tests/test_daily_generate_workflow.py
"""

import sys
import os
import pytest
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# 将 src 目录添加到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 加载 .env 环境变量
from wechat_ai_daily.utils.env_loader import load_env
load_env()

from wechat_ai_daily.workflows.daily_generate import DailyGenerator


# 配置日志 - 使用更详细的格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


def print_status(message: str, status: str = "INFO"):
    """打印带状态的信息

    Args:
        message: 要显示的信息
        status: 状态类型 (INFO, OK, WARN, ERROR, WAIT)
    """
    icons = {
        "INFO": "ℹ️ ",
        "OK": "✅",
        "WARN": "⚠️ ",
        "ERROR": "❌",
        "WAIT": "⏳",
        "START": "🚀",
        "END": "🏁",
    }
    icon = icons.get(status, "")
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {icon} {message}", flush=True)


@pytest.fixture
def test_markdown_file():
    """测试数据文件路径"""
    project_root = Path(__file__).parent.parent
    markdown_file = project_root / "output" / "articles_20260119.md"

    assert markdown_file.exists(), f"测试文件不存在: {markdown_file}"

    return str(markdown_file)


@pytest.fixture
def daily_generator():
    """创建 DailyGenerator 实例"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        pytest.skip("未设置 DASHSCOPE_API_KEY 环境变量，跳过测试")

    generator = DailyGenerator(
        model="qwen-plus",
        enable_thinking=True,
        thinking_budget=1024,
        max_retries=2
    )

    return generator


def test_parse_article_urls(daily_generator, test_markdown_file):
    """测试解析文章链接功能"""
    print_status("开始测试: 解析文章链接", "START")

    urls = daily_generator._parse_article_urls(test_markdown_file)

    assert len(urls) > 0, "应该解析到至少一个链接"
    print_status(f"成功解析到 {len(urls)} 个文章链接", "OK")

    for i, url in enumerate(urls, 1):
        assert url.startswith("https://mp.weixin.qq.com/s/"), f"链接格式不正确: {url}"
        print_status(f"  {i}. {url}", "INFO")

    print_status("文章链接解析测试通过", "OK")


@pytest.mark.asyncio
async def test_get_html_content(daily_generator, test_markdown_file):
    """测试获取HTML内容功能"""
    print_status("开始测试: 获取HTML内容", "START")

    urls = daily_generator._parse_article_urls(test_markdown_file)
    assert len(urls) > 0, "需要至少一个测试链接"

    test_url = urls[0]
    print_status(f"测试链接: {test_url}", "INFO")
    print_status("正在获取HTML内容（可能需要几秒钟）...", "WAIT")

    html_content = daily_generator._get_html_content(test_url)

    assert len(html_content) > 0, "HTML内容不应为空"
    print_status(f"成功获取HTML内容，长度: {len(html_content)} 字符", "OK")


@pytest.mark.asyncio
async def test_extract_article_metadata(daily_generator, test_markdown_file):
    """测试提取文章元数据功能"""
    print_status("开始测试: 提取文章元数据", "START")

    urls = daily_generator._parse_article_urls(test_markdown_file)
    test_url = urls[0]

    print_status("正在获取HTML内容...", "WAIT")
    html_content = daily_generator._get_html_content(test_url)

    print_status("正在提取元数据...", "WAIT")
    metadata = daily_generator._extract_article_metadata(
        html_content, test_url)

    assert metadata.title, "标题不应为空"
    assert metadata.article_url == test_url, "URL应该匹配"

    print_status(f"文章标题: {metadata.title}", "INFO")
    print_status(f"公众号名称: {metadata.account_name}", "INFO")
    print_status(f"发布时间: {metadata.publish_time}", "INFO")
    print_status(f"正文长度: {len(metadata.content)} 字符", "INFO")

    print_status("文章元数据提取测试通过", "OK")


@pytest.mark.asyncio
async def test_generate_article_summary(daily_generator, test_markdown_file):
    """测试生成文章摘要功能（调用LLM，耗时较长）"""
    print_status("开始测试: 生成文章摘要", "START")
    print_status("⚠️  此测试会调用LLM API，可能需要30-60秒，请耐心等待...", "WARN")

    urls = daily_generator._parse_article_urls(test_markdown_file)
    test_url = urls[0]

    print_status("正在获取HTML内容...", "WAIT")
    html_content = daily_generator._get_html_content(test_url)

    print_status("正在提取元数据...", "WAIT")
    metadata = daily_generator._extract_article_metadata(
        html_content, test_url)
    print_status(f"文章: {metadata.title}", "INFO")

    print_status("正在调用LLM生成摘要（这一步比较耗时）...", "WAIT")
    start_time = datetime.now()

    summary = await daily_generator._generate_article_summary(metadata)

    elapsed = (datetime.now() - start_time).total_seconds()
    print_status(f"LLM调用完成，耗时: {elapsed:.1f}秒", "INFO")

    assert summary is not None, "摘要不应为None"
    assert 0 <= summary.score <= 100, "评分应在0-100范围内"

    print_status(f"推荐评分: {summary.score}/100", "INFO")
    print_status(f"文章摘要: {summary.summary[:100]}...", "INFO")
    print_status(f"推荐理由: {summary.reason[:80]}...", "INFO")

    print_status("文章摘要生成测试通过", "OK")


@pytest.mark.asyncio
async def test_build_workflow_full(daily_generator, test_markdown_file):
    """测试完整的工作流（主要测试）

    ⚠️ 此测试会处理所有文章并调用多次LLM，预计耗时2-5分钟
    """
    print_status("=" * 60, "INFO")
    print_status("开始测试: 完整工作流", "START")
    print_status("⚠️  此测试会处理所有文章并多次调用LLM", "WARN")
    print_status("⚠️  预计耗时 2-5 分钟，请耐心等待...", "WARN")
    print_status("=" * 60, "INFO")

    start_time = datetime.now()

    # 执行完整工作流
    await daily_generator.build_workflow(test_markdown_file)

    elapsed = (datetime.now() - start_time).total_seconds()
    print_status(f"工作流执行完成，总耗时: {elapsed:.1f}秒 ({elapsed/60:.1f}分钟)", "OK")

    # 验证输出文件
    output_file = Path(
        "output") / f"daily_rich_text_{datetime.now().strftime('%Y%m%d')}.html"

    if output_file.exists():
        print_status(f"输出文件已生成: {output_file}", "OK")
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        print_status(f"输出文件大小: {len(content)} 字符", "INFO")
    else:
        print_status("未生成输出文件（可能是文章评分都低于90分）", "WARN")

    print_status("完整工作流测试通过", "OK")


def test_run_sync_method(daily_generator, test_markdown_file):
    """测试同步入口方法 run()

    ⚠️ 此测试与 test_build_workflow_full 功能相同，只测试一个即可
    """
    print_status("=" * 60, "INFO")
    print_status("开始测试: 同步入口方法 run()", "START")
    print_status("⚠️  此测试会处理所有文章并多次调用LLM", "WARN")
    print_status("⚠️  预计耗时 2-5 分钟，请耐心等待...", "WARN")
    print_status("=" * 60, "INFO")

    start_time = datetime.now()

    # 调用同步方法
    daily_generator.run(test_markdown_file)

    elapsed = (datetime.now() - start_time).total_seconds()
    print_status(f"执行完成，总耗时: {elapsed:.1f}秒 ({elapsed/60:.1f}分钟)", "OK")
    print_status("同步方法测试通过", "OK")


# ========== 直接运行脚本时的入口 ==========
if __name__ == "__main__":
    """
    直接运行此文件进行测试

    使用方法:
        uv run python tests/test_daily_generate_workflow.py
    """
    print("\n" + "=" * 60)
    print("🧪 每日日报生成器工作流测试")
    print("=" * 60 + "\n")

    # 设置测试文件路径
    project_root = Path(__file__).parent.parent
    test_file = project_root / "output" / "articles_20260119.md"

    if not test_file.exists():
        print_status(f"测试文件不存在: {test_file}", "ERROR")
        sys.exit(1)

    # 检查环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print_status("未设置 DASHSCOPE_API_KEY 环境变量", "ERROR")
        print_status(
            "请设置环境变量: export DASHSCOPE_API_KEY='your_api_key'", "INFO")
        sys.exit(1)

    print_status(f"测试文件: {test_file}", "INFO")
    print_status(f"环境变量 DASHSCOPE_API_KEY: 已设置", "OK")

    # 创建生成器
    print_status("正在初始化 DailyGenerator...", "WAIT")
    generator = DailyGenerator(
        model="qwen-plus",
        enable_thinking=True,
        thinking_budget=1024,
        max_retries=2
    )
    print_status("DailyGenerator 初始化完成", "OK")

    # 步骤1: 测试解析文章链接
    print("\n" + "-" * 40)
    print_status("步骤 1/4: 解析文章链接", "START")
    urls = generator._parse_article_urls(str(test_file))
    print_status(f"解析到 {len(urls)} 个文章链接", "OK")
    for i, url in enumerate(urls, 1):
        print_status(f"  {i}. {url}", "INFO")

    # 步骤2: 测试获取HTML内容
    print("\n" + "-" * 40)
    print_status("步骤 2/4: 获取第一篇文章HTML内容", "START")
    print_status("正在请求网页...", "WAIT")
    html_content = generator._get_html_content(urls[0])
    print_status(f"HTML内容长度: {len(html_content)} 字符", "OK")

    # 步骤3: 测试提取元数据
    print("\n" + "-" * 40)
    print_status("步骤 3/4: 提取文章元数据", "START")
    metadata = generator._extract_article_metadata(html_content, urls[0])
    print_status(f"标题: {metadata.title}", "INFO")
    print_status(f"公众号: {metadata.account_name}", "INFO")
    print_status(f"发布时间: {metadata.publish_time}", "INFO")
    print_status(f"正文长度: {len(metadata.content)} 字符", "OK")

    # 步骤4: 运行完整工作流
    print("\n" + "-" * 40)
    print_status("步骤 4/4: 执行完整工作流", "START")
    print_status("⚠️  此步骤会处理所有文章并多次调用LLM", "WARN")
    print_status("⚠️  预计耗时 2-5 分钟，每篇文章会显示进度...", "WARN")
    print("-" * 40 + "\n")

    start_time = datetime.now()
    generator.run(str(test_file))
    elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 60)
    print_status(f"🎉 所有测试完成！总耗时: {elapsed:.1f}秒 ({elapsed/60:.1f}分钟)", "END")
    print("=" * 60)

    # 检查输出文件
    output_file = Path(
        "output") / f"daily_rich_text_{datetime.now().strftime('%Y%m%d')}.html"
    if output_file.exists():
        print_status(f"生成的文件: {output_file}", "OK")
    else:
        print_status("未生成输出文件", "WARN")
