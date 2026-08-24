"""视觉分析模块 — MiMo V2.5 图片理解

设计理念：
- 图片在进入内容生成前已完成视觉理解
- 策略 Agent 拿到的始终是文字（图片已转为描述）
- 认知偏差：视觉理解模型独立于内容生成模型

启用方式 (.env):
  OPENROUTER_API_KEY=sk-or-v1-...    # 从 https://openrouter.ai/keys 免费获取
  或
  MIMO_API_KEY=sk-...                # 从 https://platform.xiaomimimo.com/ 获取

优先级: OpenRouter Key > MiMo 官方 Key > 无（优雅降级）

备用 OCR 后端（pip install easyocr 即可启用，零 API 费用）:
  OCR_BACKEND=easyocr
"""

import base64
import os
from typing import Any

_vision_client: Any = None
_vision_model: str | None = None


def _get_vision():
    """懒加载视觉客户端"""
    global _vision_client, _vision_model

    if _vision_client is not None:
        return _vision_client

    from openai import OpenAI

    # 1. OpenRouter（推荐，免费注册）
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    if openrouter_key:
        _vision_client = OpenAI(
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
        )
        _vision_model = "xiaomi/mimo-v2.5-20260422"
        return _vision_client

    # 2. MiMo 官方
    mimo_key = os.getenv("MIMO_API_KEY", "")
    if mimo_key:
        _vision_client = OpenAI(
            api_key=mimo_key,
            base_url="https://api.xiaomimimo.com/v1",
        )
        _vision_model = "mimo-v2.5"
        return _vision_client

    # 3. OCR
    if os.getenv("OCR_BACKEND") == "easyocr":
        _vision_model = "easyocr"
        return None

    # 4. 无可用后端
    _vision_model = "none"
    return None


async def describe_images(
    image_data_urls: list[str],
    product_name: str = "",
) -> str:
    """用 MiMo V2.5 理解图片内容，返回文字描述

    调用时机：用户上传图片 → MiMo 分析 → 文字注入策略
    """
    if not image_data_urls:
        return ""

    client = _get_vision()
    model = _vision_model

    if model == "none":
        return (
            "（图片已上传，但未配置视觉模型。两种启用方式：\n"
            "1. 免费方案：去 https://openrouter.ai/keys 注册，获取 Key 后加到 .env：\n"
            "   OPENROUTER_API_KEY=sk-or-v1-...\n"
            "2. OCR 方案：pip install easyocr，然后 .env 设置 OCR_BACKEND=easyocr\n"
            "3. 官方方案：去 https://platform.xiaomimimo.com/ 注册，获取 Key 后加到 .env：\n"
            "   MIMO_API_KEY=sk-..."
        )

    if model == "easyocr":
        return await _ocr_easyocr(image_data_urls, product_name)

    # MiMo V2.5 视觉理解
    prompt = (
        "请从营销角度分析以下图片。重点关注：产品名称、功能卖点、使用场景、"
        "品牌调性、与竞品的差异化元素。提取图片中的所有文字。"
    )
    if product_name:
        prompt += f"\n\n产品名称：{product_name}"

    descriptions = []
    for i, url in enumerate(image_data_urls, 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"{prompt}\n\n（第 {i}/{len(image_data_urls)} 张图片）",
                            },
                            {"type": "image_url", "image_url": {"url": url}},
                        ],
                    }
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            desc = response.choices[0].message.content or ""
            if desc.strip():
                descriptions.append(f"### 图片 {i}\n{desc.strip()}")
            else:
                descriptions.append(f"### 图片 {i}\n（MiMo 未返回有效描述）")
        except Exception as e:
            descriptions.append(f"### 图片 {i}\n（视觉分析失败: {e}）")

    return "\n\n".join(descriptions)


async def _ocr_easyocr(image_data_urls: list[str], product_name: str) -> str:
    """EasyOCR 本地文字提取（无需 API Key）"""
    import io
    import warnings

    import easyocr

    warnings.filterwarnings("ignore")
    reader = easyocr.Reader(["ch_sim", "en"], gpu=False)

    descriptions = []
    for i, url in enumerate(image_data_urls, 1):
        try:
            _, b64_data = url.split(",", 1)
            from PIL import Image

            img = Image.open(io.BytesIO(base64.b64decode(b64_data)))
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                img.save(f)
                tmp = f.name
            results = reader.readtext(tmp)
            import os as _os

            _os.unlink(tmp)

            if results:
                lines = [f"[{conf:.0%}] {text}" for _, text, conf in results if conf > 0.3]
                descriptions.append(f"### 图片 {i} OCR 文字\n```\n" + "\n".join(lines) + "\n```")
            else:
                descriptions.append(f"### 图片 {i}\n（未识别到文字）")
        except Exception as e:
            descriptions.append(f"### 图片 {i}\n（OCR 失败: {e}）")

    suffix = (
        f"\n以上是从「{product_name}」相关图片中提取的信息，请结合这些内容制定策略。"
        if product_name
        else ""
    )
    return "\n\n".join(descriptions) + suffix
