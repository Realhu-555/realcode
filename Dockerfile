FROM python:3.12-slim

WORKDIR /app

RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    gcc g++ curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null; \
    pip install --no-cache-dir fastapi uvicorn jinja2 python-dotenv openai httpx tavily-python

COPY src/ src/
COPY frontend/dist/ frontend/dist/
RUN mkdir -p data

EXPOSE 8080
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1
CMD ["python", "-m", "uvicorn", "src.web.server:app", "--host", "0.0.0.0", "--port", "8080"]
