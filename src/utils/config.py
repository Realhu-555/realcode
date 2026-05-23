"""配置类（环境变量读取）"""
import os
from pathlib import Path
from dotenv import load_dotenv


def load_config(env_file: str | None = None) -> None:
    """加载 .env 文件到环境变量"""
    if env_file:
        load_dotenv(env_file)
    else:
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / ".env"
        load_dotenv(env_path if env_path.exists() else ".env")
