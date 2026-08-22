"""日志模块单元测试"""

import logging
from unittest.mock import MagicMock, patch

from src.utils.logger import setup_logger


def test_setup_logger_creates_logger():
    """setup_logger 创建 logger 对象"""
    logger = setup_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"


def test_setup_logger_default_level():
    """默认日志级别从配置读取"""
    mock_settings = MagicMock()
    mock_settings.log_level = "WARNING"
    mock_settings.log_format = "text"

    with patch("src.utils.config.settings", mock_settings):
        logger = setup_logger("test_default_level")
        assert logger.level == logging.WARNING


def test_setup_logger_custom_level():
    """自定义日志级别"""
    logger = setup_logger("test_custom_level", level="DEBUG")
    assert logger.level == logging.DEBUG


def test_setup_logger_avoids_duplicate_handlers():
    """避免重复添加 handler"""
    logger1 = setup_logger("test_duplicate")
    initial_handler_count = len(logger1.handlers)

    logger2 = setup_logger("test_duplicate")
    assert len(logger2.handlers) == initial_handler_count


def test_setup_logger_json_format():
    """JSON 格式日志"""
    mock_settings = MagicMock()
    mock_settings.log_level = "INFO"
    mock_settings.log_format = "json"

    with patch("src.utils.config.settings", mock_settings):
        logger = setup_logger("test_json_format")
        assert logger.handlers


def test_setup_logger_text_format():
    """文本格式日志"""
    mock_settings = MagicMock()
    mock_settings.log_level = "INFO"
    mock_settings.log_format = "text"

    with patch("src.utils.config.settings", mock_settings):
        logger = setup_logger("test_text_format")
        assert logger.handlers


def test_predefined_loggers():
    """预定义的 logger 存在"""
    from src.utils.logger import agent_logger, llm_logger, orchestrator_logger

    assert agent_logger.name == "agent"
    assert llm_logger.name == "llm"
    assert orchestrator_logger.name == "orchestrator"
