@echo off
echo Starting Core Business Backend on http://127.0.0.1:8000...
cd /d "%~dp0core-backend"
"%~dp0.venv\Scripts\python.exe" -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause

