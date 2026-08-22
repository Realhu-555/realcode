"""配置模块单元测试"""

import os
from unittest.mock import patch

from src.utils.config import Settings


def test_settings_default_values():
    """默认配置值正确"""
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings(_env_file=None)  # 排除 .env，只测代码默认值
        assert settings.sandbox_timeout == 60
        assert settings.sandbox_max_memory == "512m"
        assert settings.log_level == "INFO"
        assert settings.log_format == "text"
        assert settings.app_env == "development"
        assert settings.debug is False


def test_settings_from_env():
    """从环境变量加载配置"""
    env_vars = {
        "DEEPSEEK_API_KEY": "test-ds-key",
        "MINIMAX_API_KEY": "test-mm-key",
        "SANDBOX_TIMEOUT": "120",
        "LOG_LEVEL": "DEBUG",
        "APP_ENV": "production",
        "DEBUG": "true",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        settings = Settings()
        assert settings.deepseek_api_key == "test-ds-key"
        assert settings.minimax_api_key == "test-mm-key"
        assert settings.sandbox_timeout == 120
        assert settings.log_level == "DEBUG"
        assert settings.app_env == "production"
        assert settings.debug is True


def test_settings_case_insensitive():
    """环境变量大小写不敏感"""
    env_vars = {"log_level": "WARNING"}
    with patch.dict(os.environ, env_vars, clear=False):
        settings = Settings()
        assert settings.log_level == "WARNING"
