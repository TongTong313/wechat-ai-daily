"""
测试微信公众号自动发布工作流

本测试用于验证通过微信公众号 API 创建草稿的功能。

运行方式：
    uv run python -m pytest tests/test_daily_publish.py -v -s
    
    或直接运行：
    uv run python tests/test_daily_publish.py

前置条件：
    1. 需要在 configs/config.yaml 中配置 publish_config:
       - appid: 微信公众号 AppID（可选，优先使用环境变量）
       - appsecret: 微信公众号 AppSecret（可选，优先使用环境变量）
       - cover_path: 封面图片路径（如 templates/default_cover.png）
       - author: 作者名称
    2. 或者在项目根目录创建 .env 文件（推荐）：
       WECHAT_APPID=your_appid
       WECHAT_APPSECRET=your_appsecret
    3. 公众号需要具备"发布能力"权限
    4. 需要在 output 目录有生成的 daily_rich_text_*.html 文件
"""

# 添加项目根目录到 Python 路径
import pytest
import logging
import argparse
from wechat_ai_daily.workflows.daily_publish import DailyPublisher
from wechat_ai_daily.utils.env_loader import load_env
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 加载 .env 环境变量（必须在其他模块导入前调用）
load_env()


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


DEFAULT_HTML_PATH = "output/daily_rich_text_20260122.html"


def _get_title_from_user() -> str:
    """交互式输入标题（需要 -s 运行 pytest）"""
    user_input = input("请输入微信公众号草稿标题: ").strip()
    if not user_input:
        raise ValueError("标题不能为空，请输入有效的草稿标题")
    return user_input


def test_daily_publisher_full_workflow(title: str | None = None):
    """测试 DailyPublisher 全流程

    说明：
    - title 由用户输入，或在直接运行脚本时通过命令行传入
    - digest 默认为空字符串
    - html_path 使用默认值，也可以在测试代码中修改 DEFAULT_HTML_PATH
    - 需要真实微信公众号凭证，会实际创建草稿
    """
    print("\n" + "=" * 70)
    print("测试 DailyPublisher 全流程")
    print("=" * 70)

    # 测试用的 HTML 文件路径（默认值可修改）
    html_path = DEFAULT_HTML_PATH

    # 检查 HTML 文件是否存在
    if not Path(html_path).exists():
        pytest.skip(f"测试文件不存在: {html_path}，请先生成日报文件")

    # 创建发布器实例
    print("\n🚀 正在初始化 DailyPublisher...")
    publisher = DailyPublisher()

    # 检查配置是否齐全（检查 WeChatAPI 实例中的凭证，而不是 config.yaml）
    if not publisher.wechat_api.appid or not publisher.wechat_api.appsecret:
        pytest.skip("未配置微信公众号凭证，跳过草稿创建测试")

    # 获取标题（优先使用传入值，否则交互输入）
    title = title.strip() if title else ""
    if not title:
        title = _get_title_from_user()

    # digest 默认为空
    digest = ""

    # 运行完整工作流
    print(f"\n📄 HTML 路径: {html_path}")
    print(f"📝 标题: {title}")
    print("🧾 摘要: （空）")
    draft_media_id = publisher.run(
        html_path=html_path,
        title=title,
        digest=digest
    )

    # 验证结果
    assert draft_media_id, "草稿创建失败，未返回 media_id"
    print(f"\n✅ 草稿创建成功，media_id: {draft_media_id}")


if __name__ == "__main__":
    """直接运行测试"""
    print("\n" + "="*70)
    print("微信公众号自动发布工作流测试")
    print("="*70)

    # 运行测试
    try:
        parser = argparse.ArgumentParser(description="DailyPublisher 全流程测试")
        parser.add_argument("--title", type=str, default="", help="草稿标题")
        args = parser.parse_args()

        # 测试：DailyPublisher 全流程
        test_daily_publisher_full_workflow(title=args.title)

        print("\n" + "="*70)
        print("✅ 所有测试通过")
        print("="*70)

    except Exception as e:
        print("\n" + "="*70)
        print(f"❌ 测试失败: {e}")
        print("="*70)
        sys.exit(1)
