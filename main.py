# 通过这个主函数实现每日AI公众号速览

from datetime import datetime, timedelta
import logging
import asyncio
import argparse
from pathlib import Path
from ruamel.yaml import YAML

# 加载 .env 环境变量（必须在其他模块导入前调用）
from wechat_ai_daily.utils.env_loader import load_env
load_env()

from wechat_ai_daily.workflows import DailyGenerator, RPAArticleCollector, APIArticleCollector, DailyPublisher

# 确保 logs 目录存在
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler("logs/main.log", encoding="utf-8")  # 输出到文件
    ]
)


def parse_target_date(config_path: str = "configs/config.yaml") -> datetime:
    """解析配置文件中的目标日期

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

    # null 或 "today" 表示当天
    if target_date_str is None or target_date_str == "today":
        return datetime.now()

    # "yesterday" 表示昨天
    if target_date_str == "yesterday":
        return datetime.now() - timedelta(days=1)

    # 尝试解析具体日期字符串（格式：YYYY-MM-DD）
    try:
        return datetime.strptime(target_date_str, "%Y-%m-%d")
    except ValueError:
        logging.warning(f"无法解析日期 '{target_date_str}'，使用当天日期")
        return datetime.now()


async def main():
    """主函数：支持 RPA/API 双模式采集，支持完整的采集→生成→发布工作流"""
    
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
  
  # 仅生成日报（需要先执行采集）
  python main.py --workflow generate --markdown-file output/articles_20260126.md
  
  # 仅发布草稿（需要先执行生成）
  python main.py --workflow publish --html-file output/daily_rich_text_20260126.html
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["rpa", "api"],
        default="rpa",
        help="采集模式：rpa（GUI自动化+VLM识别）或 api（微信公众平台后台接口，推荐）。默认: rpa"
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
        help="指定已有的日报 HTML 文件（用于 publish 工作流）。如不指定，将使用生成步骤生成的文件"
    )
    
    args = parser.parse_args()
    
    # 解析目标日期
    target_date = parse_target_date()
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
            logging.info("使用 RPA 模式采集（GUI 自动化 + VLM 图像识别）")
            collector = RPAArticleCollector(config="configs/config.yaml")
        else:  # api
            logging.info("使用 API 模式采集（微信公众平台后台接口）")
            collector = APIArticleCollector(config="configs/config.yaml")
        
        markdown_file = await collector.run(target_date=target_date)
        logging.info(f"✓ 文章采集完成，输出文件: {markdown_file}")
    
    # 步骤2：生成每日日报
    if args.workflow in ["generate", "full"]:
        logging.info("=" * 60)
        logging.info("步骤 2/3: 开始生成每日日报...")
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
                logging.error("错误: 未找到文章列表文件。请先执行采集步骤，或使用 --markdown-file 指定文件路径")
                return
        
        # 检查文件是否存在
        if not Path(markdown_file).exists():
            logging.error(f"错误: 文章列表文件不存在: {markdown_file}")
            return
        
        daily_generator = DailyGenerator(config="configs/config.yaml")
        html_file = await daily_generator.run(markdown_file=markdown_file, date=target_date)
        logging.info(f"✓ 日报生成完成，输出文件: {html_file}")
    
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
                logging.info(f"自动找到日报 HTML 文件: {html_file}")
            else:
                logging.error("错误: 未找到日报 HTML 文件。请先执行生成步骤，或使用 --html-file 指定文件路径")
                return
        
        # 检查文件是否存在
        if not Path(html_file).exists():
            logging.error(f"错误: 日报 HTML 文件不存在: {html_file}")
            return
        
        publisher = DailyPublisher(config="configs/config.yaml")
        await publisher.run(html_file=html_file, date=target_date)
        logging.info("✓ 草稿发布完成！请前往微信公众平台查看草稿")
    
    logging.info("=" * 60)
    logging.info("🎉 所有任务执行完成！")
    logging.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
