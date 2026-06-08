"""健康检查"""

import shutil
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """健康检查结果"""

    status: HealthStatus
    checks: dict[str, Any] = field(default_factory=dict)
    version: str = "0.1.0"


async def check_health() -> HealthCheck:
    """执行健康检查"""
    checks: dict[str, Any] = {}
    overall = HealthStatus.HEALTHY

    # 检查 LLM 配置
    try:
        from src.utils.config import settings

        checks["llm_config"] = {
            "deepseek": bool(settings.deepseek_api_key),
            "minimax": bool(settings.minimax_api_key),
        }
    except Exception as e:
        checks["llm_config"] = {"error": str(e)}
        overall = HealthStatus.DEGRADED

    # 检查磁盘空间
    usage = shutil.disk_usage("/")
    free_gb = usage.free / (1024**3)
    checks["disk"] = {
        "free_gb": round(free_gb, 2),
        "status": "ok" if free_gb > 1 else "low",
    }
    if free_gb < 1:
        overall = HealthStatus.DEGRADED

    return HealthCheck(status=overall, checks=checks)
