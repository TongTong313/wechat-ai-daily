"""
测试 APIArticleCollector + DailyGenerator 完整工作流

本测试验证从 API 采集文章到生成日报的完整流程。

运行方式：
    uv run python tests/test_api_daily_workflow.py

前置条件：
    1. 需要有一个微信公众号账号
    2. 登录 mp.weixin.qq.com 后台，获取 cookie 和 token
    3. 已在 config.yaml 中配置 cookie、token、account_names、target_date
    4. 已配置 DASHSCOPE_API_KEY 环境变量（用于 LLM 生成摘要）
"""

from wechat_ai_daily.utils.wechat import ArticleError
from wechat_ai_daily.workflows.daily_generate import DailyGenerator
from wechat_ai_daily.workflows.api_article_collector import APIArticleCollector
from wechat_ai_daily.utils.env_loader import load_env
import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from ruamel.yaml import YAML

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 加载 .env 环境变量
load_env()


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler("logs/test_api_daily_workflow.log",
                            encoding='utf-8')  # 输出到文件
    ]
)

logger = logging.getLogger(__name__)


async def test_complete_workflow(config_path: str = "configs/config.yaml"):
    """
    测试完整的 API 采集 + 日报生成工作流

    所有参数从配置文件读取：
    - cookie: 微信公众平台 cookie
    - token: 微信公众平台 token
    - account_names: 公众号名称列表
    - target_date: 目标日期（格式 YYYY-MM-DD）

    Args:
        config_path (str): 配置文件路径

    Returns:
        dict: 工作流执行结果
    """
    print("\n" + "=" * 80)
    print("开始测试 APIArticleCollector + DailyGenerator 完整工作流")
    print("=" * 80)

    # 加载配置文件
    yaml = YAML()
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.load(f)

    # 读取配置参数
    target_date = config.get("target_date")
    account_names = config.get("account_names", [])

    if not target_date:
        raise ValueError("配置文件中缺少 target_date 参数")
    if not account_names:
        raise ValueError("配置文件中缺少 account_names 参数")

    print(f"\n配置文件: {config_path}")
    print(f"目标日期: {target_date}")
    print(f"公众号列表: {', '.join(account_names)}")
    print(f"公众号数量: {len(account_names)} 个")

    result = {
        'success': False,
        'stage': '',
        'article_file': '',
        'daily_file': '',
        'error': None
    }

    try:
        # ==================== 阶段1：采集文章链接 ====================
        print("\n" + "=" * 80)
        print("阶段 1/2: 采集公众号文章链接")
        print("=" * 80)

        result['stage'] = 'collect'

        # 创建采集器（从配置文件读取所有参数）
        collector = APIArticleCollector(config=config_path)
        logger.info("APIArticleCollector 初始化成功")

        # 执行采集（使用配置文件中的参数）
        article_file = collector.run()

        if not article_file:
            raise Exception("未采集到任何文章")

        result['article_file'] = article_file

        print(f"\n✅ 文章采集完成")
        print(f"   输出文件: {article_file}")

        # 显示采集到的文章数量
        with open(article_file, "r", encoding="utf-8") as f:
            content = f.read()
            article_count = content.count("http")
        print(f"   文章数量: {article_count} 篇")

        # ==================== 阶段2：生成日报 ====================
        print("\n" + "=" * 80)
        print("阶段 2/2: 生成每日日报")
        print("=" * 80)

        result['stage'] = 'generate'

        # 创建日报生成器
        generator = DailyGenerator(config=config_path)
        logger.info("DailyGenerator 初始化成功")

        # 解析目标日期
        target_datetime = datetime.strptime(target_date, "%Y-%m-%d")

        # 执行生成
        daily_file = await generator.run(
            markdown_file=article_file,
            date=target_datetime
        )

        if not daily_file:
            raise Exception("日报生成失败")

        result['daily_file'] = daily_file

        print(f"\n✅ 日报生成完成")
        print(f"   输出文件: {daily_file}")

        # 显示文件大小
        file_size = Path(daily_file).stat().st_size / 1024  # KB
        print(f"   文件大小: {file_size:.2f} KB")

        # ==================== 完成 ====================
        result['success'] = True
        result['stage'] = 'complete'

        print("\n" + "=" * 80)
        print("🎉 完整工作流执行成功！")
        print("=" * 80)
        print(f"\n📁 输出文件:")
        print(f"   1. 文章链接: {article_file}")
        print(f"   2. 日报HTML: {daily_file}")
        print(f"\n💡 提示:")
        print(f"   - 可以用浏览器打开 {daily_file} 查看效果")
        print(f"   - 可以复制 HTML 内容到微信公众号后台发布")

    except ArticleError as e:
        result['error'] = f"API 错误: {e}"
        logger.exception(f"阶段 [{result['stage']}] 失败: API 错误")
        print(f"\n❌ 阶段 [{result['stage']}] 失败: {e}")

    except Exception as e:
        result['error'] = str(e)
        logger.exception(f"阶段 [{result['stage']}] 失败")
        print(f"\n❌ 阶段 [{result['stage']}] 失败: {e}")

    return result


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("APIArticleCollector + DailyGenerator 完整工作流测试")
    print("=" * 80)
    print("\n本测试将从 configs/config.yaml 读取所有配置")
    print("请确保已正确配置以下参数：")
    print("  - cookie: 微信公众平台 cookie")
    print("  - token: 微信公众平台 token")
    print("  - account_names: 公众号名称列表")
    print("  - target_date: 目标日期（格式 YYYY-MM-DD）")

    try:
        # 执行测试
        result = asyncio.run(test_complete_workflow())

        # 根据结果退出
        if result['success']:
            print("\n" + "=" * 80)
            print("✅ 测试完全成功")
            print("=" * 80)
            sys.exit(0)
        else:
            print("\n" + "=" * 80)
            print("❌ 测试失败")
            if result['error']:
                print(f"错误信息: {result['error']}")
            print("=" * 80)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ 测试执行失败: {e}")
        print("=" * 80)
        logger.exception("详细错误信息:")
        sys.exit(1)


if __name__ == "__main__":
    main()
