"""健康检查"""

import shutil
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class HealthStatus(StrEnum):
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

    # 检查 GIS 引擎（T14）：产物目录可写 + QGIS 前缀可用
    try:
        from src.utils.config import settings

        out_root = settings.gis_out_root
        probe = out_root / ".health_probe"
        Path(out_root).mkdir(parents=True, exist_ok=True)
        probe.write_text("ok")
        probe.unlink()
        checks["gis_out_dir"] = {"status": "ok", "path": str(out_root)}
    except Exception as e:
        checks["gis_out_dir"] = {"status": "fail", "error": str(e)}
        overall = HealthStatus.DEGRADED

    if settings.gis_engine == "qgis":
        try:
            from src.gis_toolkit.qgis_engine import _find_qgis_prefix

            _find_qgis_prefix()
            checks["qgis"] = {"status": "ok", "engine": "qgis"}
        except Exception as e:
            checks["qgis"] = {"status": "fail", "error": str(e)}
            overall = HealthStatus.DEGRADED

    return HealthCheck(status=overall, checks=checks)
