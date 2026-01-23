# 通过这个主函数实现每日AI公众号速览

from datetime import datetime
import logging
import asyncio

from wechat_ai_daily.workflows import DailyGenerator, OfficialAccountArticleCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler("logs/main.log", encoding="utf-8")  # 输出到文件
    ]
)


async def main():
    # 1. 采集公众号文章
    collector = OfficialAccountArticleCollector(config="configs/config.yaml")
    output_file = await collector.run(first_date=datetime(2026, 1, 23))

    # 2. 生成每日日报
    daily_generator = DailyGenerator()
    await daily_generator.run(markdown_file=output_file)


if __name__ == "__main__":
    asyncio.run(main())
