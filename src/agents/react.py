"""ReAct Agent 模式实现

ReAct (Reasoning + Acting) 循环：
1. Think: 分析当前状态，决定下一步行动
2. Act: 调用工具执行操作
3. Observe: 观察工具返回结果
4. 重复直到完成或达到步数上限
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

from src.agents.tools import BaseTool, ToolRegistry
from src.llm.provider import LLMProvider

logger = logging.getLogger(__name__)

DEFAULT_MAX_STEPS = 15
DEFAULT_TOKEN_BUDGET = 50000


@dataclass
class StepRecord:
    """单步执行记录"""

    step: int
    thought: str
    action: dict[str, Any] | None
    observation: str | None
    tool_name: str | None
    error: str | None = None


@dataclass
class ReActResult:
    """ReAct 执行结果"""

    final_answer: str | None
    steps: list[StepRecord]
    step_count: int
    hit_step_limit: bool
    tool_errors: list[dict[str, Any]]
    token_used: int


class ReActAgent:
    """ReAct Agent 核心实现"""

    def __init__(
        self,
        name: str,
        tools: list[BaseTool],
        max_steps: int = DEFAULT_MAX_STEPS,
        token_budget: int = DEFAULT_TOKEN_BUDGET,
    ) -> None:
        self.name = name
        self.max_steps = max_steps
        self.token_budget = token_budget
        self.llm = LLMProvider()

        # 构建工具注册表
        self.tool_registry = ToolRegistry()
        for tool in tools:
            self.tool_registry.register(tool)

    def run(self, state: dict[str, Any], task: str) -> dict[str, Any]:
        """执行 ReAct 循环

        Args:
            state: 项目状态
            task: 当前任务描述

        Returns:
            包含 final_answer 和工作记忆的更新状态
        """
        steps: list[StepRecord] = []
        tool_errors: list[dict[str, Any]] = []
        token_used = 0
        hit_step_limit = False

        # 构建初始消息
        system_prompt = self._build_system_prompt()
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"任务：{task}"},
        ]

        for step_num in range(1, self.max_steps + 1):
            # Think: 调用 LLM
            response = self.llm.chat(messages, agent_type=self.name)
            token_used += len(response) // 2  # 粗略估算

            # 解析 LLM 响应
            parsed = self._parse_response(response)
            thought = parsed.get("thought", "")
            action = parsed.get("action")
            final_answer = parsed.get("final_answer")

            # 如果有最终答案，结束循环
            if final_answer is not None:
                steps.append(
                    StepRecord(
                        step=step_num,
                        thought=thought,
                        action=None,
                        observation=None,
                        tool_name=None,
                    )
                )
                break

            # Act: 执行工具调用
            if action:
                tool_name = action.get("tool", "")
                tool_args = action.get("args", {})
                tool = self.tool_registry.get(tool_name)

                if tool is None:
                    # 未知工具
                    error_msg = f"未知工具: {tool_name}"
                    observation = f"错误: {error_msg}"
                    tool_errors.append({"step": step_num, "tool": tool_name, "error": error_msg})
                    steps.append(
                        StepRecord(
                            step=step_num,
                            thought=thought,
                            action=action,
                            observation=observation,
                            tool_name=tool_name,
                            error=error_msg,
                        )
                    )
                else:
                    # 执行工具
                    try:
                        observation = tool.execute(**tool_args)
                        steps.append(
                            StepRecord(
                                step=step_num,
                                thought=thought,
                                action=action,
                                observation=observation,
                                tool_name=tool_name,
                            )
                        )
                    except Exception as e:
                        error_msg = str(e)
                        observation = f"工具执行错误: {error_msg}"
                        tool_errors.append(
                            {"step": step_num, "tool": tool_name, "error": error_msg}
                        )
                        steps.append(
                            StepRecord(
                                step=step_num,
                                thought=thought,
                                action=action,
                                observation=observation,
                                tool_name=tool_name,
                                error=error_msg,
                            )
                        )

                # Observe: 将观察结果添加到消息历史
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"观察结果:\n{observation}"})

        else:
            # 循环正常结束但未得到最终答案（达到步数上限）
            hit_step_limit = True
            final_answer = f"达到步数上限 ({self.max_steps} 步)，任务未完成"

        # 构建工作记忆
        working_memory = {
            self.name: {
                "steps": [
                    {
                        "step": s.step,
                        "thought": s.thought,
                        "action": s.action,
                        "observation": s.observation,
                        "tool_name": s.tool_name,
                        "error": s.error,
                    }
                    for s in steps
                ]
            }
        }

        return {
            **state,
            "final_answer": final_answer,
            "working_memory": {**state.get("working_memory", {}), **working_memory},
            "step_count": len(steps),
            "hit_step_limit": hit_step_limit,
            "tool_errors": tool_errors,
            "token_used": token_used,
        }

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        tool_descriptions = self.tool_registry.get_tool_descriptions()

        return f"""你是一个 ReAct Agent，名称为 {self.name}。

你可以使用以下工具：
{tool_descriptions}

## 输出格式

每次响应必须是 JSON 格式：

1. 如果需要调用工具：
{{"thought": "你的思考过程", "action": {{"tool": "工具名", "args": {{"参数名": "值"}}}}}}

2. 如果任务完成：
{{"thought": "你的思考过程", "action": null, "final_answer": "最终答案"}}

## 规则

1. 每次只调用一个工具
2. 仔细思考后再行动
3. 如果工具执行失败，分析错误并尝试其他方案
4. 当任务完成时，返回 final_answer"""

    def _parse_response(self, response: str) -> dict[str, Any]:
        """解析 LLM 响应"""
        # 尝试清理响应内容
        text = response.strip()

        # 移除可能的 <think> 标记
        if "<think>" in text and "</think>" in text:
            start = text.find("<think>")
            end = text.find("</think>") + 7
            text = text[:start] + text[end:]

        # 尝试解析 JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试提取 JSON 部分
            try:
                # 查找第一个 { 和最后一个 }
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end > start:
                    return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        # 解析失败，返回空结果
        return {"thought": text, "action": None, "final_answer": None}
