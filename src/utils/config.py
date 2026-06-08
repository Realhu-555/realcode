"""配置管理 — 使用 pydantic-settings 集中管理"""

from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用全局配置"""

    # ── LLM 配置 ──────────────────────────────────────
    deepseek_api_key: str = ""
    minimax_api_key: str = ""
    openai_api_key: str = ""

    # ── 沙箱配置 ──────────────────────────────────────
    sandbox_timeout: int = 60
    sandbox_max_memory: str = "512m"

    # ── 日志配置 ──────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] = "text"

    # ── 应用配置 ──────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}


# 全局单例
settings = Settings()
