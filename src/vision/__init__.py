"""视觉分析模块 — MiMo V2.5 图片理解

设计理念：
- 图片在进入内容生成前已完成视觉理解
- 策略 Agent 拿到的始终是文字（图片已被 MiMo 转为描述）
- 认知偏差：视觉理解模型独立于内容生成模型，各用各的优势

启用方式 (.env):
  MIMO_API_KEY=sk-...    # 从 https://platform.xiaomimimo.com/ 获取
"""

from src.llm.provider import LLMProvider

llm = LLMProvider()


async def describe_images(
    image_data_urls: list[str],
    product_name: str = "",
) -> str:
    """用 MiMo V2.5 理解图片内容，返回文字描述

    调用时机：用户在提交表单的同时上传了图片
    返回值会注入到 PromptContext.image_descriptions

    Args:
        image_data_urls: base64 图片 URL 列表
        product_name: 产品名称（辅助视觉模型聚焦相关细节）

    Returns:
        多图片的综合文字描述（Markdown 格式）
    """
    if not image_data_urls:
        return ""

    prompt = (
        f"请仔细观察以下图片，从营销角度描述图片内容。"
        f"重点关注：产品外观、使用场景、视觉风格、目标用户特征、"
        f"品牌调性线索、与竞品的差异化视觉元素。"
    )
    if product_name:
        prompt += f"\n\n产品名称：{product_name}"

    descriptions = []
    for i, url in enumerate(image_data_urls, 1):
        img_prompt = f"{prompt}\n\n（第 {i}/{len(image_data_urls)} 张图片）"
        desc = llm.chat_multimodal(img_prompt, [url])
        if desc:
            descriptions.append(f"### 图片 {i}\n{desc}")

    return "\n\n".join(descriptions)
