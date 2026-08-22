@echo off
REM 质量门禁：ruff + pytest（提交前 / CI 用，硬性必须全绿）
cd /d %~dp0..

echo [1/3] ruff check ...
call venv\Scripts\python.exe -m ruff check src tests
if errorlevel 1 exit /b 1

echo [2/3] ruff format --check ...
call venv\Scripts\python.exe -m ruff format --check src tests
if errorlevel 1 exit /b 1

echo [3/3] pytest ...
call venv\Scripts\python.exe -m pytest tests -q --basetemp=.pytest_tmp\ci -p no:cacheprovider --ignore=tests/test_ocr_docker.py --ignore=tests/test_sandbox.py --ignore=tests/test_gis_sandbox.py
if errorlevel 1 exit /b 1

echo.
echo ALL CHECKS PASSED
