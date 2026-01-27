from abc import ABC, abstractmethod
from typing import Optional, Callable


class CancelledError(Exception):
    """工作流被取消时抛出的异常"""
    pass


class BaseWorkflow(ABC):
    """基础工作流类

    支持通过 cancel_checker 回调函数检查取消状态。
    子类在耗时操作（如循环、网络请求）前应调用 check_cancelled() 方法。
    """

    def __init__(self) -> None:
        """初始化基础工作流
        """
        # 取消检查回调函数，由外部（如 WorkflowWorker）设置
        self._cancel_checker: Optional[Callable[[], bool]] = None

    def set_cancel_checker(self, checker: Callable[[], bool]) -> None:
        """设置取消检查回调函数

        Args:
            checker: 返回 True 表示已取消，返回 False 表示未取消
        """
        self._cancel_checker = checker

    def is_cancelled(self) -> bool:
        """检查工作流是否已被取消

        Returns:
            bool: True 表示已取消，False 表示未取消
        """
        if self._cancel_checker is not None:
            return self._cancel_checker()
        return False

    def check_cancelled(self) -> None:
        """检查取消状态，如果已取消则抛出 CancelledError

        Raises:
            CancelledError: 当工作流被取消时抛出
        """
        if self.is_cancelled():
            raise CancelledError("工作流已被用户取消")

    @abstractmethod
    def build_workflow(self) -> None:
        """构建工作流抽象方法
        """
        pass

    @abstractmethod
    def run(self) -> None:
        """运行工作流抽象方法
        """
        pass
