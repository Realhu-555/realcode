"""健康检查模块单元测试"""

import pytest
from unittest.mock import patch, MagicMock

from src.utils.health import HealthStatus, HealthCheck, check_health


def test_health_status_enum():
    """HealthStatus 枚举值正确"""
    assert HealthStatus.HEALTHY == "healthy"
    assert HealthStatus.DEGRADED == "degraded"
    assert HealthStatus.UNHEALTHY == "unhealthy"


def test_health_check_dataclass():
    """HealthCheck 数据类结构正确"""
    check = HealthCheck(status=HealthStatus.HEALTHY)
    assert check.status == HealthStatus.HEALTHY
    assert check.checks == {}
    assert check.version == "0.1.0"


def test_health_check_with_checks():
    """HealthCheck 可以包含检查结果"""
    checks = {"disk": {"free_gb": 10.5, "status": "ok"}}
    check = HealthCheck(status=HealthStatus.HEALTHY, checks=checks)
    assert check.checks == checks


@pytest.mark.asyncio
async def test_check_health_returns_healthy():
    """健康检查返回健康状态"""
    mock_settings = MagicMock()
    mock_settings.deepseek_api_key = "test-key"
    mock_settings.minimax_api_key = "test-key"

    with patch("src.utils.health.shutil.disk_usage") as mock_disk:
        mock_disk.return_value = MagicMock(free=10 * 1024**3)  # 10GB

        with patch("src.utils.config.settings", mock_settings):
            result = await check_health()

            assert result.status == HealthStatus.HEALTHY
            assert "llm_config" in result.checks
            assert "disk" in result.checks
            assert result.checks["disk"]["free_gb"] == 10.0


@pytest.mark.asyncio
async def test_check_health_low_disk():
    """磁盘空间不足时返回 degraded 状态"""
    mock_settings = MagicMock()
    mock_settings.deepseek_api_key = "test-key"
    mock_settings.minimax_api_key = "test-key"

    with patch("src.utils.health.shutil.disk_usage") as mock_disk:
        mock_disk.return_value = MagicMock(free=0.5 * 1024**3)  # 0.5GB

        with patch("src.utils.config.settings", mock_settings):
            result = await check_health()

            assert result.status == HealthStatus.DEGRADED
            assert result.checks["disk"]["status"] == "low"


@pytest.mark.asyncio
async def test_check_health_config_error():
    """配置错误时返回 degraded 状态"""
    import src.utils.config as config_mod

    mock_settings = MagicMock()
    type(mock_settings).deepseek_api_key = property(
        lambda self: (_ for _ in ()).throw(Exception("Config error"))
    )
    original_settings = config_mod.settings

    with patch("src.utils.health.shutil.disk_usage") as mock_disk:
        mock_disk.return_value = MagicMock(free=10 * 1024**3)
        config_mod.settings = mock_settings
        try:
            result = await check_health()

            assert result.status == HealthStatus.DEGRADED
            assert "llm_config" in result.checks
            assert "error" in result.checks["llm_config"]
        finally:
            config_mod.settings = original_settings
