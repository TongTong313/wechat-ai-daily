# 通过这个主函数实现每日AI公众号速览

from datetime import datetime, timedelta
import logging
import asyncio
from ruamel.yaml import YAML

# 加载 .env 环境变量（必须在其他模块导入前调用）
from wechat_ai_daily.utils.env_loader import load_env
load_env()

from wechat_ai_daily.workflows import DailyGenerator, ArticleCollector

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
    # 解析目标日期
    target_date = parse_target_date()
    logging.info(f"目标日期: {target_date.strftime('%Y-%m-%d')}")

    # 1. 采集公众号文章
    collector = ArticleCollector(config="configs/config.yaml")
    output_file = await collector.run(target_date=target_date)

    # 2. 生成每日日报
    daily_generator = DailyGenerator(config="configs/config.yaml")
    await daily_generator.run(markdown_file=output_file, date=target_date)


if __name__ == "__main__":
    asyncio.run(main())
