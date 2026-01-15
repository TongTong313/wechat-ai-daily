"""
自定义 Logging Handler

用于拦截 Python logging 输出并转发到前端监控界面。
无需修改核心代码，只需配置 logger 即可。
"""

import logging
import re
from typing import Optional, List, Dict
from pathlib import Path


class WebSocketLoggingHandler(logging.Handler):
    """WebSocket 日志处理器
    
    拦截所有 logging 输出，将日志消息转发到 ProgressReporter，
    然后通过 WebSocket 推送到前端。
    
    特点：
    1. 不影响原有日志输出（控制台和文件照常工作）
    2. 自动解析日志内容，识别操作状态
    3. 提取关键信息（如进度、文章链接等）
    """
    
    def __init__(self, progress_reporter):
        """初始化 Handler
        
        Args:
            progress_reporter: ProgressReporter 实例
        """
        super().__init__()
        self.reporter = progress_reporter
        
        # 关键操作的日志模式（用于自动识别当前操作状态）
        self.status_patterns = [
            (r'正在打开微信|打开/激活微信', '正在打开微信'),
            (r'微信已启动|微信窗口已激活|微信应用已就绪', '微信应用已就绪'),
            (r'正在打开微信搜索|打开微信搜索', '打开微信搜索'),
            (r'微信搜索界面已打开', '搜索界面已就绪'),
            (r'正在复制公众号URL|搜索公众号URL', '正在搜索公众号'),
            (r'已成功进入公众号主页|公众号主页已加载', '进入公众号主页'),
            (r'开始采集公众号文章|开始采集当天所有文章', '开始采集文章'),
            (r'正在识别当天日期|VLM 识别中', '使用 VLM 识别日期'),
            (r'识别到.*个当天日期位置', 'VLM 识别完成'),
            (r'点击进入文章', '正在点击文章'),
            (r'正在查找.*三个点.*按钮|复制文章链接', '正在复制链接'),
            (r'文章链接已复制|已复制文章链接', '链接复制成功'),
            (r'正在查找.*返回.*按钮|返回公众号主页', '返回主页'),
            (r'向下滚动页面', '滚动加载更多'),
            (r'文章链接采集完成', '当前公众号采集完成'),
            (r'所有公众号采集任务完成', '全部采集完成'),
        ]
        
        # 进度信息的模式
        self.progress_patterns = [
            r'正在处理第\s*(\d+)/(\d+)\s*个公众号',
            r'处理第\s*(\d+)/(\d+)\s*个文章位置',
        ]
        
        # 文章链接模式
        self.article_link_pattern = r'(https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+)'
        
    def emit(self, record: logging.LogRecord):
        """处理日志记录
        
        Args:
            record: logging.LogRecord 对象
        """
        try:
            # 格式化日志消息
            message = self.format(record)
            
            # 1. 发送日志到前端
            level = self._map_log_level(record.levelno)
            self.reporter.send_log(level, message)
            
            # 2. 尝试识别操作状态
            status = self._extract_status(message)
            if status:
                self.reporter.send_status(status)
            
            # 3. 尝试提取进度信息
            progress = self._extract_progress(message)
            if progress:
                current, total = progress
                self.reporter.send_progress(current, total)
            
            # 注意：文章链接不再从日志中自动提取
            # 改为从 output 目录的 markdown 文件中读取（避免重复统计）
                
        except Exception as e:
            # Handler 内部错误不应该影响主程序
            # 只在控制台输出错误信息
            import sys
            print(f"WebSocketLoggingHandler 错误: {e}", file=sys.stderr)
    
    def _map_log_level(self, levelno: int) -> str:
        """映射 logging 级别到前端显示级别
        
        Args:
            levelno: logging 级别数值
            
        Returns:
            前端级别字符串: info/warning/error/success
        """
        if levelno >= logging.ERROR:
            return 'error'
        elif levelno >= logging.WARNING:
            return 'warning'
        elif levelno >= logging.INFO:
            # 特殊处理：包含"成功"、"完成"等关键词的显示为 success
            return 'info'
        else:
            return 'info'
    
    def _extract_status(self, message: str) -> Optional[str]:
        """从日志消息中提取操作状态
        
        Args:
            message: 日志消息
            
        Returns:
            操作状态文本，如果未匹配返回 None
        """
        for pattern, status in self.status_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return status
        return None
    
    def _extract_progress(self, message: str) -> Optional[tuple]:
        """从日志消息中提取进度信息
        
        Args:
            message: 日志消息
            
        Returns:
            (current, total) 元组，如果未匹配返回 None
        """
        for pattern in self.progress_patterns:
            match = re.search(pattern, message)
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                return (current, total)
        return None
    
    def _extract_article_link(self, message: str) -> Optional[str]:
        """从日志消息中提取文章链接
        
        Args:
            message: 日志消息
            
        Returns:
            文章链接，如果未匹配返回 None
        """
        match = re.search(self.article_link_pattern, message)
        if match:
            return match.group(1)
        return None


def setup_logging_forwarding(progress_reporter) -> WebSocketLoggingHandler:
    """配置日志转发到前端
    
    Args:
        progress_reporter: ProgressReporter 实例
        
    Returns:
        WebSocketLoggingHandler 实例
    """
    # 创建 WebSocket Handler
    ws_handler = WebSocketLoggingHandler(progress_reporter)
    ws_handler.setLevel(logging.INFO)  # 只转发 INFO 及以上级别的日志
    
    # 使用简洁的格式（前端会自带时间戳）
    formatter = logging.Formatter('%(message)s')
    ws_handler.setFormatter(formatter)
    
    # 添加到根 logger，这样所有模块的日志都会被拦截
    root_logger = logging.getLogger()
    root_logger.addHandler(ws_handler)
    
    return ws_handler


def remove_logging_forwarding(handler: WebSocketLoggingHandler):
    """移除日志转发
    
    Args:
        handler: 要移除的 WebSocketLoggingHandler 实例
    """
    root_logger = logging.getLogger()
    root_logger.removeHandler(handler)


def parse_articles_from_markdown(md_file_path: str) -> List[Dict[str, str]]:
    """从 markdown 文件中解析文章链接列表
    
    文件格式示例：
    ```
    # 微信公众号文章链接
    生成时间: 2026-01-15 12:00:00
    
    ## 文章列表
    1. https://mp.weixin.qq.com/s/xxxxx
    2. https://mp.weixin.qq.com/s/yyyyy
    ```
    
    Args:
        md_file_path: markdown 文件路径
        
    Returns:
        文章列表，每个元素包含 {'link': '链接', 'index': 序号}
    """
    articles = []
    
    try:
        if not Path(md_file_path).exists():
            return articles
            
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 正则匹配：序号 + 链接格式
        # 例如：1. https://mp.weixin.qq.com/s/xxxxx
        pattern = r'^\s*(\d+)\.\s+(https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+)'
        
        for line in content.split('\n'):
            match = re.match(pattern, line)
            if match:
                index = int(match.group(1))
                link = match.group(2)
                articles.append({
                    'index': index,
                    'link': link
                })
        
    except Exception as e:
        logging.warning(f"解析 markdown 文件失败: {e}")
    
    return articles


def get_latest_articles_file(output_dir: str = "output") -> Optional[str]:
    """获取 output 目录中最新的文章文件
    
    Args:
        output_dir: 输出目录路径
        
    Returns:
        最新文章文件的路径，如果不存在返回 None
    """
    try:
        output_path = Path(output_dir)
        if not output_path.exists():
            return None
        
        # 查找所有 markdown 文件
        md_files = list(output_path.glob("articles_*.md"))
        
        if not md_files:
            return None
        
        # 按修改时间排序，返回最新的
        latest_file = max(md_files, key=lambda p: p.stat().st_mtime)
        return str(latest_file)
        
    except Exception as e:
        logging.warning(f"获取最新文章文件失败: {e}")
        return None
