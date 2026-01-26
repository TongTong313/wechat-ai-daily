from abc import ABC, abstractmethod


class BaseWorkflow(ABC):
    """基础工作流类
    """

    def __init__(self) -> None:
        """初始化基础工作流
        """
        pass

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
