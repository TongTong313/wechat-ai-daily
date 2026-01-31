# -*- coding: utf-8 -*-
"""
微信 AI 日报助手 - Web 控制台入口

运行方式：
    uv run web_app.py
"""

import os
import sys
from pathlib import Path

import uvicorn

from wechat_ai_daily.utils.env_loader import load_env


def _get_project_root() -> Path:
    """获取项目根目录，确保 Web 服务可正确定位配置与静态资源"""
    return Path(__file__).resolve().parent


def main() -> None:
    project_root = _get_project_root()
    os.environ.setdefault("WECHAT_AI_DAILY_ROOT", str(project_root))

    # 确保项目根目录与 src 可被导入
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    src_path = project_root / "src"
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # 加载 .env 文件中的环境变量
    load_env()

    uvicorn.run(
        "apps.web.server:app",
        host="127.0.0.1",
        port=7860,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
