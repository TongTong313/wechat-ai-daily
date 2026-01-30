# -*- coding: utf-8 -*-
"""
测试配置管理器的隐私保护功能和配置优先级

验证配置优先级：config.yaml > .env 文件 > 系统环境变量
确保敏感数据不会意外泄露到配置文件中。
"""

import os
import tempfile
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.desktop.utils.config_manager import ConfigManager
from apps.desktop.utils.env_file_manager import EnvFileManager


def test_priority_config_over_env_file():
    """测试：config.yaml 优先级高于 .env 文件"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        
        # 创建配置文件，API Key 有值
        config_content = """target_date: null
article_urls: []
model_config:
  LLM:
    model: qwen-plus
    api_key: sk-config-key
  VLM:
    model: qwen3-vl-plus
    api_key: sk-config-key
"""
        config_path.write_text(config_content, encoding='utf-8')
        
        # 创建 .env 文件
        env_manager = EnvFileManager(Path(tmpdir))
        env_manager.create({'DASHSCOPE_API_KEY': 'sk-env-key'})
        
        # 加载环境变量
        from dotenv import load_dotenv
        load_dotenv(env_manager.get_file_path(), override=True)
        
        try:
            config_manager = ConfigManager(str(config_path))
            
            # 验证读取到的是 config.yaml 的值
            api_key, source = config_manager.get_api_key_with_source()
            assert api_key == 'sk-config-key', f"Expected 'sk-config-key', got {api_key}"
            assert source == 'config', f"Expected 'config', got {source}"
            
            print("✓ 测试通过：config.yaml 优先级高于 .env 文件")
            
        finally:
            if 'DASHSCOPE_API_KEY' in os.environ:
                del os.environ['DASHSCOPE_API_KEY']


def test_priority_env_file_over_system():
    """测试：.env 文件优先级高于系统环境变量"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        
        # 创建配置文件，不包含 model_config（这样才会fallback到环境变量）
        config_content = """target_date: null
article_urls: []
"""
        config_path.write_text(config_content, encoding='utf-8')
        
        # 设置系统环境变量
        os.environ['DASHSCOPE_API_KEY'] = 'sk-system-key'
        
        # 创建 .env 文件到临时目录
        env_file = Path(tmpdir) / ".env"
        env_file.write_text('DASHSCOPE_API_KEY="sk-env-file-key"', encoding='utf-8')
        
        # 加载环境变量（.env 会覆盖系统环境变量）
        from dotenv import load_dotenv
        load_dotenv(env_file, override=True)
        
        # 验证环境变量已更新
        assert os.environ.get('DASHSCOPE_API_KEY') == 'sk-env-file-key', \
            f"Environment variable should be updated to 'sk-env-file-key'"
        
        try:
            config_manager = ConfigManager(str(config_path))
            
            # 由于 config 中没有 api_key 键，应该读取环境变量
            # 注意：ConfigManager 会使用自己的 project_root，但环境变量已经通过 load_dotenv 加载
            api_key = config_manager.get_api_key()
            assert api_key == 'sk-env-file-key', f"Expected 'sk-env-file-key', got {api_key}"
            
            print("✓ 测试通过：.env 文件优先级高于系统环境变量")
            
        finally:
            if 'DASHSCOPE_API_KEY' in os.environ:
                del os.environ['DASHSCOPE_API_KEY']


def test_save_to_env_file():
    """测试：保存到 .env 文件，不泄露到 config.yaml"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        
        # 创建初始配置文件
        config_content = """target_date: null
article_urls: []
api_config:
  account_names:
    - 测试公众号
"""
        config_path.write_text(config_content, encoding='utf-8')
        
        config_manager = ConfigManager(str(config_path))
        env_manager = EnvFileManager(config_manager.project_root)
        
        # 备份原有的 .env 值
        old_token = env_manager.get('WECHAT_API_TOKEN')
        old_cookie = env_manager.get('WECHAT_API_COOKIE')
        
        try:
            # 保存 Token 和 Cookie 到 .env 文件
            config_manager.set_api_token('new_token_123', save_to_env=True)
            config_manager.set_api_cookie('new_cookie_456', save_to_env=True)
            config_manager.save_config()
            
            # 验证 .env 文件包含这些值
            assert env_manager.get('WECHAT_API_TOKEN') == 'new_token_123'
            assert env_manager.get('WECHAT_API_COOKIE') == 'new_cookie_456'
            
            # 验证 config.yaml 不包含这些值
            saved_content = config_path.read_text(encoding='utf-8')
            assert 'new_token_123' not in saved_content
            assert 'new_cookie_456' not in saved_content
            
            print("✓ 测试通过：保存到 .env 文件，未泄露到 config.yaml")
            
        finally:
            # 恢复原有的值或删除测试添加的键
            if old_token:
                env_manager.update('WECHAT_API_TOKEN', old_token)
            else:
                env_manager.remove('WECHAT_API_TOKEN')
            
            if old_cookie:
                env_manager.update('WECHAT_API_COOKIE', old_cookie)
            else:
                env_manager.remove('WECHAT_API_COOKIE')


def test_save_to_config_file():
    """测试：保存到 config.yaml 的正常功能"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        
        config_content = """target_date: null
article_urls: []
api_config:
  account_names:
    - 测试公众号
"""
        config_path.write_text(config_content, encoding='utf-8')
        
        config_manager = ConfigManager(str(config_path))
        
        # 保存到配置文件
        config_manager.set_api_token('config_token_789', save_to_env=False)
        config_manager.set_api_cookie('config_cookie_000', save_to_env=False)
        config_manager.save_config()
        
        # 验证 config.yaml 包含这些值
        saved_content = config_path.read_text(encoding='utf-8')
        assert 'config_token_789' in saved_content or 'token: config_token_789' in saved_content
        assert 'config_cookie_000' in saved_content
        
        # 验证 .env 文件不存在或不包含这些值
        env_manager = EnvFileManager(Path(tmpdir))
        if env_manager.exists():
            assert env_manager.get('WECHAT_API_TOKEN') != 'config_token_789'
            assert env_manager.get('WECHAT_API_COOKIE') != 'config_cookie_000'
        
        print("✓ 测试通过：正确保存到 config.yaml")


def test_clear_sensitive_data():
    """测试：清空敏感数据"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        
        # 创建包含敏感数据的配置文件
        config_content = """target_date: null
article_urls: []
api_config:
  token: 1234567890
  cookie: old_cookie
  account_names:
    - 测试公众号
"""
        config_path.write_text(config_content, encoding='utf-8')
        
        config_manager = ConfigManager(str(config_path))
        
        # 清空 Token 和 Cookie（保存到 config.yaml 模式）
        config_manager.set_api_token('', save_to_env=False)
        config_manager.set_api_cookie('', save_to_env=False)
        config_manager.save_config()
        
        # 验证配置文件中的值已清空
        saved_content = config_path.read_text(encoding='utf-8')
        assert '1234567890' not in saved_content
        assert 'old_cookie' not in saved_content
        
        print("✓ 测试通过：清空敏感数据功能正常")


if __name__ == '__main__':
    print("开始测试配置优先级和隐私保护功能...\n")
    print("配置优先级（从高到低）：")
    print("  1. config.yaml 文件")
    print("  2. .env 文件")
    print("  3. 系统环境变量\n")
    
    test_priority_config_over_env_file()
    test_priority_env_file_over_system()
    test_save_to_env_file()
    test_save_to_config_file()
    test_clear_sensitive_data()
    
    print("\n✅ 所有测试通过！配置优先级和隐私保护功能正常工作。")
