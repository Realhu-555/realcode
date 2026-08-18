"""共享 fixtures"""

import pytest
from src.sandbox.executor import SandboxExecutor


@pytest.fixture
def sandbox():
    """创建已初始化的沙箱"""
    sb = SandboxExecutor()
    sb.create("test_project")
    yield sb
    sb.cleanup()
