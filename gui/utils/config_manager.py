# -*- coding: utf-8 -*-
"""
配置管理器

负责读写 configs/config.yaml 配置文件，管理 API Key 等敏感信息。
"""

import os
import sys
import yaml
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path


class ConfigManager:
    """配置管理器

    负责管理应用配置，包括：
    - 读写 config.yaml 文件
    - 管理 API Key（环境变量或配置文件）
    - 根据操作系统自动设置 GUI 模板路径
    """

    # 默认配置文件路径（相对于项目根目录）
    DEFAULT_CONFIG_PATH = "configs/config.yaml"

    # API Key 环境变量名
    API_KEY_ENV_NAME = "DASHSCOPE_API_KEY"

    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为 configs/config.yaml
        """
        # 确定项目根目录
        self.project_root = self._find_project_root()

        # 配置文件路径（支持 PyInstaller 打包后的 fallback）
        if config_path:
            self.config_path = Path(config_path)
            self._save_path = self.config_path  # 保存位置与读取位置相同
        else:
            # 配置文件的持久化保存位置（始终在 exe 旁边，确保不丢失）
            self._save_path = self.project_root / self.DEFAULT_CONFIG_PATH
            
            # 读取位置：优先使用项目根目录下的配置文件
            self.config_path = self._save_path

            # 如果不存在且在打包环境中，从打包资源读取默认配置
            if not self.config_path.exists() and getattr(sys, 'frozen', False):
                bundled_config = Path(sys._MEIPASS) / self.DEFAULT_CONFIG_PATH
                if bundled_config.exists():
                    self.config_path = bundled_config
                    # 注意：_save_path 仍然指向 exe 旁边，确保保存时不会写入临时目录

        # 加载配置
        self.config: Dict[str, Any] = {}
        self.load_config()

    def _find_project_root(self) -> Path:
        """查找项目根目录

        优先使用环境变量 WECHAT_AI_DAILY_ROOT（由 app.py 设置，兼容 PyInstaller 打包）。
        如果环境变量不存在，则通过查找 pyproject.toml 或 configs 目录来定位。

        Returns:
            Path: 项目根目录路径
        """
        # 优先使用环境变量（兼容 PyInstaller 打包后的环境）
        env_root = os.environ.get('WECHAT_AI_DAILY_ROOT')
        if env_root:
            return Path(env_root)

        # 检查是否在 PyInstaller 打包环境中
        if getattr(sys, 'frozen', False):
            # 打包后使用 exe 所在目录
            return Path(sys.executable).parent

        # 开发环境：从当前文件向上查找
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

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件

        Returns:
            Dict: 配置字典
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f) or {}
                logging.info(f"配置文件加载成功: {self.config_path}")
            else:
                logging.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self.config = self._get_default_config()
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            self.config = self._get_default_config()

        return self.config

    def save_config(self) -> bool:
        """保存配置到文件
        
        注意：始终保存到 exe 旁边的持久化位置（_save_path），
        而不是可能指向临时目录的 config_path。

        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在（使用持久化保存路径）
            self._save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self._save_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False
                )
            logging.info(f"配置文件保存成功: {self._save_path}")
            
            # 保存后更新 config_path，后续读取使用新保存的文件
            self.config_path = self._save_path
            return True
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
            return False

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置

        Returns:
            Dict: 默认配置字典
        """
        return {
            "target_date": None,  # null 表示当天
            "article_urls": [],
            "GUI_config": self._get_platform_gui_config(),
            "model_config": {
                "LLM": {
                    "model": "qwen-plus",
                    "api_key": None,
                    "thinking_budget": 1024,
                    "enable_thinking": True
                },
                "VLM": {
                    "model": "qwen3-vl-plus",
                    "api_key": None,
                    "thinking_budget": 1024,
                    "enable_thinking": True
                }
            }
        }

    def _get_platform_gui_config(self) -> Dict[str, str]:
        """根据操作系统获取 GUI 模板配置

        Returns:
            Dict: GUI 模板路径配置
        """
        if sys.platform == "darwin":
            # macOS
            return {
                "search_website": "templates/search_website_mac.png",
                "three_dots": "templates/three_dots_mac.png",
                "turnback": "templates/turnback_mac.png"
            }
        else:
            # Windows 或其他
            return {
                "search_website": "templates/search_website.png",
                "three_dots": "templates/three_dots.png",
                "turnback": "templates/turnback.png"
            }

    # ==================== 日期配置管理 ====================

    def get_target_date(self) -> Optional[str]:
        """获取目标日期配置

        Returns:
            Optional[str]: 目标日期字符串，可能的值：
                - None: 当天
                - "today": 当天
                - "yesterday": 昨天
                - "YYYY-MM-DD": 指定日期
        """
        return self.config.get("target_date")

    def set_target_date(self, date_value: Optional[str]) -> None:
        """设置目标日期配置

        Args:
            date_value: 目标日期值，支持：
                - None 或 "today": 当天
                - "yesterday": 昨天
                - "YYYY-MM-DD": 指定日期
        """
        self.config["target_date"] = date_value

    # ==================== 文章链接管理 ====================

    def get_article_urls(self) -> List[str]:
        """获取文章链接列表

        Returns:
            List[str]: 文章链接列表
        """
        return self.config.get("article_urls", [])

    def set_article_urls(self, urls: List[str]) -> None:
        """设置文章链接列表

        Args:
            urls: 文章链接列表
        """
        self.config["article_urls"] = urls

    def add_article_url(self, url: str) -> bool:
        """添加文章链接

        Args:
            url: 文章链接

        Returns:
            bool: 是否添加成功（重复则返回 False）
        """
        urls = self.get_article_urls()
        if url not in urls:
            urls.append(url)
            self.config["article_urls"] = urls
            return True
        return False

    def remove_article_url(self, url: str) -> bool:
        """删除文章链接

        Args:
            url: 要删除的链接

        Returns:
            bool: 是否删除成功
        """
        urls = self.get_article_urls()
        if url in urls:
            urls.remove(url)
            self.config["article_urls"] = urls
            return True
        return False

    # ==================== API Key 管理 ====================

    def get_api_key(self) -> Optional[str]:
        """获取 API Key

        优先从配置文件读取，如果为空则从环境变量读取。

        Returns:
            Optional[str]: API Key，如果未设置返回 None
        """
        # 先尝试从配置文件读取
        config_api_key = self.config.get(
            "model_config", {}).get("LLM", {}).get("api_key")
        if config_api_key:
            return config_api_key

        # 再从环境变量读取
        return os.environ.get(self.API_KEY_ENV_NAME)

    def set_api_key(self, api_key: str, save_to_env: bool = False) -> None:
        """设置 API Key

        Args:
            api_key: API Key 值
            save_to_env: 是否保存到环境变量（当前会话）
        """
        if save_to_env:
            # 保存到环境变量（当前会话有效）
            os.environ[self.API_KEY_ENV_NAME] = api_key
            # 配置文件中设为 null
            if "model_config" not in self.config:
                self.config["model_config"] = {}
            if "LLM" not in self.config["model_config"]:
                self.config["model_config"]["LLM"] = {}
            if "VLM" not in self.config["model_config"]:
                self.config["model_config"]["VLM"] = {}
            self.config["model_config"]["LLM"]["api_key"] = None
            self.config["model_config"]["VLM"]["api_key"] = None
        else:
            # 保存到配置文件
            if "model_config" not in self.config:
                self.config["model_config"] = {}
            if "LLM" not in self.config["model_config"]:
                self.config["model_config"]["LLM"] = {}
            if "VLM" not in self.config["model_config"]:
                self.config["model_config"]["VLM"] = {}
            self.config["model_config"]["LLM"]["api_key"] = api_key
            self.config["model_config"]["VLM"]["api_key"] = api_key

    # ==================== 模型配置管理 ====================

    def get_llm_model(self) -> str:
        """获取 LLM 模型名称

        Returns:
            str: LLM 模型名称
        """
        return self.config.get("model_config", {}).get("LLM", {}).get("model", "qwen-plus")

    def set_llm_model(self, model: str) -> None:
        """设置 LLM 模型名称

        Args:
            model: 模型名称
        """
        if "model_config" not in self.config:
            self.config["model_config"] = {}
        if "LLM" not in self.config["model_config"]:
            self.config["model_config"]["LLM"] = {}
        self.config["model_config"]["LLM"]["model"] = model

    def get_vlm_model(self) -> str:
        """获取 VLM 模型名称

        Returns:
            str: VLM 模型名称
        """
        return self.config.get("model_config", {}).get("VLM", {}).get("model", "qwen3-vl-plus")

    def set_vlm_model(self, model: str) -> None:
        """设置 VLM 模型名称

        Args:
            model: 模型名称
        """
        if "model_config" not in self.config:
            self.config["model_config"] = {}
        if "VLM" not in self.config["model_config"]:
            self.config["model_config"]["VLM"] = {}
        self.config["model_config"]["VLM"]["model"] = model

    def get_enable_thinking(self) -> bool:
        """获取是否启用思考模式

        Returns:
            bool: 是否启用思考模式
        """
        return self.config.get("model_config", {}).get("LLM", {}).get("enable_thinking", True)

    def set_enable_thinking(self, enabled: bool) -> None:
        """设置是否启用思考模式

        Args:
            enabled: 是否启用
        """
        if "model_config" not in self.config:
            self.config["model_config"] = {}
        if "LLM" not in self.config["model_config"]:
            self.config["model_config"]["LLM"] = {}
        if "VLM" not in self.config["model_config"]:
            self.config["model_config"]["VLM"] = {}
        self.config["model_config"]["LLM"]["enable_thinking"] = enabled
        self.config["model_config"]["VLM"]["enable_thinking"] = enabled

    def get_thinking_budget(self) -> int:
        """获取思考预算（token 数量）

        Returns:
            int: 思考预算，默认 1024
        """
        return self.config.get("model_config", {}).get("LLM", {}).get("thinking_budget", 1024)

    def set_thinking_budget(self, budget: int) -> None:
        """设置思考预算（token 数量）

        Args:
            budget: 思考预算
        """
        if "model_config" not in self.config:
            self.config["model_config"] = {}
        if "LLM" not in self.config["model_config"]:
            self.config["model_config"]["LLM"] = {}
        if "VLM" not in self.config["model_config"]:
            self.config["model_config"]["VLM"] = {}
        self.config["model_config"]["LLM"]["thinking_budget"] = budget
        self.config["model_config"]["VLM"]["thinking_budget"] = budget

    # ==================== GUI 配置管理 ====================

    def update_gui_config_for_platform(self) -> None:
        """根据当前操作系统更新 GUI 配置

        自动设置正确的模板图片路径。
        """
        self.config["GUI_config"] = self._get_platform_gui_config()

    def get_gui_config(self) -> Dict[str, str]:
        """获取 GUI 模板配置

        Returns:
            Dict: GUI 模板路径配置
        """
        return self.config.get("GUI_config", self._get_platform_gui_config())

    def set_gui_template_path(self, key: str, path: str) -> None:
        """设置单个 GUI 模板路径

        Args:
            key: 模板键名（search_website, three_dots, turnback）
            path: 模板文件路径
        """
        if "GUI_config" not in self.config:
            self.config["GUI_config"] = self._get_platform_gui_config()
        self.config["GUI_config"][key] = path

    def get_current_platform(self) -> str:
        """获取当前操作系统名称

        Returns:
            str: 操作系统名称（Windows / macOS / Linux）
        """
        if sys.platform == "darwin":
            return "macOS"
        elif sys.platform == "win32":
            return "Windows"
        else:
            return "Linux"

    # ==================== 环境变量检测 ====================

    def has_env_api_key(self) -> bool:
        """检测环境变量中是否设置了 API Key

        Returns:
            bool: 是否存在环境变量 DASHSCOPE_API_KEY
        """
        env_key = os.environ.get(self.API_KEY_ENV_NAME, "")
        return bool(env_key and env_key.strip())

    def get_env_api_key(self) -> Optional[str]:
        """获取环境变量中的 API Key

        Returns:
            Optional[str]: 环境变量中的 API Key，如果不存在返回 None
        """
        return os.environ.get(self.API_KEY_ENV_NAME)

    def get_config_api_key(self) -> Optional[str]:
        """获取配置文件中的 API Key（不读取环境变量）

        Returns:
            Optional[str]: 配置文件中的 API Key，如果未设置返回 None
        """
        return self.config.get("model_config", {}).get("LLM", {}).get("api_key")

    def get_config_path(self) -> Path:
        """获取配置文件路径

        Returns:
            Path: 配置文件路径
        """
        return self.config_path

    def get_project_root(self) -> Path:
        """获取项目根目录

        Returns:
            Path: 项目根目录路径
        """
        return self.project_root
