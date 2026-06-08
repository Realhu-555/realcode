# ── 开发阶段 ──────────────────────────────────────────
FROM python:3.12-slim AS development

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# 复制代码
COPY src/ src/
COPY tests/ tests/

# 默认运行测试
CMD ["pytest", "tests/", "-v"]

# ── 生产阶段 ──────────────────────────────────────────
FROM python:3.12-slim AS production

WORKDIR /app

# 安装依赖
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# 复制源码
COPY src/ src/

# 暴露端口
EXPOSE 8080

# 启动 Web 服务
CMD ["python", "-m", "uvicorn", "src.web.server:app", "--host", "0.0.0.0", "--port", "8080"]
