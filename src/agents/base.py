"""Agent 抽象基类"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """所有 Agent 的基类"""

    def __init__(self, name: str, system_prompt: str) -> None:
        self.name = name
        self.system_prompt = system_prompt

    @abstractmethod
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """执行 Agent 任务，输入共享状态，返回更新后的状态"""
        pass
