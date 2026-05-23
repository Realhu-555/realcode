#!/bin/bash
# AI Dev Platform 启动脚本
cd "$(dirname "$0")"
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate 2>/dev/null
pip install -q fastapi uvicorn websockets 2>/dev/null
python -m uvicorn src.web.server:app --host 0.0.0.0 --port 8080 --reload
