"""
环境变量加载工具

负责从 .env 文件加载环境变量到系统环境变量中。

敏感信息配置优先级（从高到低）：
1. config.yaml 文件（最高优先级，如果对应项有值且不为空）
2. .env 文件（项目级环境变量，中优先级）
3. 系统环境变量（全局环境变量，如 ~/.zshrc 中设置的变量，最低优先级）

注意：
- 本模块只负责 .env 文件的加载，不涉及 config.yaml 的读取
- config.yaml 优先级由各业务模块自行处理（如 api_article_collector.py、daily_publish.py 等）
- 调用 load_env() 后，.env 文件中的变量会加载到系统环境变量中
- .env 文件会覆盖系统环境变量（.env 文件 > 系统环境变量）

使用方式：
    在应用启动时调用 load_env() 即可自动加载 .env 文件中的配置。
    
示例：
    >>> from wechat_ai_daily.utils.env_loader import load_env, log_env_diagnostic
    >>> 
    >>> # 加载环境变量
    >>> load_env()
    >>> 
    >>> # 输出诊断信息（可选，用于调试）
    >>> log_env_diagnostic()
"""

from typing import Dict, Any
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging


# 环境变量名称常量
ENV_WECHAT_APPID = "WECHAT_APPID"
ENV_WECHAT_APPSECRET = "WECHAT_APPSECRET"
ENV_DASHSCOPE_API_KEY = "DASHSCOPE_API_KEY"
ENV_WECHAT_API_TOKEN = "WECHAT_API_TOKEN"  # API 模式专属（v2.0.0 新增）
ENV_WECHAT_API_COOKIE = "WECHAT_API_COOKIE"  # API 模式专属（v2.0.0 新增）


def find_project_root() -> Path:
    """查找项目根目录（包含 .env 文件或 pyproject.toml）

    Returns:
        Path: 项目根目录路径
    """
    # 检查是否在 PyInstaller 打包环境中
    if getattr(sys, 'frozen', False):
        # 打包后使用 exe 所在目录
        return Path(sys.executable).parent

    # 开发环境：从当前文件向上查找
    current = Path(__file__).resolve().parent

    for _ in range(10):  # 最多向上查找 10 级
        # 优先查找 .env 文件
        if (current / ".env").exists():
            return current
        # 其次查找 pyproject.toml
        if (current / "pyproject.toml").exists():
            return current

        parent = current.parent
        if parent == current:
            break
        current = parent

    # 如果找不到，使用当前工作目录
    return Path.cwd()


def load_env() -> dict:
    """加载 .env 文件中的环境变量，并返回配置来源报告

    自动查找项目根目录下的 .env 文件并加载。
    .env 文件会覆盖系统环境变量（.env 文件优先级更高）。

    Returns:
        dict: 配置来源报告 {
            'env_file_loaded': bool,  # 是否成功加载 .env 文件
            'env_file_path': str,     # .env 文件路径
            'sources': {
                'WECHAT_APPID': 'env_file' | 'system' | 'not_set',
                'WECHAT_APPSECRET': 'env_file' | 'system' | 'not_set',
                'DASHSCOPE_API_KEY': 'env_file' | 'system' | 'not_set',
            }
        }
    """
    project_root = find_project_root()
    env_path = project_root / ".env"

    # 记录加载前已存在的环境变量（来自系统）
    env_keys = [
        ENV_WECHAT_APPID, 
        ENV_WECHAT_APPSECRET, 
        ENV_DASHSCOPE_API_KEY,
        ENV_WECHAT_API_TOKEN,
        ENV_WECHAT_API_COOKIE
    ]
    before_load = {key: os.getenv(key) for key in env_keys}

    # 加载 .env 文件
    env_file_loaded = False
    if env_path.exists():
        # override=True: .env 文件覆盖系统环境变量（.env 文件优先级更高）
        load_dotenv(env_path, override=True)
        env_file_loaded = True
        logging.info(f"✅ 已加载环境变量文件: {env_path}")
    else:
        logging.debug(f"未找到 .env 文件: {env_path}")

    # 检测每个环境变量的来源
    sources = {}
    for key in env_keys:
        current_value = os.getenv(key)
        if not current_value:
            sources[key] = 'not_set'
        elif env_file_loaded and current_value != before_load.get(key):
            sources[key] = 'env_file'  # 从 .env 文件加载（值发生了变化）
            logging.info(f"  {key}: 从 .env 文件加载")
        elif before_load.get(key):
            sources[key] = 'system'  # 系统环境变量（.env 中没有该键）
            logging.info(f"  {key}: 使用系统环境变量")
        else:
            sources[key] = 'env_file'  # 从 .env 文件加载（新增的键）
            logging.info(f"  {key}: 从 .env 文件加载")

    return {
        'env_file_loaded': env_file_loaded,
        'env_file_path': str(env_path) if env_file_loaded else None,
        'sources': sources
    }


def get_env(key: str, default: str = None) -> str:
    """获取环境变量（支持从 .env 或系统环境变量读取）

    Args:
        key: 环境变量名
        default: 默认值（如果环境变量不存在）

    Returns:
        str: 环境变量值
    """
    return os.getenv(key, default)


def has_env(key: str) -> bool:
    """检查环境变量是否存在

    Args:
        key: 环境变量名

    Returns:
        bool: 是否存在且非空
    """
    value = os.getenv(key, "")
    return bool(value and value.strip())


def diagnose_env() -> Dict[str, Any]:
    """诊断环境变量配置情况

    用于调试和故障排查，显示所有配置来源。

    Returns:
        Dict[str, Any]: 诊断报告嵌套字典
        - project_root (Path): 项目根目录
        - env_file_exists (bool): 是否存在 .env 文件
        - environment_variables (Dict[str, Any]): 环境变量字典
            - key (str): 环境变量名（WECHAT_APPID、WECHAT_APPSECRET、DASHSCOPE_API_KEY）
            - value (Dict[str, Any]): 环境变量值嵌套字典
                - is_set (bool): 是否设置
                - value_length (int): 值长度
                - masked_value (str): 值前8位（如果值长度大于8，则显示前8位并省略剩余部分，否则不显示）
    """
    report = {
        'project_root': str(find_project_root()),
        'env_file_exists': (find_project_root() / ".env").exists(),
        'environment_variables': {}
    }

    env_keys = [
        ENV_WECHAT_APPID, 
        ENV_WECHAT_APPSECRET, 
        ENV_DASHSCOPE_API_KEY,
        ENV_WECHAT_API_TOKEN,
        ENV_WECHAT_API_COOKIE
    ]

    for key in env_keys:
        value = os.getenv(key)
        report['environment_variables'][key] = {
            'is_set': bool(value),
            'value_length': len(value) if value else 0,  # 不显示实际值，只显示长度
            'masked_value': value[:8] + '...' if value and len(value) > 8 else None
        }

    return report


def log_env_diagnostic():
    """使用 logging 输出环境变量诊断信息（用于调试）"""
    report = diagnose_env()
    
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "="*70)
    logger.info("环境变量诊断报告")
    logger.info("="*70)
    logger.info(f"项目根目录: {report['project_root']}")
    logger.info(f".env 文件存在: {'是' if report['env_file_exists'] else '否'}")
    logger.info("\n环境变量状态:")

    for key, info in report['environment_variables'].items():
        status = "✅ 已设置" if info['is_set'] else "❌ 未设置"
        value_info = f"({info['masked_value']})" if info['masked_value'] else ""
        logger.info(f"  {key}: {status} {value_info}")

    logger.info("="*70 + "\n")
