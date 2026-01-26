#!/usr/bin/env python3
"""环境变量诊断工具

用于检查环境变量配置情况，帮助排查配置问题。

运行方式：
    uv run python tests/diagnose_env.py
"""

import sys
import logging
from pathlib import Path

# 配置日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from wechat_ai_daily.utils.env_loader import load_env, log_env_diagnostic


if __name__ == "__main__":
    logger.info("\n🔍 正在检查环境变量配置...\n")
    
    # 加载环境变量
    result = load_env()
    
    logger.info(f"\n📂 .env 文件加载: {'✅ 成功' if result['env_file_loaded'] else '❌ 未找到'}")
    if result['env_file_path']:
        logger.info(f"📍 文件路径: {result['env_file_path']}")
    
    # 输出诊断信息
    log_env_diagnostic()
    
    # 提供建议
    logger.info("💡 配置建议:")
    logger.info("  1. 如果要使用 .env 文件，请复制 .env.example 为 .env")
    logger.info("     命令: cp .env.example .env")
    logger.info("  2. 编辑 .env 文件，填写真实凭证")
    logger.info("  3. 或者在 ~/.zshrc 中设置全局环境变量")
    logger.info("  4. 配置优先级：系统环境变量 > .env 文件 > config.yaml\n")

