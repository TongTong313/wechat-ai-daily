# -*- coding: utf-8 -*-
"""
测试配置面板是否能正确读取系统环境变量
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 加载环境变量
from wechat_ai_daily.utils.env_loader import load_env
load_env()

print("=" * 70)
print("测试配置面板读取系统环境变量")
print("=" * 70)

# 1. 测试系统环境变量
print("\n1️⃣ 测试 os.environ.get()")
api_key_from_os = os.environ.get("DASHSCOPE_API_KEY")
if api_key_from_os:
    print(f"✅ 系统环境变量: {api_key_from_os[:20]}...")
else:
    print("❌ 系统环境变量: 未找到")

# 2. 测试 ConfigManager
print("\n2️⃣ 测试 ConfigManager.get_api_key_with_source()")
from apps.desktop.utils.config_manager import ConfigManager

config_manager = ConfigManager(project_root)
api_key, source = config_manager.get_api_key_with_source()

if api_key:
    print(f"✅ API Key: {api_key[:20]}... (来源: {source})")
else:
    print(f"❌ API Key: None (来源: {source})")

# 3. 测试 has_env_api_key
print("\n3️⃣ 测试 ConfigManager.has_env_api_key()")
has_env = config_manager.has_env_api_key()
print(f"{'✅' if has_env else '❌'} has_env_api_key(): {has_env}")

# 4. 测试 get_env_api_key
print("\n4️⃣ 测试 ConfigManager.get_env_api_key()")
env_key = config_manager.get_env_api_key()
if env_key:
    print(f"✅ get_env_api_key(): {env_key[:20]}...")
else:
    print("❌ get_env_api_key(): None")

# 5. 检查 config.yaml 和 .env 文件中的值
print("\n5️⃣ 检查配置文件")
config_key = config_manager.get_config_api_key()
print(f"config.yaml 中的值: {config_key if config_key else 'None'}")

from apps.desktop.utils.env_file_manager import EnvFileManager
env_manager = EnvFileManager(project_root)
env_file_key = env_manager.get("DASHSCOPE_API_KEY")
if env_file_key:
    print(f".env 文件中的值: {env_file_key[:20]}...")
else:
    print(".env 文件中的值: None")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
