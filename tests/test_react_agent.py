"""ReAct Agent 模式测试 - TDD: 先写测试，再写实现

ReAct 模式核心逻辑：
1. Think: 分析当前状态，决定下一步行动
2. Act: 调用工具执行操作
3. Observe: 观察工具返回结果
4. 重复直到完成或达到步数上限

步数上限：15 步
"""

from unittest.mock import MagicMock, patch

import pytest
from src.orchestrator.state import create_output_artifact

# ========================================================================
# 工具系统测试
# ========================================================================


class TestToolRegistry:
    """工具注册表测试"""

    def test_register_tool(self) -> None:
        """注册工具到注册表"""
        from src.agents.tools import ToolRegistry

        registry = ToolRegistry()
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "测试工具"

        registry.register(mock_tool)

        assert "test_tool" in registry.tools

    def test_get_tool_returns_registered(self) -> None:
        """获取已注册的工具"""
        from src.agents.tools import ToolRegistry

        registry = ToolRegistry()
        mock_tool = MagicMock()
        mock_tool.name = "file_read"

        registry.register(mock_tool)

        result = registry.get("file_read")
        assert result is mock_tool

    def test_get_tool_returns_none_for_unknown(self) -> None:
        """获取未注册的工具返回 None"""
        from src.agents.tools import ToolRegistry

        registry = ToolRegistry()
        result = registry.get("unknown_tool")
        assert result is None

    def test_list_tools(self) -> None:
        """列出所有已注册工具"""
        from src.agents.tools import ToolRegistry

        registry = ToolRegistry()
        mock_tool1 = MagicMock()
        mock_tool1.name = "tool1"
        mock_tool2 = MagicMock()
        mock_tool2.name = "tool2"

        registry.register(mock_tool1)
        registry.register(mock_tool2)

        tools = registry.list_tools()
        assert "tool1" in tools
        assert "tool2" in tools


# ========================================================================
# BaseTool 接口测试
# ========================================================================


class TestBaseTool:
    """BaseTool 抽象接口测试"""

    def test_cannot_instantiate_directly(self) -> None:
        """不能直接实例化 BaseTool"""
        from src.agents.tools import BaseTool

        with pytest.raises(TypeError):
            BaseTool()  # type: ignore


# ========================================================================
# ReActAgent 循环逻辑测试
# ========================================================================


class TestReActAgent:
    """ReAct Agent 核心循环测试"""

    @patch("src.agents.react.LLMProvider")
    def test_single_step_completion(self, mock_llm_cls: MagicMock) -> None:
        """单步完成任务 - LLM 直接给出最终答案"""
        from src.agents.react import ReActAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        # LLM 第一次调用就给出完成标记
        mock_llm.chat.return_value = (
            '{"thought": "任务很简单", "action": null, "final_answer": "完成"}'
        )

        agent = ReActAgent(name="test", tools=[])
        state = {
            "current_stage": "backend",
            "messages": [],
        }

        result = agent.run(state, task="生成一个简单的 hello world")

        assert result["final_answer"] is not None
        assert result["step_count"] == 1

    @patch("src.agents.react.LLMProvider")
    def test_multi_step_completion(self, mock_llm_cls: MagicMock) -> None:
        """多步完成任务 - 需要调用工具"""
        from src.agents.react import ReActAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        # 模拟 LLM 的多轮响应
        mock_llm.chat.side_effect = [
            '{"thought": "需要读取文件", "action": {"tool": "file_read", "args": {"path": "config.py"}}}',
            '{"thought": "文件内容已获取，需要分析", "action": null, "final_answer": "分析完成"}',
        ]

        # Mock 工具
        mock_tool = MagicMock()
        mock_tool.name = "file_read"
        mock_tool.execute.return_value = "config content"

        agent = ReActAgent(name="test", tools=[mock_tool])
        state = {
            "current_stage": "backend",
            "messages": [],
        }

        result = agent.run(state, task="分析配置文件")

        assert result["final_answer"] is not None
        assert result["step_count"] == 2
        mock_tool.execute.assert_called_once_with(path="config.py")

    @patch("src.agents.react.LLMProvider")
    def test_step_limit_enforced(self, mock_llm_cls: MagicMock) -> None:
        """步数上限强制停止"""
        from src.agents.react import ReActAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        # 模拟 LLM 始终需要更多步骤（无限循环）
        mock_llm.chat.return_value = (
            '{"thought": "还需要继续", "action": {"tool": "file_read", "args": {"path": "x.py"}}}'
        )

        mock_tool = MagicMock()
        mock_tool.name = "file_read"
        mock_tool.execute.return_value = "content"

        agent = ReActAgent(name="test", tools=[mock_tool], max_steps=5)
        state = {
            "current_stage": "backend",
            "messages": [],
        }

        result = agent.run(state, task="复杂任务")

        # 应该在 5 步时停止
        assert result["step_count"] == 5
        assert result["hit_step_limit"] is True

    @patch("src.agents.react.LLMProvider")
    def test_tool_execution_error_handling(self, mock_llm_cls: MagicMock) -> None:
        """工具执行错误处理"""
        from src.agents.react import ReActAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        # LLM 先尝试调用工具
        mock_llm.chat.side_effect = [
            '{"thought": "尝试读取文件", "action": {"tool": "file_read", "args": {"path": "missing.py"}}}',
            '{"thought": "文件不存在，换个方案", "action": null, "final_answer": "文件不存在，跳过"}',
        ]

        # 工具抛出异常
        mock_tool = MagicMock()
        mock_tool.name = "file_read"
        mock_tool.execute.side_effect = FileNotFoundError("文件不存在")

        agent = ReActAgent(name="test", tools=[mock_tool])
        state = {
            "current_stage": "backend",
            "messages": [],
        }

        result = agent.run(state, task="读取文件")

        # 应该优雅处理错误，继续执行
        assert result["final_answer"] is not None
        assert "tool_errors" in result
        assert len(result["tool_errors"]) == 1

    @patch("src.agents.react.LLMProvider")
    def test_unknown_tool_handling(self, mock_llm_cls: MagicMock) -> None:
        """调用未知工具时的处理"""
        from src.agents.react import ReActAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        mock_llm.chat.side_effect = [
            '{"thought": "尝试未知工具", "action": {"tool": "unknown_tool", "args": {}}}',
            '{"thought": "工具不存在，换方案", "action": null, "final_answer": "完成"}',
        ]

        agent = ReActAgent(name="test", tools=[])  # 没有注册任何工具
        state = {
            "current_stage": "backend",
            "messages": [],
        }

        result = agent.run(state, task="测试")

        assert result["final_answer"] is not None
        assert len(result["tool_errors"]) == 1
        assert "unknown" in result["tool_errors"][0]["error"].lower()

    @patch("src.agents.react.LLMProvider")
    def test_observation_passed_to_llm(self, mock_llm_cls: MagicMock) -> None:
        """工具执行结果作为观察传递给 LLM"""
        from src.agents.react import ReActAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        mock_llm.chat.side_effect = [
            '{"thought": "调用工具", "action": {"tool": "terminal", "args": {"cmd": "ls"}}}',
            '{"thought": "看到文件列表", "action": null, "final_answer": "完成"}',
        ]

        mock_tool = MagicMock()
        mock_tool.name = "terminal"
        mock_tool.execute.return_value = "file1.py\nfile2.py"

        agent = ReActAgent(name="test", tools=[mock_tool])
        state = {
            "current_stage": "backend",
            "messages": [],
        }

        agent.run(state, task="列出文件")

        # 检查第二次调用 LLM 时是否包含观察结果
        second_call_args = mock_llm.chat.call_args_list[1]
        messages = second_call_args[0][0]
        assert any("file1.py" in msg["content"] for msg in messages)


# ========================================================================
# ReAct Agent 与 State 集成测试
# ========================================================================


class TestReActAgentStateIntegration:
    """ReAct Agent 与状态系统集成测试"""

    @patch("src.agents.react.LLMProvider")
    def test_working_memory_stored_in_state(self, mock_llm_cls: MagicMock) -> None:
        """工作记忆存储在 state 中"""
        from src.agents.react import ReActAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        mock_llm.chat.side_effect = [
            '{"thought": "第一步", "action": {"tool": "file_read", "args": {"path": "x.py"}}}',
            '{"thought": "第二步", "action": null, "final_answer": "完成"}',
        ]

        mock_tool = MagicMock()
        mock_tool.name = "file_read"
        mock_tool.execute.return_value = "content"

        agent = ReActAgent(name="backend", tools=[mock_tool])
        state = {
            "current_stage": "backend",
            "messages": [],
        }

        result = agent.run(state, task="测试")

        # 验证 working_memory 被存储
        assert "working_memory" in result
        memory = result["working_memory"]
        assert "backend" in memory
        assert len(memory["backend"]["steps"]) == 2

    @patch("src.agents.react.LLMProvider")
    def test_token_budget_respected(self, mock_llm_cls: MagicMock) -> None:
        """token 预算控制 - 验证 token_used 被记录"""
        from src.agents.react import ReActAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        # 模拟正常输出
        response = '{"thought": "分析任务", "action": null, "final_answer": "完成"}'
        mock_llm.chat.return_value = response

        agent = ReActAgent(name="test", tools=[], token_budget=1000)
        state = {
            "current_stage": "backend",
            "messages": [],
        }

        result = agent.run(state, task="测试")

        # 验证 token_used 被记录
        assert "token_used" in result
        assert result["token_used"] > 0


# ========================================================================
# ReAct 模式与 Agent 集成测试
# ========================================================================


class TestReActAgentModeSelection:
    """测试不同 Agent 选择 ReAct 模式"""

    @patch("src.agents.react.LLMProvider")
    def test_backend_agent_uses_react(self, mock_llm_cls: MagicMock) -> None:
        """Backend Agent 使用 ReAct 模式"""
        from src.agents.backend_react import BackendReActAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        mock_llm.chat.return_value = (
            '{"thought": "生成代码", "action": null, "final_answer": "def hello(): pass"}'
        )

        agent = BackendReActAgent()
        state = {
            "tech_plan": create_output_artifact(content="技术方案"),
            "backend_code": None,
            "current_stage": "backend",
            "messages": [],
        }

        result = agent.run(state)

        assert result["backend_code"] is not None

    @patch("src.agents.react.LLMProvider")
    def test_frontend_agent_uses_react(self, mock_llm_cls: MagicMock) -> None:
        """Frontend Agent 使用 ReAct 模式"""
        from src.agents.frontend_react import FrontendReActAgent

        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm

        mock_llm.chat.return_value = '{"thought": "生成组件", "action": null, "final_answer": "export default function App() {}"}'

        agent = FrontendReActAgent()
        state = {
            "tech_plan": create_output_artifact(content="技术方案"),
            "frontend_code": None,
            "current_stage": "frontend",
            "messages": [],
        }

        result = agent.run(state)

        assert result["frontend_code"] is not None
