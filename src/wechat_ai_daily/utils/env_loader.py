"""
环境变量加载工具

负责从 .env 文件加载环境变量，优先级：
1. 系统环境变量（最高优先级）
2. .env 文件
3. config.yaml 文件（最低优先级，由各模块自行处理）

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
    已存在的环境变量不会被覆盖（系统环境变量优先级更高）。

    Returns:
        dict: 配置来源报告 {
            'env_file_loaded': bool,  # 是否成功加载 .env 文件
            'env_file_path': str,     # .env 文件路径
            'sources': {
                'WECHAT_APPID': 'system' | 'env_file' | 'not_set',
                'WECHAT_APPSECRET': 'system' | 'env_file' | 'not_set',
                'DASHSCOPE_API_KEY': 'system' | 'env_file' | 'not_set',
            }
        }
    """
    project_root = find_project_root()
    env_path = project_root / ".env"

    # 记录加载前已存在的环境变量（来自系统）
    env_keys = [ENV_WECHAT_APPID, ENV_WECHAT_APPSECRET, ENV_DASHSCOPE_API_KEY]
    before_load = {key: os.getenv(key) for key in env_keys}

    # 加载 .env 文件
    env_file_loaded = False
    if env_path.exists():
        # override=False: 不覆盖已存在的环境变量（系统环境变量优先）
        load_dotenv(env_path, override=False)
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
        elif before_load[key]:
            sources[key] = 'system'  # 系统环境变量
            logging.info(f"  {key}: 使用系统环境变量")
        else:
            sources[key] = 'env_file'  # 从 .env 文件加载
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

    env_keys = [ENV_WECHAT_APPID, ENV_WECHAT_APPSECRET, ENV_DASHSCOPE_API_KEY]

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
