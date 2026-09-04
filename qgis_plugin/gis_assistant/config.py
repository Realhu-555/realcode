"""插件配置：本地服务端口与访问令牌（存 QSettings，跨会话保留）。"""

from __future__ import annotations

import secrets

from PyQt5.QtCore import QSettings

_ORG = "gis-assistant"
_APP = "live-engine"
_KEY_PORT = "plugins/gis_assistant/port"
_KEY_TOKEN = "plugins/gis_assistant/token"

DEFAULT_PORT = 8756


def _settings() -> QSettings:
    return QSettings(_ORG, _APP)


def get_server_port() -> int:
    """读取端口；非法/未配置时返回默认端口。"""
    settings = _settings()
    value = settings.value(_KEY_PORT, DEFAULT_PORT)
    try:
        return int(value)
    except (TypeError, ValueError):
        return DEFAULT_PORT


def get_token() -> str:
    """读取令牌；不存在则生成一个并持久化。"""
    settings = _settings()
    token = settings.value(_KEY_TOKEN, "")
    if not token:
        token = secrets.token_hex(16)
        settings.setValue(_KEY_TOKEN, token)
    return str(token)
