@echo off
echo Starting ML Inference Service on http://127.0.0.1:8001 (Auth: X-API-Key)...
cd /d "%~dp0ml-service"
"%~dp0.venv\Scripts\python.exe" -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
pause

