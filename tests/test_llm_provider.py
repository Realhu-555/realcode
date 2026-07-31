"""LLMProvider 单元测试"""

import os
from unittest.mock import MagicMock, patch

from src.llm.provider import LLMProvider


def test_model_map_exists():
    """MODEL_MAP 存在且非空"""
    assert len(LLMProvider.MODEL_MAP) > 0


def test_all_content_agents_have_deepseek_model():
    """内容平台 Agent 全部使用 DeepSeek"""
    agents = ["celve", "gongzhonghao", "zhihu", "xiaohongshu", "shenjiao", "export"]
    for agent_type in agents:
        model = LLMProvider.MODEL_MAP[agent_type]
        assert "deepseek" in model, f"{agent_type}: {model}"


def test_vision_model():
    """视觉模型配置"""
    assert LLMProvider.MODEL_MAP["vision"] == "mimo:mimo-v2.5"


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
        result = provider.chat([{"role": "user", "content": "Hi"}], agent_type="celve")

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
        provider.chat(messages, agent_type="shenjiao")

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"] == messages
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["max_tokens"] == 4096


def test_chat_retry_on_empty():
    """空响应时重试一次"""
    with patch("src.llm.provider.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_response_empty = MagicMock()
        mock_response_empty.choices = [MagicMock()]
        mock_response_empty.choices[0].message.content = ""
        mock_response_ok = MagicMock()
        mock_response_ok.choices = [MagicMock()]
        mock_response_ok.choices[0].message.content = "retry worked"
        mock_client.chat.completions.create.side_effect = [
            mock_response_empty,
            mock_response_ok,
        ]
        mock_openai_cls.return_value = mock_client

        provider = LLMProvider()
        result = provider.chat([{"role": "user", "content": "test"}], agent_type="gongzhonghao")

        assert result == "retry worked"
        assert mock_client.chat.completions.create.call_count == 2


def test_strip_thinking_blocks():
    """移除 <think> 推理块"""
    from src.llm.provider import _strip_thinking

    text = "<think>这是推理</think>回答内容"
    assert _strip_thinking(text) == "回答内容"

    text_no_think = "正常回复"
    assert _strip_thinking(text_no_think) == "正常回复"

    assert _strip_thinking("") == ""


def test_mimo_client_lazy_loading():
    """MiMo 客户端懒加载"""
    from src.llm.provider import LLMProvider

    p = LLMProvider()
    assert p._mimo_client is None
    # 不实际调用以避免网络请求


def test_chat_multimodal_signature():
    """多模态方法签名"""
    from src.llm.provider import LLMProvider

    p = LLMProvider()
    assert callable(p.chat_multimodal)
    # text_prompt + image_data_urls -> str
