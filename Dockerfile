FROM python:3.12-slim

WORKDIR /app

RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    gcc g++ curl && rm -rf /var/lib/apt/lists/*

# 只装 Web 层最简依赖（最慢的 langgraph/langchain 本机已有，Docker 用 --network host 或将来加镜像）
RUN pip install --no-cache-dir --default-timeout=300 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    fastapi "uvicorn[standard]" jinja2 python-dotenv \
    openai httpx pydantic websockets tavily-python

COPY src/ src/
COPY data/ data/
RUN mkdir -p data

EXPOSE 8080
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
CMD ["python", "-m", "uvicorn", "src.web.server:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
