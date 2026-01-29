# 通过这个主函数实现每日AI公众号速览

from wechat_ai_daily.workflows import DailyGenerator, RPAArticleCollector, APIArticleCollector, DailyPublisher
from datetime import datetime, date
import logging
import asyncio
import argparse
from pathlib import Path
from ruamel.yaml import YAML

# 加载 .env 环境变量（必须在其他模块导入前调用）
from wechat_ai_daily.utils.env_loader import load_env
load_env()


# 确保 logs 目录存在
Path("logs").mkdir(exist_ok=True)

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler("logs/main.log", encoding="utf-8")  # 输出到文件
    ],
    force=True  # 强制重新配置，覆盖之前的配置
)

# 确保根日志记录器的级别是 INFO
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 同时确保所有 handler 的级别也是 INFO
for handler in logger.handlers:
    handler.setLevel(logging.INFO)


def print_legal_notice():
    """打印法律声明（使用 logging.warning 层级）"""
    logging.warning("=" * 70)
    logging.warning("⚠️  法律声明")
    logging.warning("=" * 70)
    logging.warning("本工具仅供个人学习和研究使用，请勿用于商业目的。")
    logging.warning("")
    logging.warning("【风险提示】")
    logging.warning("• API 模式使用了微信公众平台的非公开后台接口，可能违反平台服务协议")
    logging.warning("• RPA 模式的 GUI 自动化操作可能违反微信用户协议")
    logging.warning("• 使用本工具产生的一切后果由使用者自行承担")
    logging.warning("")
    logging.warning("继续使用即表示您已阅读并同意遵守相关声明。")
    logging.warning("详细条款请查看 LICENSE 文件和 README.md 中的法律声明部分。")
    logging.warning("=" * 70)


def parse_target_date(config_path: str = "configs/config.yaml") -> datetime:
    """解析配置文件中的目标日期（RPA 模式专用）

    Args:
        config_path: 配置文件路径

    Returns:
        datetime: 解析后的目标日期
    """
    try:
        yaml = YAML()
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.load(f) or {}
    except Exception as e:
        logging.warning(f"读取配置文件失败: {e}，使用当天日期")
        return datetime.now()

    target_date_str = config.get("target_date")

    # null 表示当天
    if target_date_str is None:
        return datetime.now()

    # 如果 YAML 已经解析为 date/datetime 对象，直接转换
    if isinstance(target_date_str, datetime):
        return target_date_str
    if isinstance(target_date_str, date):
        return datetime.combine(target_date_str, datetime.min.time())

    # 尝试解析具体日期字符串（格式：YYYY-MM-DD）
    try:
        return datetime.strptime(target_date_str, "%Y-%m-%d")
    except ValueError:
        logging.warning(f"无法解析日期 '{target_date_str}'，使用当天日期")
        return datetime.now()


def parse_date_range(config_path: str = "configs/config.yaml") -> tuple[datetime, datetime]:
    """解析配置文件中的时间范围（API 模式专用）

    Args:
        config_path: 配置文件路径

    Returns:
        tuple[datetime, datetime]: (开始时间, 结束时间) 元组
    """
    try:
        yaml = YAML()
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.load(f) or {}
    except Exception as e:
        logging.warning(f"读取配置文件失败: {e}，使用当天时间范围")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return today, today.replace(hour=23, minute=59)

    start_date_str = config.get("start_date")
    end_date_str = config.get("end_date")

    # 解析开始时间
    start_date = _parse_datetime_str(start_date_str, "start_date")
    if start_date is None:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # 解析结束时间
    end_date = _parse_datetime_str(end_date_str, "end_date")
    if end_date is None:
        end_date = datetime.now().replace(hour=23, minute=59, second=0, microsecond=0)

    # 验证时间范围
    if start_date > end_date:
        logging.warning(f"开始时间 {start_date} 晚于结束时间 {end_date}，自动交换")
        start_date, end_date = end_date, start_date

    return start_date, end_date


def _parse_datetime_str(date_str, field_name: str) -> datetime | None:
    """解析日期时间字符串

    支持两种格式：
    - "YYYY-MM-DD HH:mm" - 精确到分钟
    - "YYYY-MM-DD" - 精确到天（自动补充时间）

    Args:
        date_str: 日期时间字符串或 datetime/date 对象
        field_name: 字段名称（用于日志）

    Returns:
        datetime | None: 解析后的 datetime 对象，解析失败返回 None
    """
    if date_str is None:
        return None

    # 如果 YAML 已经解析为 datetime 对象
    if isinstance(date_str, datetime):
        return date_str

    # 如果 YAML 已经解析为 date 对象
    if isinstance(date_str, date):
        return datetime.combine(date_str, datetime.min.time())

    # 尝试解析字符串
    if isinstance(date_str, str):
        # 尝试格式：YYYY-MM-DD HH:mm
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            pass

        # 尝试格式：YYYY-MM-DD
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            pass

        logging.warning(
            f"无法解析 {field_name} '{date_str}'，格式应为 'YYYY-MM-DD HH:mm' 或 'YYYY-MM-DD'")

    return None


async def main():
    """主函数：支持 RPA/API 双模式采集，支持完整的采集→生成→发布工作流"""

    # 显示法律声明
    print_legal_notice()

    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="微信公众号文章智能发布工具 - 支持 RPA/API 双模式采集，支持完整的采集→生成→发布工作流",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  # 一键全流程（RPA 模式）
  python main.py --mode rpa --workflow full
  
  # 一键全流程（API 模式，推荐）
  python main.py --mode api --workflow full
  
  # 仅采集文章（RPA 模式）
  python main.py --mode rpa --workflow collect
  
  # 仅采集文章（API 模式）
  python main.py --mode api --workflow collect
  
    # 仅生成公众号文章内容（需要先执行采集）
  python main.py --workflow generate --markdown-file output/articles_20260126.md
  
  # 仅发布草稿（需要先执行生成）
  python main.py --workflow publish --html-file output/daily_rich_text_20260126.html
        """
    )

    parser.add_argument(
        "--mode",
        choices=["rpa", "api"],
        default="api",
        help="采集模式：rpa（GUI自动化+VLM识别）或 api（微信公众平台后台接口，推荐）。默认: api"
    )

    parser.add_argument(
        "--workflow",
        choices=["collect", "generate", "publish", "full"],
        default="full",
        help="工作流类型：collect（仅采集）、generate（仅生成）、publish（仅发布）、full（完整流程）。默认: full"
    )

    parser.add_argument(
        "--markdown-file",
        type=str,
        help="指定已有的文章列表 Markdown 文件（用于 generate 或 publish 工作流）。如不指定，将使用采集步骤生成的文件"
    )

    parser.add_argument(
        "--html-file",
        type=str,
        help="指定已有的公众号文章内容 HTML 文件（用于 publish 工作流）。如不指定，将使用生成步骤生成的文件"
    )

    parser.add_argument(
        "--start-date",
        type=str,
        help="开始时间（API 模式专用），格式 'YYYY-MM-DD HH:mm' 或 'YYYY-MM-DD'。如不指定，从配置文件读取"
    )

    parser.add_argument(
        "--end-date",
        type=str,
        help="结束时间（API 模式专用），格式 'YYYY-MM-DD HH:mm' 或 'YYYY-MM-DD'。如不指定，从配置文件读取"
    )

    args = parser.parse_args()

    # 根据模式解析日期/时间范围
    if args.mode == "api":
        # API 模式：使用时间范围（精确到分钟）
        # 命令行参数优先于配置文件
        if args.start_date:
            start_date = _parse_datetime_str(args.start_date, "start-date")
            if start_date is None:
                logging.error(f"无法解析 --start-date 参数: {args.start_date}")
                return
        else:
            start_date = None

        if args.end_date:
            end_date = _parse_datetime_str(args.end_date, "end-date")
            if end_date is None:
                logging.error(f"无法解析 --end-date 参数: {args.end_date}")
                return
        else:
            end_date = None

        # 如果命令行未指定，从配置文件读取
        if start_date is None or end_date is None:
            config_start, config_end = parse_date_range()
            if start_date is None:
                start_date = config_start
            if end_date is None:
                end_date = config_end

        # 用于后续步骤的目标日期（取开始日期的日期部分）
        target_date = start_date

        logging.info(
            f"时间范围: {start_date.strftime('%Y-%m-%d %H:%M')} ~ {end_date.strftime('%Y-%m-%d %H:%M')}")
    else:
        # RPA 模式：使用目标日期（精确到天）
        target_date = parse_target_date()
        start_date = None
        end_date = None
        logging.info(f"目标日期: {target_date.strftime('%Y-%m-%d')}")

    logging.info(f"采集模式: {args.mode.upper()}")
    logging.info(f"工作流类型: {args.workflow.upper()}")

    # 初始化变量
    markdown_file = args.markdown_file
    html_file = args.html_file

    # 步骤1：采集公众号文章
    if args.workflow in ["collect", "full"]:
        logging.info("=" * 60)
        logging.info("步骤 1/3: 开始采集公众号文章...")
        logging.info("=" * 60)

        if args.mode == "rpa":
            # RPA 模式：使用 RPAArticleCollector（异步方法）
            logging.info("使用 RPA 模式采集（GUI 自动化 + VLM 图像识别）")
            collector = RPAArticleCollector(config="configs/config.yaml")
            markdown_file = await collector.run()
        else:  # api
            # API 模式：使用 APIArticleCollector（同步方法）
            logging.info("使用 API 模式采集（微信公众平台后台接口）")
            collector = APIArticleCollector(config="configs/config.yaml")
            markdown_file = collector.run()

        logging.info(f"✓ 文章采集完成，输出文件: {markdown_file}")

    # 步骤2：生成公众号文章内容
    if args.workflow in ["generate", "full"]:
        logging.info("=" * 60)
        logging.info("步骤 2/3: 开始生成公众号文章内容...")
        logging.info("=" * 60)

        # 检查是否有 markdown 文件
        if not markdown_file:
            # 如果没有指定，尝试自动查找当天的文件
            date_str = target_date.strftime("%Y%m%d")
            auto_markdown = f"output/articles_{date_str}.md"
            if Path(auto_markdown).exists():
                markdown_file = auto_markdown
                logging.info(f"自动找到文章列表文件: {markdown_file}")
            else:
                logging.error(
                    "错误: 未找到文章列表文件。请先执行采集步骤，或使用 --markdown-file 指定文件路径")
                return

        # 检查文件是否存在
        if not Path(markdown_file).exists():
            logging.error(f"错误: 文章列表文件不存在: {markdown_file}")
            return

        daily_generator = DailyGenerator(config="configs/config.yaml")
        # API 模式按“时间范围”过滤，RPA 模式按“目标日期”过滤
        if args.mode == "api":
            html_file = await daily_generator.run(
                markdown_file=markdown_file,
                date=target_date,
                start_time=start_date,
                end_time=end_date
            )
        else:
            html_file = await daily_generator.run(
                markdown_file=markdown_file,
                date=target_date
            )
        logging.info(f"✓ 公众号文章内容生成完成，输出文件: {html_file}")

    # 步骤3：发布草稿
    if args.workflow in ["publish", "full"]:
        logging.info("=" * 60)
        logging.info("步骤 3/3: 开始发布公众号草稿...")
        logging.info("=" * 60)

        # 检查是否有 html 文件
        if not html_file:
            # 如果没有指定，尝试自动查找当天的文件
            date_str = target_date.strftime("%Y%m%d")
            auto_html = f"output/daily_rich_text_{date_str}.html"
            if Path(auto_html).exists():
                html_file = auto_html
                logging.info(f"自动找到公众号文章内容 HTML 文件: {html_file}")
            else:
                logging.error(
                    "错误: 未找到公众号文章内容 HTML 文件。请先执行生成步骤，或使用 --html-file 指定文件路径")
                return

        # 检查文件是否存在
        if not Path(html_file).exists():
            logging.error(f"错误: 公众号文章内容 HTML 文件不存在: {html_file}")
            return

        publisher = DailyPublisher(config="configs/config.yaml")

        # 生成标题（格式：AI日报 - YYYY-MM-DD）
        title = f"AI日报 - {target_date.strftime('%Y-%m-%d')}"
        logging.info(f"使用标题: {title}")

        # DailyPublisher.run() 是同步方法，参数为 html_path, title, digest
        draft_media_id = publisher.run(
            html_path=html_file, title=title, digest="")
        logging.info(f"✓ 草稿发布完成！media_id: {draft_media_id}")
        logging.info("请前往微信公众平台查看草稿")

    logging.info("=" * 60)
    logging.info("🎉 所有任务执行完成！")
    logging.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
