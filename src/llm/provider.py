"""统一 LLM Provider"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

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
    """统一的 LLM 调用接口

    视觉模型：MiMo V2.5（小米官方，支持图片理解）
    注册 API Key：https://platform.xiaomimimo.com/
    配置方式（.env）：
      MIMO_API_KEY=<your_key>          # 从 platform.xiaomimimo.com 获取
    """

    MODEL_MAP = {
        # 原有 Agent（向后兼容）
        "requirement": "deepseek:deepseek-v4-pro",
        "architect": "deepseek:deepseek-v4-pro",
        "backend": "deepseek:deepseek-v4-pro",
        "frontend": "deepseek:deepseek-v4-pro",
        "tester": "deepseek:deepseek-v4-pro",
        "deployer": "deepseek:deepseek-v4-pro",
        "documenter": "deepseek:deepseek-v4-pro",
        # 营销内容 Agent — 全部 DeepSeek
        "celve": "deepseek:deepseek-v4-pro",
        "gongzhonghao": "deepseek:deepseek-v4-pro",
        "zhihu": "deepseek:deepseek-v4-pro",
        "xiaohongshu": "deepseek:deepseek-v4-pro",
        "shenjiao": "deepseek:deepseek-v4-pro",
        "export": "deepseek:deepseek-v4-pro",
        # 视觉模型 — MiMo V2.5
        "vision": "mimo:mimo-v2.5",
    }

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        self.deepseek_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url="https://api.deepseek.com",
        )
        self._mimo_client = None

    @property
    def mimo_client(self):
        """懒加载 MiMo 视觉客户端

        小米官方 API：https://api.xiaomimimo.com
        也可通过 MIMO_BASE_URL 环境变量切换第三方代理
        """
        if self._mimo_client is None:
            base = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
            key = os.getenv("MIMO_API_KEY", "")
            self._mimo_client = OpenAI(api_key=key, base_url=base)
        return self._mimo_client

    def chat(self, messages: list[dict], agent_type: str = "requirement") -> str:
        """发消息给 LLM，返回文本。空响应时重试一次。自动清理 <think> 块。"""
        model_key = self.MODEL_MAP.get(agent_type, "deepseek:deepseek-v4-pro")
        provider, model = model_key.split(":", 1)
        content = self._call_openai_compatible(messages, model, provider)
        if not content:
            content = self._call_openai_compatible(messages, model, provider)
        return _strip_thinking(content)

    def chat_multimodal(self, text_prompt: str, image_data_urls: list[str]) -> str:
        """多模态视觉理解 —— MiMo V2.5 分析图片

        Args:
            text_prompt: 给视觉模型的文字指令
            image_data_urls: base64 编码的图片列表
                （格式：data:image/png;base64,...）

        Returns:
            视觉模型对图片的文字描述
        """
        content_parts = [{"type": "text", "text": text_prompt}]
        for url in image_data_urls:
            content_parts.append(
                {"type": "image_url", "image_url": {"url": url}}
            )

        response = self.mimo_client.chat.completions.create(
            model="mimo-v2.5",
            messages=[{"role": "user", "content": content_parts}],
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""

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
