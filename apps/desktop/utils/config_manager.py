# -*- coding: utf-8 -*-
"""
配置管理器

负责读写 configs/config.yaml 配置文件，管理 API Key 等敏感信息。
"""

import os
import sys
from ruamel.yaml import YAML
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

    # 微信公众号凭证环境变量名
    WECHAT_APPID_ENV_NAME = "WECHAT_APPID"
    WECHAT_APPSECRET_ENV_NAME = "WECHAT_APPSECRET"

    # 默认发布标题
    DEFAULT_PUBLISH_TITLE = "AI公众号精选速览"

    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为 configs/config.yaml
        """
        # 初始化 ruamel.yaml（保留注释和格式）
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.default_flow_style = False
        self.yaml.width = 4096  # 避免长行被折叠

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
                    self.config = self.yaml.load(f) or {}
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
        使用 ruamel.yaml 保留注释和格式。

        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在（使用持久化保存路径）
            self._save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self._save_path, "w", encoding="utf-8") as f:
                self.yaml.dump(self.config, f)

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
        """获取目标日期配置（RPA 模式专用）

        Returns:
            Optional[str]: 目标日期字符串，格式 "YYYY-MM-DD"
        """
        return self.config.get("target_date")

    def set_target_date(self, date_value: Optional[str]) -> None:
        """设置目标日期配置（RPA 模式专用）

        Args:
            date_value: 目标日期值，格式 "YYYY-MM-DD"
        """
        self.config["target_date"] = date_value

    def get_start_date(self) -> Optional[str]:
        """获取开始时间配置（API 模式专用）

        Returns:
            Optional[str]: 开始时间字符串，格式 "YYYY-MM-DD HH:mm"
        """
        return self.config.get("start_date")

    def set_start_date(self, date_value: Optional[str]) -> None:
        """设置开始时间配置（API 模式专用）

        Args:
            date_value: 开始时间值，格式 "YYYY-MM-DD HH:mm"
        """
        self.config["start_date"] = date_value

    def get_end_date(self) -> Optional[str]:
        """获取结束时间配置（API 模式专用）

        Returns:
            Optional[str]: 结束时间字符串，格式 "YYYY-MM-DD HH:mm"
        """
        return self.config.get("end_date")

    def set_end_date(self, date_value: Optional[str]) -> None:
        """设置结束时间配置（API 模式专用）

        Args:
            date_value: 结束时间值，格式 "YYYY-MM-DD HH:mm"
        """
        self.config["end_date"] = date_value

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

        优先级：config.yaml > .env 文件 > 系统环境变量

        Returns:
            Optional[str]: API Key，如果未设置返回 None
        """
        # 1. 先尝试从配置文件读取
        config_api_key = self.config.get(
            "model_config", {}).get("LLM", {}).get("api_key")
        if config_api_key:
            return config_api_key

        # 2. 检查 .env 文件
        from .env_file_manager import EnvFileManager
        env_manager = EnvFileManager(self.project_root)
        env_file_value = env_manager.get(self.API_KEY_ENV_NAME)
        if env_file_value:
            return env_file_value

        # 3. 检查系统环境变量
        return os.environ.get(self.API_KEY_ENV_NAME)

    def get_api_key_with_source(self) -> tuple[Optional[str], str]:
        """获取 API Key 及其来源

        优先级：config.yaml > .env 文件 > 系统环境变量
        注意：config.yaml 中值为 null 或空字符串时，视为未设置，会读取环境变量

        Returns:
            tuple[Optional[str], str]: (值, 来源)
            来源可能为: 'config' | 'env_file' | 'system' | 'not_set'
        """
        # 1. 先检查 config.yaml（只有值非空时才使用）
        model_config = self.config.get("model_config", {})
        llm_config = model_config.get("LLM", {})
        config_value = llm_config.get("api_key")
        if config_value:  # 只有非空时才返回 config 来源
            return config_value, 'config'

        # 2. 检查 .env 文件
        from .env_file_manager import EnvFileManager
        env_manager = EnvFileManager(self.project_root)
        env_file_value = env_manager.get(self.API_KEY_ENV_NAME)
        if env_file_value:
            return env_file_value, 'env_file'

        # 3. 检查系统环境变量
        system_value = os.environ.get(self.API_KEY_ENV_NAME)
        if system_value:
            return system_value, 'system'

        return None, 'not_set'

    def set_api_key(self, api_key: str, save_to_env: bool = False) -> None:
        """设置 API Key

        Args:
            api_key: API Key 值（空字符串表示清空）
            save_to_env: 是否保存到 .env 文件（否则保存到 config.yaml）
        """
        if save_to_env:
            # 保存到 .env 文件
            from .env_file_manager import EnvFileManager
            env_manager = EnvFileManager(self.project_root)
            
            if api_key:
                env_manager.update(self.API_KEY_ENV_NAME, api_key)
            else:
                # 空字符串表示清空
                env_manager.remove(self.API_KEY_ENV_NAME)
            
            # 配置文件中设为 null（确保不会从 config.yaml 读取）
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
            
            if api_key:
                self.config["model_config"]["LLM"]["api_key"] = api_key
                self.config["model_config"]["VLM"]["api_key"] = api_key
            else:
                # 空字符串表示清空，设为 None
                self.config["model_config"]["LLM"]["api_key"] = None
                self.config["model_config"]["VLM"]["api_key"] = None

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

    # ==================== 发布配置管理 ====================

    def get_publish_config(self) -> Dict[str, Any]:
        """获取发布配置

        Returns:
            Dict: 发布配置字典
        """
        return self.config.get("publish_config", {})

    def has_wechat_credentials(self) -> bool:
        """检测微信公众号凭证是否已配置

        优先级：config.yaml > 环境变量

        Returns:
            bool: 是否已配置完整的凭证（AppID 和 AppSecret）
        """
        appid, _ = self.get_wechat_appid()
        appsecret, _ = self.get_wechat_appsecret()
        return bool(appid and appsecret)

    def get_wechat_appid(self) -> tuple[Optional[str], str]:
        """获取微信 AppID 及其来源

        优先级：config.yaml > .env 文件 > 系统环境变量
        注意：config.yaml 中值为 null 或空字符串时，视为未设置，会读取环境变量

        Returns:
            tuple[Optional[str], str]: (值, 来源)
            来源可能为: 'config' | 'env_file' | 'system' | 'not_set'
        """
        # 1. 先检查 config.yaml（只有值非空时才使用）
        publish_config = self.config.get("publish_config", {})
        config_value = publish_config.get("appid")
        if config_value:  # 只有非空时才返回 config 来源
            return config_value, 'config'

        # 2. 检查 .env 文件
        from .env_file_manager import EnvFileManager
        env_manager = EnvFileManager(self.project_root)
        env_file_value = env_manager.get(self.WECHAT_APPID_ENV_NAME)
        if env_file_value:
            return env_file_value, 'env_file'

        # 3. 检查系统环境变量
        system_value = os.getenv(self.WECHAT_APPID_ENV_NAME)
        if system_value:
            return system_value, 'system'

        return None, 'not_set'

    def get_wechat_appsecret(self) -> tuple[Optional[str], str]:
        """获取微信 AppSecret 及其来源

        优先级：config.yaml > .env 文件 > 系统环境变量
        注意：config.yaml 中值为 null 或空字符串时，视为未设置，会读取环境变量

        Returns:
            tuple[Optional[str], str]: (值, 来源)
            来源可能为: 'config' | 'env_file' | 'system' | 'not_set'
        """
        # 1. 先检查 config.yaml（只有值非空时才使用）
        publish_config = self.config.get("publish_config", {})
        config_value = publish_config.get("appsecret")
        if config_value:  # 只有非空时才返回 config 来源
            return config_value, 'config'

        # 2. 检查 .env 文件
        from .env_file_manager import EnvFileManager
        env_manager = EnvFileManager(self.project_root)
        env_file_value = env_manager.get(self.WECHAT_APPSECRET_ENV_NAME)
        if env_file_value:
            return env_file_value, 'env_file'

        # 3. 检查系统环境变量
        system_value = os.getenv(self.WECHAT_APPSECRET_ENV_NAME)
        if system_value:
            return system_value, 'system'

        return None, 'not_set'

    def set_wechat_appid(self, appid: str, save_to_config: bool = True) -> None:
        """设置微信 AppID

        Args:
            appid: AppID 值，空字符串表示清空配置
            save_to_config: 是否保存到配置文件（否则保存到 .env 文件）
        """
        if save_to_config:
            # 保存到配置文件
            if "publish_config" not in self.config:
                self.config["publish_config"] = {}
            # 空字符串表示清空，设为 None
            self.config["publish_config"]["appid"] = appid if appid else None
        else:
            # 保存到 .env 文件
            from .env_file_manager import EnvFileManager
            env_manager = EnvFileManager(self.project_root)
            
            if appid:
                env_manager.update(self.WECHAT_APPID_ENV_NAME, appid)
            else:
                env_manager.remove(self.WECHAT_APPID_ENV_NAME)
            
            # 配置文件中设为 None
            if "publish_config" in self.config:
                self.config["publish_config"]["appid"] = None

    def set_wechat_appsecret(self, appsecret: str, save_to_config: bool = True) -> None:
        """设置微信 AppSecret

        Args:
            appsecret: AppSecret 值，空字符串表示清空配置
            save_to_config: 是否保存到配置文件（否则保存到 .env 文件）
        """
        if save_to_config:
            # 保存到配置文件
            if "publish_config" not in self.config:
                self.config["publish_config"] = {}
            # 空字符串表示清空，设为 None
            self.config["publish_config"]["appsecret"] = appsecret if appsecret else None
        else:
            # 保存到 .env 文件
            from .env_file_manager import EnvFileManager
            env_manager = EnvFileManager(self.project_root)
            
            if appsecret:
                env_manager.update(self.WECHAT_APPSECRET_ENV_NAME, appsecret)
            else:
                env_manager.remove(self.WECHAT_APPSECRET_ENV_NAME)
            
            # 配置文件中设为 None
            if "publish_config" in self.config:
                self.config["publish_config"]["appsecret"] = None

    def get_publish_author(self) -> Optional[str]:
        """获取发布作者名

        Returns:
            Optional[str]: 作者名，如果未设置返回 None
        """
        return self.config.get("publish_config", {}).get("author")

    def set_publish_author(self, author: str) -> None:
        """设置发布作者名

        Args:
            author: 作者名
        """
        if "publish_config" not in self.config:
            self.config["publish_config"] = {}
        self.config["publish_config"]["author"] = author

    def get_publish_cover_path(self) -> Optional[str]:
        """获取发布封面图片路径

        Returns:
            Optional[str]: 封面图片路径，如果未设置返回 None
        """
        return self.config.get("publish_config", {}).get("cover_path")

    def set_publish_cover_path(self, path: str) -> None:
        """设置发布封面图片路径

        Args:
            path: 封面图片路径
        """
        if "publish_config" not in self.config:
            self.config["publish_config"] = {}
        self.config["publish_config"]["cover_path"] = path

    def get_publish_title(self) -> str:
        """获取发布默认标题

        Returns:
            str: 默认标题，如果未设置返回默认值
        """
        return self.config.get("publish_config", {}).get("default_title", self.DEFAULT_PUBLISH_TITLE)

    def set_publish_title(self, title: str) -> None:
        """设置发布默认标题

        Args:
            title: 默认标题
        """
        if "publish_config" not in self.config:
            self.config["publish_config"] = {}
        self.config["publish_config"]["default_title"] = title

    # ==================== API 模式配置管理 ====================

    # API 模式环境变量名
    WECHAT_API_TOKEN_ENV_NAME = "WECHAT_API_TOKEN"
    WECHAT_API_COOKIE_ENV_NAME = "WECHAT_API_COOKIE"

    def _get_api_config(self) -> Dict[str, Any]:
        """获取 api_config 节点，不存在则创建

        Returns:
            Dict: api_config 配置字典
        """
        if "api_config" not in self.config:
            self.config["api_config"] = {}
        return self.config["api_config"]

    def get_account_names(self) -> List[str]:
        """获取公众号名称列表（API 模式）

        Returns:
            List[str]: 公众号名称列表
        """
        return self._get_api_config().get("account_names", [])

    def set_account_names(self, names: List[str]) -> None:
        """设置公众号名称列表（API 模式）

        Args:
            names: 公众号名称列表
        """
        self._get_api_config()["account_names"] = names

    def add_account_name(self, name: str) -> bool:
        """添加公众号名称

        Args:
            name: 公众号名称

        Returns:
            bool: 是否添加成功（重复则返回 False）
        """
        names = self.get_account_names()
        if name not in names:
            names.append(name)
            self._get_api_config()["account_names"] = names
            return True
        return False

    def remove_account_name(self, name: str) -> bool:
        """删除公众号名称

        Args:
            name: 要删除的名称

        Returns:
            bool: 是否删除成功
        """
        names = self.get_account_names()
        if name in names:
            names.remove(name)
            self._get_api_config()["account_names"] = names
            return True
        return False

    def get_api_cookie(self) -> Optional[str]:
        """获取 API 模式的 cookie

        优先级：config.yaml > 环境变量

        Returns:
            Optional[str]: cookie 字符串，如果未设置返回 None
        """
        # 1. 先检查 config.yaml
        config_value = self._get_api_config().get("cookie")
        if config_value:
            return config_value

        # 2. 再检查环境变量
        return os.getenv(self.WECHAT_API_COOKIE_ENV_NAME)

    def get_api_cookie_with_source(self) -> tuple[Optional[str], str]:
        """获取 API 模式的 cookie 及其来源

        优先级：config.yaml > .env 文件 > 系统环境变量
        注意：config.yaml 中值为 null 或空字符串时，视为未设置，会读取环境变量

        Returns:
            tuple[Optional[str], str]: (值, 来源)
            来源可能为: 'config' | 'env_file' | 'system' | 'not_set'
        """
        # 1. 先检查 config.yaml（只有值非空时才使用）
        api_config = self._get_api_config()
        config_value = api_config.get("cookie")
        if config_value:  # 只有非空时才返回 config 来源
            return config_value, 'config'

        # 2. 检查 .env 文件
        from .env_file_manager import EnvFileManager
        env_manager = EnvFileManager(self.project_root)
        env_file_value = env_manager.get(self.WECHAT_API_COOKIE_ENV_NAME)
        if env_file_value:
            return env_file_value, 'env_file'

        # 3. 检查系统环境变量
        system_value = os.getenv(self.WECHAT_API_COOKIE_ENV_NAME)
        if system_value:
            return system_value, 'system'

        return None, 'not_set'

    def set_api_cookie(self, cookie: str, save_to_env: bool = False) -> None:
        """设置 API 模式的 cookie

        Args:
            cookie: cookie 字符串，空字符串表示清空配置
            save_to_env: 是否保存到 .env 文件（否则保存到 config.yaml）
        """
        if save_to_env:
            # 保存到 .env 文件
            from .env_file_manager import EnvFileManager
            env_manager = EnvFileManager(self.project_root)
            
            if cookie:
                env_manager.update(self.WECHAT_API_COOKIE_ENV_NAME, cookie)
            else:
                env_manager.remove(self.WECHAT_API_COOKIE_ENV_NAME)
            
            # 配置文件中设为 None
            self._get_api_config()["cookie"] = None
        else:
            # 保存到配置文件
            if cookie:
                self._get_api_config()["cookie"] = cookie
            else:
                # 空字符串表示用户想清空，设为 None
                self._get_api_config()["cookie"] = None

    def get_api_token(self) -> Optional[str]:
        """获取 API 模式的 token

        优先级：config.yaml > 环境变量

        Returns:
            Optional[str]: token 字符串，如果未设置返回 None
        """
        # 1. 先检查 config.yaml
        token = self._get_api_config().get("token")
        if token is not None:
            return str(token)

        # 2. 再检查环境变量
        return os.getenv(self.WECHAT_API_TOKEN_ENV_NAME)

    def get_api_token_with_source(self) -> tuple[Optional[str], str]:
        """获取 API 模式的 token 及其来源

        优先级：config.yaml > .env 文件 > 系统环境变量
        注意：config.yaml 中值为 null 或空字符串时，视为未设置，会读取环境变量

        Returns:
            tuple[Optional[str], str]: (值, 来源)
            来源可能为: 'config' | 'env_file' | 'system' | 'not_set'
        """
        # 1. 先检查 config.yaml（只有值非空时才使用）
        api_config = self._get_api_config()
        config_value = api_config.get("token")
        if config_value:  # 只有非空时才返回 config 来源
            return str(config_value), 'config'

        # 2. 检查 .env 文件
        from .env_file_manager import EnvFileManager
        env_manager = EnvFileManager(self.project_root)
        env_file_value = env_manager.get(self.WECHAT_API_TOKEN_ENV_NAME)
        if env_file_value:
            return env_file_value, 'env_file'

        # 3. 检查系统环境变量
        system_value = os.getenv(self.WECHAT_API_TOKEN_ENV_NAME)
        if system_value:
            return system_value, 'system'

        return None, 'not_set'

    def set_api_token(self, token: str, save_to_env: bool = False) -> None:
        """设置 API 模式的 token

        Args:
            token: token 字符串，空字符串表示清空配置
            save_to_env: 是否保存到 .env 文件（否则保存到 config.yaml）
        """
        if save_to_env:
            # 保存到 .env 文件
            from .env_file_manager import EnvFileManager
            env_manager = EnvFileManager(self.project_root)
            
            if token:
                env_manager.update(self.WECHAT_API_TOKEN_ENV_NAME, token)
            else:
                env_manager.remove(self.WECHAT_API_TOKEN_ENV_NAME)
            
            # 配置文件中设为 None
            self._get_api_config()["token"] = None
        else:
            # 保存到配置文件
            if token:
                # 尝试转换为整数存储（与原配置文件格式保持一致）
                try:
                    self._get_api_config()["token"] = int(token)
                except ValueError:
                    self._get_api_config()["token"] = token
            else:
                # 空字符串表示用户想清空，设为 None
                self._get_api_config()["token"] = None
