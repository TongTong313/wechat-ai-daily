# 微信公众号自动发布工作流

from ruamel.yaml import YAML
import logging
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
import requests

from .base import BaseWorkflow
from ..utils.wechat import PublishClient


class DailyPublisher(BaseWorkflow):
    """微信公众号自动发布工作流

    采用微信官方的公众号API接口实现自动发布功能。

    Args:
        config (str): 配置文件的路径地址，默认为 "configs/config.yaml"
            publish_config:
                appid: 微信公众号 AppID
                appsecret: 微信公众号 AppSecret
                cover_path: 封面图片路径
    """

    def __init__(self, config: str = "configs/config.yaml") -> None:
        """
        初始化微信公众号自动发布工作流

        Args:
            config (str): 配置文件路径

        Raises:
            FileNotFoundError: 配置文件不存在时抛出
        """
        # 检查文件是否存在
        if not Path(config).exists():
            raise FileNotFoundError(f"配置文件不存在: {config}")

        # 保存配置文件路径，用于后续写回
        self.config_path = config
        self.yaml = YAML()  # 使用 ruamel.yaml 保留注释
        self.yaml.preserve_quotes = True  # 保留引号
        self.yaml.default_flow_style = False  # 使用块样式

        # 加载配置文件
        with open(config, "r", encoding="utf-8") as f:
            self.config = self.yaml.load(f)

        # 验证必需字段
        if "publish_config" not in self.config:
            raise ValueError("配置文件缺少必需字段: publish_config")

        publish_config = self.config["publish_config"]
        for key in ["cover_path", "author"]:
            if key not in publish_config:
                raise ValueError(f"publish_config 缺少必需字段: {key}")

        # 获取 AppID 和 AppSecret
        # 优先级：config.yaml > .env 文件 > 系统环境变量
        # 注意：os.getenv 会读取环境变量（已在 env_loader 中加载 .env 文件，.env 优先于系统环境变量）
        appid = publish_config.get("appid") or os.getenv("WECHAT_APPID")
        appsecret = publish_config.get(
            "appsecret") or os.getenv("WECHAT_APPSECRET")

        # 初始化微信发布客户端（PublishClient 会进行参数验证和日志输出）
        self.wechat_api = PublishClient(appid, appsecret)

    def _get_access_token(self) -> str:
        """
        获取微信公众号 access token

        Returns:
            str: access token 字符串
        """
        return self.wechat_api.get_access_token()

    def _html_to_wechat_format(self,
                               html_path: str,
                               convert_headings: bool = False) -> str:
        """
        将 HTML 富文本转换为微信公众号支持的格式，由于采用DailyGenerator生成的HTML内容已经符合微信公众号要求，所以默认不转换标题标签。

        Args:
            html_path (str): 原始 HTML 文件路径
            convert_headings (bool, optional): 是否转换标题标签，默认为 False

        Returns:
            str: 转换后的 HTML 字符串
        """
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, "html.parser")

        # 步骤 1: 替换所有标题标签为 p 标签（避免微信 API 的标题限制）
        if convert_headings:
            replaced_count = 0
            for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                for tag in soup.find_all(tag_name):
                    # 创建新的 p 标签
                    new_tag = soup.new_tag('p')
                    # 复制所有属性（包括 style）
                    new_tag.attrs = tag.attrs.copy()
                    # 复制所有子节点（包括文本和嵌套标签）
                    for child in list(tag.children):
                        new_tag.append(child)
                    # 替换原标签
                    tag.replace_with(new_tag)
                    replaced_count += 1

            if replaced_count > 0:
                logging.warning(f"自动替换了 {replaced_count} 个标题标签 (h1-h6 → p)")

        # 步骤 2: 提取 body 内的 section 容器
        # 我们的模板已经使用了内联样式，所以直接提取主要内容即可
        main_section = soup.find("section")

        if not main_section:
            raise ValueError("未找到主要内容区域（<section> 标签）")

        # 步骤 3: 清理HTML格式化空白字符
        # 原始HTML源码中包含换行和缩进空格（为了代码可读性），
        # 浏览器渲染时会忽略这些空白，但微信API会直接保留导致显示异常。
        # 将所有换行及其前后的空白替换为空字符串，彻底去除格式化空白。
        html_content = str(main_section)
        html_content = re.sub(r'\s*\n\s*', '', html_content)

        return html_content

    def _get_material_list(self, material_type: str = "image", offset: int = 0, count: int = 20) -> dict:
        """
        获取永久素材列表，主要为了判断是否已存在封面图片，如果存在则直接使用，否则需要上传封面图片

        Args:
            material_type (str, optional): 素材类型（image/video/voice/news）
            offset (int, optional): 从全部素材的该偏移位置开始返回，0表示从第一个素材
            count (int, optional): 返回素材的数量，取值在1到20之间

        Returns:
            dict: 素材列表，包含 media_id、name、update_time、url 等信息
        """
        access_token = self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={access_token}"

        data = {
            "type": material_type,
            "offset": offset,
            "count": count
        }

        try:
            response = requests.post(url, json=data, timeout=30)
            result = response.json()
        except requests.exceptions.Timeout:
            raise TimeoutError(f"获取素材列表超时（30秒）")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"网络请求失败: {e}")

        if result.get("errcode", 0) != 0:
            raise RuntimeError(f"获取素材列表失败: {result}")

        return result

    def _find_media_by_name(self, file_name: str, material_type: str = "image") -> str:
        """
        根据文件名查找素材的 media_id

        Args:
            file_name (str): 文件名（如 "default_cover.png"）
            material_type (str, optional): 素材类型

        Returns:
            str: media_id，如果未找到返回 None
        """
        offset = 0
        count = 20

        while True:
            result = self._get_material_list(material_type, offset, count)

            if result.get("item_count", 0) == 0:
                break

            for item in result.get("item", []):
                if item.get("name") == file_name:
                    return item["media_id"]

            offset += count
            if offset >= result.get("total_count", 0):
                break

        return None

    def _upload_cover_img(self, cover_img_path: str, media_type: str = "image") -> str:
        """
        上传封面图片作为微信公众号永久素材，主要是为了获取封面图片的 media_id，会先根据图片文件名判断是否已存在，如果存在则直接使用，否则需要上传


        Args:
            cover_img_path (str): 封面图片路径
            media_type (str, optional): 素材类型，默认为 "image"

        Returns:
            str: 封面图片的 media_id，如果未找到返回 None
        """

        cover_img_name = Path(cover_img_path).name
        media_id = self._find_media_by_name(cover_img_name, media_type)
        if media_id:
            logging.info(f"✓ 封面图片已存在，media_id: {media_id}")
            return media_id
        else:
            logging.info(f"✗ 封面图片不存在，正在上传...")
            try:
                media_id = self.wechat_api.upload_media(
                    cover_img_path, media_type)
                logging.info(f"✓ 封面图片上传成功，media_id: {media_id}")
                return media_id
            except (OSError, IOError) as e:
                logging.exception(f"封面图片文件读取失败: {e}")
                raise
            except requests.exceptions.RequestException as e:
                logging.exception(f"封面图片上传网络请求失败: {e}")
                raise
            except Exception as e:
                logging.exception(f"封面图片上传失败: {e}")
                raise

    def _create_draft(self,
                      wechat_content: str,
                      title: str,
                      digest: str = "") -> str:
        """创建微信公众号草稿

        自动处理封面图片上传逻辑：
        1. 如果配置文件中已有 media_id，直接使用
        2. 如果没有，根据 cover_path 上传图片并获取 media_id
        3. 将获取到的 media_id 写回配置文件，避免重复上传

        Args:
            wechat_content (str): 微信公众号内容
            title (str): 微信公众号标题
            digest (str, optional): 微信公众号摘要，默认为空

        Returns:
            str: 草稿的 media_id
        """
        # 获取或上传封面图片的 media_id
        if self.config["publish_config"].get("media_id"):
            thumb_media_id = self.config["publish_config"]["media_id"]
            logging.info(f"✓ 使用配置文件中的封面 media_id: {thumb_media_id}")
        else:
            thumb_media_id = self._upload_cover_img(
                self.config["publish_config"]["cover_path"])
            # 将 media_id 写回配置文件（使用 ruamel.yaml 保留注释）
            self.config["publish_config"]["media_id"] = thumb_media_id
            with open(self.config_path, "w", encoding="utf-8") as f:
                self.yaml.dump(self.config, f)
            logging.info(f"✓ 已将 media_id 写入配置文件")

        # 构建草稿请求体
        request = [{
            "title": title,
            "author": self.config["publish_config"]["author"],
            "digest": digest,
            "content": wechat_content,
            "content_source_url": "",
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }]

        # 创建草稿并返回 media_id
        draft_media_id = self.wechat_api.create_draft(request)
        logging.info(f"✓ 草稿创建成功，media_id: {draft_media_id}")
        return draft_media_id

    def build_workflow(self,
                       html_path: str,
                       title: str,
                       digest: str = "") -> str:
        """基于HTML富文本内容构建微信公众号草稿内容，并创建微信公众号草稿

        Args:
            html_path (str): HTML富文本内容路径
            title (str): 微信公众号标题
            digest (str, optional): 微信公众号摘要，默认为空

        Returns:
            str: 微信公众号草稿的 media_id
        """

        try:
            logging.info(f"✓ 开始基于HTML富文本内容构建微信公众号草稿内容...")
            wechat_content = self._html_to_wechat_format(html_path)
            logging.info(
                f"✓ 基于HTML富文本内容构建微信公众号草稿内容成功，长度: {len(wechat_content)} 字符")

            logging.info(f"✓ 开始创建微信公众号草稿...")
            draft_media_id = self._create_draft(wechat_content, title, digest)
            logging.info(f"✓ 微信公众号草稿创建成功，media_id: {draft_media_id}")
            return draft_media_id

        except FileNotFoundError as e:
            logging.exception(f"HTML文件不存在: {e}")
            raise
        except ValueError as e:
            logging.exception(f"HTML格式错误: {e}")
            raise
        except Exception as e:
            logging.exception(f"构建微信公众号草稿失败: {e}")
            raise

    def run(self, html_path: str, title: str, digest: str = "") -> str:
        """运行微信公众号自动发布工作流

        Args:
            html_path (str): HTML富文本内容路径
            title (str): 微信公众号标题
            digest (str, optional): 微信公众号摘要，默认为空

        Returns:
            str: 微信公众号草稿的 media_id
        """
        try:
            logging.info(f"✓ 开始运行微信公众号自动发布工作流...")
            draft_media_id = self.build_workflow(html_path, title, digest)
            logging.info(f"✓ 微信公众号自动发布工作流运行成功，media_id: {draft_media_id}")
            return draft_media_id
        except Exception as e:
            logging.exception(f"微信公众号自动发布工作流运行失败: {e}")
            raise
