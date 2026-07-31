"""视觉分析模块 — OCR 图片文字提取

后端自动选择（优先级）：
  1. PaddleOCR  (本地免费，中英文)
  2. pytesseract (Tesseract OCR)
  3. MiMo V2.5   (需要 MIMO_API_KEY)

策略 Agent 始终拿到文字——图片在进入分析前已完成 OCR。

首次使用 PaddleOCR 会自动下载模型（约 50MB），之后缓存到 ~/.paddlex/。
"""

import base64
import io
import tempfile
from pathlib import Path
from typing import Any

_ocr_backend: str | None = None
_ocr_instance: Any = None


def _detect_backend() -> str:
    """自动检测可用的 OCR 后端"""
    # 1. PaddleOCR
    try:
        from paddleocr import PaddleOCR  # noqa: F401
        return "paddleocr"
    except ImportError:
        pass

    # 2. Tesseract
    try:
        import pytesseract  # noqa: F401
        pytesseract.get_tesseract_version()
        return "tesseract"
    except Exception:
        pass

    # 3. MiMo V2.5
    import os
    if os.getenv("MIMO_API_KEY"):
        return "mimo"

    return "none"


def _get_ocr():
    global _ocr_instance, _ocr_backend
    if _ocr_instance is not None:
        return _ocr_instance

    _ocr_backend = _detect_backend()

    if _ocr_backend == "paddleocr":
        from paddleocr import PaddleOCR
        _ocr_instance = PaddleOCR(lang="ch")
    elif _ocr_backend == "tesseract":
        import pytesseract
        _ocr_instance = pytesseract
    elif _ocr_backend == "mimo":
        from src.llm.provider import LLMProvider
        _ocr_instance = LLMProvider()

    return _ocr_instance


def _ocr_paddle(image_bytes: bytes) -> str:
    ocr = _get_ocr()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(image_bytes)
        tmp_path = f.name
    try:
        results = ocr.predict(tmp_path)
        lines = []
        for item in results:
            # PaddleOCR 3.x 返回格式: [{"rec_text": "...", "rec_score": 0.99}, ...]
            if isinstance(item, dict):
                text = item.get("rec_text", "")
                score = item.get("rec_score", 0)
                if text and score > 0.5:
                    lines.append(text)
            elif isinstance(item, list):
                for b in item:
                    if isinstance(b, list) and len(b) >= 2:
                        text = b[1][0] if isinstance(b[1], (list, tuple)) else str(b[1])
                        lines.append(str(text))
        return "\n".join(lines)
    except Exception as e:
        return f"[PaddleOCR 失败: {e}]"
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _ocr_tesseract(image_bytes: bytes) -> str:
    import pytesseract
    from PIL import Image
    img = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(img, lang="chi_sim+eng")


def _ocr_mimo(image_bytes: bytes) -> str:
    llm = _get_ocr()
    b64 = base64.b64encode(image_bytes).decode()
    data_url = f"data:image/png;base64,{b64}"
    return llm.chat_multimodal("请提取这张图片中的所有文字，不做任何解释。", [data_url])


async def describe_images(
    image_data_urls: list[str],
    product_name: str = "",
) -> str:
    """从图片中提取文字，注入策略分析

    调用时机：用户在提交表单时上传图片
    返回值注入 PromptContext.image_descriptions
    """
    if not image_data_urls:
        return ""

    backend = _detect_backend()
    if backend == "none":
        return (
            "（图片已上传，但未检测到 OCR 引擎。安装方式：\n"
            "- pip install paddleocr (推荐，免费本地)\n"
            "- 或 安装 Tesseract + pip install pytesseract\n"
            "- 或 设置 MIMO_API_KEY 环境变量使用 MiMo V2.5）"
        )

    descriptions = []
    for i, url in enumerate(image_data_urls, 1):
        try:
            _, b64_data = url.split(",", 1)
            image_bytes = base64.b64decode(b64_data)
        except Exception:
            descriptions.append(f"### 图片 {i}\n（图片解码失败）")
            continue

        try:
            if backend == "paddleocr":
                text = _ocr_paddle(image_bytes)
            elif backend == "tesseract":
                text = _ocr_tesseract(image_bytes)
            elif backend == "mimo":
                text = _ocr_mimo(image_bytes)
            else:
                text = ""

            if text and text.strip():
                descriptions.append(f"### 图片 {i} OCR 文字\n```\n{text.strip()}\n```")
            else:
                descriptions.append(f"### 图片 {i}\n（未识别到文字）")
        except Exception as e:
            descriptions.append(f"### 图片 {i}\n（OCR 失败: {e}）")

    suffix = ""
    if product_name:
        suffix = f"\n以上是从「{product_name}」相关图片中提取的文字信息，请结合这些内容制定策略。"

    return "\n\n".join(descriptions) + suffix
