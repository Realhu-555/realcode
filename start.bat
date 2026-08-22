@echo off
REM GIS 智能助手后端启动（Windows）
cd /d %~dp0
set PYTHONIOENCODING=utf-8
call venv\Scripts\activate.bat
python -m uvicorn src.web.server:app --host 0.0.0.0 --port 8080
