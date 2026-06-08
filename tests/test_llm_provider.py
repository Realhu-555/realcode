"""LLMProvider 单元测试"""

import os
from unittest.mock import MagicMock, patch

from src.llm.provider import LLMProvider


def test_model_map_has_all_agent_types():
    """所有 Agent 类型都有对应的模型配置"""
    expected_agents = [
        "requirement",
        "architect",
        "backend",
        "frontend",
        "tester",
        "deployer",
        "documenter",
    ]
    for agent_type in expected_agents:
        assert agent_type in LLMProvider.MODEL_MAP


def test_chat_routes_to_correct_provider():
    """不同的 agent_type 路由到不同的 provider"""
    with patch("src.llm.provider.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response from llm"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        provider = LLMProvider()

        # DeepSeek 路由
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-ds-key"}):
            result = provider.chat([{"role": "user", "content": "hello"}], agent_type="architect")
            # DeepSeek client 被调用，base_url 应该是 deepseek 的
            assert result == "response from llm"

        # MiniMax 路由
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-mm-key"}):
            result = provider.chat([{"role": "user", "content": "hello"}], agent_type="requirement")
            assert result == "response from llm"


def test_chat_returns_string():
    """chat() 返回字符串"""
    with patch("src.llm.provider.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello, world!"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        provider = LLMProvider()
        result = provider.chat([{"role": "user", "content": "Hi"}], agent_type="backend")

        assert isinstance(result, str)
        assert result == "Hello, world!"


def test_chat_passes_correct_parameters():
    """chat() 传递正确的参数给 API"""
    with patch("src.llm.provider.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        provider = LLMProvider()
        messages = [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]
        provider.chat(messages, agent_type="tester")

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"] == messages
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["max_tokens"] == 4096
