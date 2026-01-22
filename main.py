# 通过这个主函数实现每日AI公众号速览

from wechat_ai_daily.workflows import DailyGenerateWorkflow, OfficialAccountArticleCollector


def main():
    daily_generate_workflow = DailyGenerateWorkflow()
    daily_generate_workflow.run()


if __name__ == "__main__":
    main()
