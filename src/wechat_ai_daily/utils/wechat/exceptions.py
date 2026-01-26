"""微信 API 异常定义"""


class WeChatAPIError(Exception):
    """微信 API 错误基类"""
    
    def __init__(self, code: int, message: str):
        """
        初始化异常
        
        Args:
            code: 错误码
            message: 错误信息
        """
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class PublishError(WeChatAPIError):
    """发布 API 错误"""
    pass


class ArticleError(WeChatAPIError):
    """文章获取 API 错误"""
    pass
