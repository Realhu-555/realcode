"""共享 fixtures"""

import os

# 单测固定默认 geopandas 引擎：避免 .env（如 GIS_ENGINE=live 依赖 QGIS 插件）
# 污染测试环境；需要 QGIS/真实插件的用例应显式传 engine。
os.environ["GIS_ENGINE"] = "geopandas"

import pytest
from src.sandbox.executor import SandboxExecutor


@pytest.fixture
def sandbox():
    """创建已初始化的沙箱"""
    sb = SandboxExecutor()
    sb.create("test_project")
    yield sb
    sb.cleanup()
