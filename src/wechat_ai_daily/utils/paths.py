# -*- coding: utf-8 -*-
"""
路径工具模块

提供获取项目根目录的工具函数，兼容 PyInstaller 打包后的环境。

PyInstaller 打包说明：
- _MEIPASS: 打包资源的临时解压目录（只读）
- exe 所在目录: 用户可以放置配置文件和模板的位置（可写）
- 本模块优先使用 exe 所在目录，以便用户可以自定义配置和模板
"""

import os
import sys
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录路径（用于输出文件等可写内容）
    
    优先级：
    1. 环境变量 WECHAT_AI_DAILY_ROOT（由 app.py 设置）
    2. PyInstaller 打包环境：exe 所在目录
    3. 开发环境：从当前文件向上查找 pyproject.toml 或 configs 目录
    
    Returns:
        Path: 项目根目录路径
    """
    # 优先使用环境变量（由 app.py 设置，兼容 GUI 客户端）
    env_root = os.environ.get('WECHAT_AI_DAILY_ROOT')
    if env_root:
        return Path(env_root)
    
    # 检查是否在 PyInstaller 打包环境中
    if getattr(sys, 'frozen', False):
        # 打包后使用 exe 所在目录
        return Path(sys.executable).parent
    
    # 开发环境：从当前文件向上查找项目根目录
    # 当前文件位于 src/wechat_ai_daily/utils/paths.py
    current = Path(__file__).resolve().parent
    
    for _ in range(10):  # 最多向上查找 10 级
        if (current / "pyproject.toml").exists():
            return current
        if (current / "configs").is_dir():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    
    # 如果找不到，使用当前工作目录
    return Path.cwd()


def _get_bundled_dir() -> Path:
    """获取 PyInstaller 打包资源目录
    
    Returns:
        Path: 打包资源目录路径（_MEIPASS 或项目根目录）
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包环境，返回临时解压目录
        return Path(sys._MEIPASS)
    else:
        # 开发环境，返回项目根目录
        return get_project_root()


def get_output_dir() -> Path:
    """获取输出目录路径
    
    输出目录始终在 exe 所在目录（或项目根目录），以便用户访问生成的文件。
    
    Returns:
        Path: 输出目录路径（项目根目录下的 output 文件夹）
    """
    output_dir = get_project_root() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_temp_dir() -> Path:
    """获取临时文件目录路径
    
    Returns:
        Path: 临时目录路径（项目根目录下的 temp 文件夹）
    """
    temp_dir = get_project_root() / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def get_templates_dir() -> Path:
    """获取模板目录路径
    
    优先使用 exe 旁边的 templates 目录（允许用户自定义），
    如果不存在则使用打包进去的资源。
    
    Returns:
        Path: 模板目录路径
    """
    # 优先检查 exe 旁边是否有 templates 目录
    external_templates = get_project_root() / "templates"
    if external_templates.is_dir():
        return external_templates
    
    # 否则使用打包进去的资源
    return _get_bundled_dir() / "templates"


def get_configs_dir() -> Path:
    """获取配置目录路径
    
    优先使用 exe 旁边的 configs 目录（允许用户自定义配置），
    如果不存在则使用打包进去的资源。
    
    Returns:
        Path: 配置目录路径
    """
    # 优先检查 exe 旁边是否有 configs 目录
    external_configs = get_project_root() / "configs"
    if external_configs.is_dir():
        return external_configs
    
    # 否则使用打包进去的资源
    return _get_bundled_dir() / "configs"
