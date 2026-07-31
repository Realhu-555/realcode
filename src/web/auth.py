"""简单 API Key 认证 — 无需注册，Key 即身份

请求头: X-API-Key: <your-key>
首次使用任意 Key 自动创建用户，同一 Key 下所有项目隔离。

部署时建议设置环境变量：
  API_KEYS=key1,key2,key3   # 允许的 Key 列表（留空 = 任意 Key 通过）
"""

import os

from fastapi import Header, HTTPException

_ALLOWED_KEYS: set[str] | None = None


def get_user_id(x_api_key: str = Header(default="", alias="X-API-Key")) -> str:
    """从请求头提取用户 ID"""
    key = x_api_key.strip()
    if not key:
        raise HTTPException(status_code=401, detail="缺少 X-API-Key 请求头")

    global _ALLOWED_KEYS
    if _ALLOWED_KEYS is None:
        env = os.getenv("API_KEYS", "")
        _ALLOWED_KEYS = set(k.strip() for k in env.split(",") if k.strip()) if env else None

    if _ALLOWED_KEYS and key not in _ALLOWED_KEYS:
        raise HTTPException(status_code=403, detail="API Key 未授权")

    # Key 经过哈希作为 user_id（不存明文）
    import hashlib
    return hashlib.sha256(key.encode()).hexdigest()[:16]
