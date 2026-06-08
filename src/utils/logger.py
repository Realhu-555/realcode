"""结构化日志"""

import logging
import sys


def setup_logger(
    name: str,
    level: str | None = None,
    format_type: str | None = None,
) -> logging.Logger:
    """创建结构化 Logger"""
    from src.utils.config import settings

    logger = logging.getLogger(name)
    logger.setLevel(level or settings.log_level)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    formatter: logging.Formatter

    if (format_type or settings.log_format) == "json":
        try:
            from pythonjsonlogger import jsonlogger

            formatter = jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
                rename_fields={"levelname": "level", "asctime": "timestamp"},
            )
        except ImportError:
            formatter = logging.Formatter(
                fmt="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# 预定义 logger
agent_logger = setup_logger("agent")
llm_logger = setup_logger("llm")
orchestrator_logger = setup_logger("orchestrator")
