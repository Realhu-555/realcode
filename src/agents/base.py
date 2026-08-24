"""Agent 抽象基类 —— 支持工具调用和 PromptContext"""

from abc import ABC, abstractmethod
from typing import Any

from src.prompt.context import PromptContext
from src.prompt.renderer import PromptRenderer


class BaseAgent(ABC):
    """所有 Agent 的基类

    改造后支持：
    - PromptContext 多源组装（产品信息 + 策略 + 工具描述 + 品牌偏好）
    - 工具调用权限控制
    - Jinja2 模板渲染 system prompt
    """

    def __init__(
        self,
        name: str,
        system_prompt: str = "",
        tools: list[str] | None = None,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt  # 保留向后兼容
        self.tool_ids = tools or []  # 该 Agent 可用的工具 ID 列表
        self.renderer = PromptRenderer()

    @abstractmethod
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """执行 Agent 任务

        Args:
            state: 共享状态字典（ContentProjectState）

        Returns:
            更新后的状态字典
        """
        pass

    def build_prompt_context(self, state: dict[str, Any]) -> PromptContext:
        """从 ProjectState 构建 PromptContext —— 子类重写

        默认实现：提供最基础的上下文。子类应重写此方法，
        从 state 中提取产品信息、策略、工具描述等。

        Args:
            state: 共享状态字典

        Returns:
            PromptContext 数据对象
        """
        return PromptContext(agent_name=self.name)

    def build_system_prompt(self, state: dict[str, Any]) -> str:
        """构建最终 system prompt —— PromptContext → 模板渲染

        Args:
            state: 共享状态字典

        Returns:
            渲染后的 system prompt 字符串
        """
        ctx = self.build_prompt_context(state)
        template = ctx.role_instructions or self.system_prompt
        if not template:
            return self.system_prompt
        return self.renderer.render(template, ctx.to_template_vars())

    async def call_tool(self, tool_id: str, ctx: Any, **kwargs: Any) -> Any:
        """调用工具 —— 从 ToolRegistry 查找并执行

        Args:
            tool_id: 工具 ID
            ctx: ToolContext 对象
            **kwargs: 工具参数

        Returns:
            ToolResult 对象

        Raises:
            ValueError: 工具不存在
            PermissionError: Agent 无权使用该工具
        """
        from src.tools.registry import tool_registry

        tool = tool_registry.get(tool_id)
        if tool is None:
            raise ValueError(f"工具不存在: {tool_id}")
        if tool_id not in self.tool_ids:
            raise PermissionError(f"Agent {self.name} 无权使用工具: {tool_id}")
        return await tool.execute(ctx, **kwargs)
