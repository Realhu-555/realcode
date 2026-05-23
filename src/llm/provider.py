"""统一 LLM Provider"""
import os
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# 自动加载项目根目录的 .env
_env_path = Path(__file__).parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# MiniMax 输出可能包含 <think> 推理块，自动清理
_THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)


def _strip_thinking(text: str) -> str:
    """移除 MiniMax 的 <think> 推理块"""
    if not text:
        return text
    return _THINK_PATTERN.sub("", text).strip()


class LLMProvider:
    """统一的 LLM 调用接口"""

    MODEL_MAP = {
        "requirement": "deepseek:deepseek-ai/deepseek-v4-pro",  # MiniMax 不跟进对话格式，换 DeepSeek
        "architect": "deepseek:deepseek-ai/deepseek-v4-pro",  # 技术推理要求高
        "backend": "deepseek:deepseek-ai/deepseek-v4-pro",    # 代码质量要求最高
        "frontend": "minimax:MiniMax-M2.7",       # 分担 DeepSeek 压力
        "tester": "minimax:MiniMax-M2.7",         # 测试用例生成
        "deployer": "minimax:MiniMax-M2.7",
        "documenter": "minimax:MiniMax-M2.7",
    }

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        self.deepseek_client = OpenAI(
            api_key=os.getenv("NVIDIA_API_KEY", ""),
            base_url="https://integrate.api.nvidia.com/v1",
        )
        self.minimax_client = OpenAI(
            api_key=os.getenv("MINIMAX_API_KEY", ""),
            base_url="https://api.minimax.chat/v1",
        )

    def chat(self, messages: list[dict], agent_type: str = "requirement") -> str:
        """发消息给 LLM，返回文本。空响应时重试一次。自动清理 <think> 块。"""
        model_key = self.MODEL_MAP.get(agent_type, "deepseek:deepseek-v4-pro")
        provider, model = model_key.split(":", 1)
        content = self._call_openai_compatible(messages, model, provider)
        if not content:
            content = self._call_openai_compatible(messages, model, provider)
        return _strip_thinking(content)

    def _call_openai_compatible(self, messages, model, provider):
        """OpenAI 兼容接口（DeepSeek / MiniMax / OpenAI）"""
        if provider == "deepseek":
            client = self.deepseek_client
        elif provider == "minimax":
            client = self.minimax_client
        else:
            client = self.openai_client
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
        )
        return response.choices[0].message.content
