# -*- coding: utf-8 -*-
"""
API 模式全流程测试（采集 → 生成 → 发布）

本测试验证 API 模式下从文章采集、公众号文章内容生成到草稿发布的完整工作流。

运行方式：
    uv run python tests/test_api_full_workflow.py

    # 指定标题
    uv run python tests/test_api_full_workflow.py --title "AI日报测试"

    # 跳过发布阶段（仅测试采集和生成）
    uv run python tests/test_api_full_workflow.py --skip-publish

前置条件：
    1. API 采集凭证（两种方式二选一）：
       - 推荐：设置环境变量 WECHAT_API_TOKEN 和 WECHAT_API_COOKIE（在 .env 文件中）
       - 或：在 config.yaml 的 api_config 中配置 token 和 cookie
    2. 已在 config.yaml 中配置：
       - api_config.account_names: 公众号名称列表
       - target_date: 目标日期（格式 YYYY-MM-DD）
    3. 已配置 DASHSCOPE_API_KEY 环境变量（用于 LLM 生成摘要）
    4. 发布凭证（如需发布）：
       - 推荐：设置环境变量 WECHAT_APPID 和 WECHAT_APPSECRET
       - 或：在 config.yaml 的 publish_config 中配置 appid 和 appsecret
"""
import sys
import logging
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径（必须在其他模块导入前执行）
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 加载 .env 环境变量（必须在其他模块导入前调用）
from wechat_ai_daily.utils.env_loader import load_env
load_env()

# 现在可以安全导入其他模块
from ruamel.yaml import YAML
from wechat_ai_daily.utils.wechat import ArticleError
from wechat_ai_daily.workflows.daily_publish import DailyPublisher
from wechat_ai_daily.workflows.daily_generate import DailyGenerator
from wechat_ai_daily.workflows.api_article_collector import APIArticleCollector


def setup_logging() -> logging.Logger:
    """配置日志系统

    统一配置根日志器，确保所有模块的日志都能正确输出。

    Returns:
        logging.Logger: 测试脚本的日志器
    """
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 配置根日志器，这样所有子模块的日志都会被捕获
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 清除已有的处理器，避免重复
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # 文件处理器
    file_handler = logging.FileHandler(
        log_dir / "test_api_full_workflow.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)

    return logging.getLogger(__name__)


# 初始化日志
logger = setup_logging()


def log_banner(text: str, char: str = "=", width: int = 70) -> None:
    """打印横幅到日志

    Args:
        text: 横幅文本
        char: 横幅字符
        width: 横幅宽度
    """
    logger.info(char * width)
    logger.info(text)
    logger.info(char * width)


async def run_full_workflow(
    config_path: str = "configs/config.yaml",
    title: str = None,
    skip_publish: bool = False
) -> dict:
    """
    执行 API 模式全流程测试

    Args:
        config_path: 配置文件路径
        title: 草稿标题（可选，为空则自动生成）
        skip_publish: 是否跳过发布阶段

    Returns:
        dict: 工作流执行结果
    """
    log_banner("API 模式全流程测试（采集 → 生成 → 发布）")

    # 加载配置文件
    yaml = YAML()
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.load(f)

    # 读取配置参数
    api_config = config.get("api_config", {})
    target_date = config.get("target_date")
    account_names = api_config.get("account_names", [])

    # 验证必要配置
    if not target_date:
        raise ValueError("配置文件中缺少 target_date 参数")
    if not account_names:
        raise ValueError("配置文件中缺少 api_config.account_names 参数")

    logger.info(f"配置文件: {config_path}")
    logger.info(f"目标日期: {target_date}")
    logger.info(f"公众号列表: {', '.join(account_names)}")
    logger.info(f"公众号数量: {len(account_names)} 个")
    logger.info(f"跳过发布: {'是' if skip_publish else '否'}")

    # 初始化结果
    result = {
        'success': False,
        'stage': '',
        'article_file': '',
        'daily_file': '',
        'draft_media_id': '',
        'error': None
    }

    start_time = datetime.now()

    try:
        # ==================== 阶段 1/3: 采集文章链接 ====================
        log_banner("阶段 1/3: 采集公众号文章链接", "-")
        result['stage'] = 'collect'

        logger.info("初始化 APIArticleCollector...")
        collector = APIArticleCollector(config=config_path)
        logger.info("APIArticleCollector 初始化成功")

        logger.info("开始采集文章...")
        article_file = collector.run()

        if not article_file:
            raise Exception("未采集到任何文章")

        result['article_file'] = article_file

        # 统计采集到的文章数量
        with open(article_file, "r", encoding="utf-8") as f:
            content = f.read()
            article_count = content.count("http")

        logger.info("文章采集完成")
        logger.info(f"输出文件: {article_file}")
        logger.info(f"文章数量: {article_count} 篇")

        # ==================== 阶段 2/3: 生成公众号文章内容 ====================
        log_banner("阶段 2/3: 生成公众号文章内容", "-")
        result['stage'] = 'generate'

        logger.info("初始化 DailyGenerator...")
        generator = DailyGenerator(config=config_path)
        logger.info("DailyGenerator 初始化成功")

        # 解析目标日期（target_date 可能是 str 或 datetime.date 类型）
        if isinstance(target_date, str):
            target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
        else:
            # 如果是 date 对象，转换为 datetime
            target_datetime = datetime.combine(target_date, datetime.min.time())

        logger.info("开始生成公众号文章内容（此步骤会调用 LLM，可能需要几分钟）...")
        daily_file = await generator.run(
            markdown_file=article_file,
            date=target_datetime
        )

        if not daily_file:
            raise Exception("公众号文章内容生成失败")

        result['daily_file'] = daily_file

        # 显示文件大小
        file_size = Path(daily_file).stat().st_size / 1024

        logger.info("公众号文章内容生成完成")
        logger.info(f"输出文件: {daily_file}")
        logger.info(f"文件大小: {file_size:.2f} KB")

        # ==================== 阶段 3/3: 发布草稿 ====================
        if skip_publish:
            log_banner("阶段 3/3: 发布草稿（已跳过）", "-")
            logger.warning("用户选择跳过发布阶段")
            result['stage'] = 'complete'
            result['success'] = True
        else:
            log_banner("阶段 3/3: 发布到公众号草稿", "-")
            result['stage'] = 'publish'

            logger.info("初始化 DailyPublisher...")
            publisher = DailyPublisher(config=config_path)
            logger.info("DailyPublisher 初始化成功")

            # 确定标题
            if not title:
                title = f"AI日报 - {target_date}"

            logger.info(f"草稿标题: {title}")
            logger.info("开始发布草稿...")

            draft_media_id = publisher.run(
                html_path=daily_file,
                title=title,
                digest=""
            )

            if not draft_media_id:
                raise Exception("草稿发布失败")

            result['draft_media_id'] = draft_media_id

            logger.info("草稿发布完成")
            logger.info(f"草稿 media_id: {draft_media_id}")

            result['stage'] = 'complete'
            result['success'] = True

    except ArticleError as e:
        result['error'] = f"API 错误: {e}"
        logger.exception(f"阶段 [{result['stage']}] 失败: API 错误")

    except Exception as e:
        result['error'] = str(e)
        logger.exception(f"阶段 [{result['stage']}] 失败")

    # 计算总耗时
    elapsed = (datetime.now() - start_time).total_seconds()
    result['elapsed'] = elapsed

    return result


def log_report(result: dict) -> None:
    """打印测试报告到日志"""
    log_banner("测试报告")

    if result['success']:
        logger.info("全流程执行成功")
    else:
        logger.error(f"执行失败，停止于阶段: {result['stage']}")
        if result['error']:
            logger.error(f"错误信息: {result['error']}")

    # 显示执行时间
    elapsed = result.get('elapsed', 0)
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    logger.info(f"总耗时: {minutes} 分 {seconds} 秒")

    # 显示输出文件
    logger.info("输出文件:")
    if result['article_file']:
        logger.info(f"  1. 文章链接: {result['article_file']}")
    if result['daily_file']:
        logger.info(f"  2. 公众号文章内容HTML: {result['daily_file']}")
    if result['draft_media_id']:
        logger.info(f"  3. 草稿ID:   {result['draft_media_id']}")

    # 提示信息
    if result['success']:
        logger.info("提示:")
        if result['daily_file']:
            logger.info(f"  - 可以用浏览器打开 {result['daily_file']} 查看效果")
        if result['draft_media_id']:
            logger.info(f"  - 请前往微信公众号后台查看并发布草稿")


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="API 模式全流程测试（采集 → 生成 → 发布）"
    )
    parser.add_argument(
        "--title",
        type=str,
        default="",
        help="草稿标题（可选，默认自动生成）"
    )
    parser.add_argument(
        "--skip-publish",
        action="store_true",
        help="跳过发布阶段（仅测试采集和生成）"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/config.yaml",
        help="配置文件路径（默认: configs/config.yaml）"
    )
    args = parser.parse_args()

    log_banner("API 模式全流程测试")
    logger.info("本测试将执行以下步骤：")
    logger.info("  1. 采集公众号文章链接（APIArticleCollector）")
    logger.info("  2. 生成公众号文章内容（DailyGenerator）")
    if not args.skip_publish:
        logger.info("  3. 发布到公众号草稿（DailyPublisher）")
    else:
        logger.info("  3. 发布到公众号草稿（已跳过）")

    logger.info("请确保已正确配置以下参数：")
    logger.info("  采集凭证（两种方式二选一）：")
    logger.info("    - 推荐：环境变量 WECHAT_API_TOKEN 和 WECHAT_API_COOKIE")
    logger.info("    - 或：config.yaml 的 api_config.token 和 api_config.cookie")
    logger.info("  其他配置（config.yaml）：")
    logger.info("    - api_config.account_names: 公众号名称列表")
    logger.info("    - target_date: 目标日期（格式 YYYY-MM-DD）")
    if not args.skip_publish:
        logger.info("  发布凭证（两种方式二选一）：")
        logger.info("    - 推荐：环境变量 WECHAT_APPID 和 WECHAT_APPSECRET")
        logger.info("    - 或：config.yaml 的 publish_config.appid 和 publish_config.appsecret")

    try:
        # 执行测试
        result = asyncio.run(run_full_workflow(
            config_path=args.config,
            title=args.title if args.title else None,
            skip_publish=args.skip_publish
        ))

        # 打印报告
        log_report(result)

        # 根据结果退出
        if result['success']:
            log_banner("测试完全成功", "=")
            sys.exit(0)
        else:
            log_banner("测试失败", "=")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("测试被用户中断")
        sys.exit(1)

    except Exception as e:
        log_banner("测试执行失败")
        logger.error(f"错误: {e}")
        logger.exception("详细错误信息:")
        sys.exit(1)


if __name__ == "__main__":
    main()
