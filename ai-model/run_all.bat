@echo off
echo =========================================================================
echo   Starting House Price Prediction Multi-Tier System
echo   1. ML Inference Service   : http://127.0.0.1:8001 (Protected by X-API-Key)
echo   2. Core Business Backend  : http://127.0.0.1:8000 (Orchestration & Logic)
echo   3. React Frontend         : http://localhost:5173 (User Dashboard)
echo =========================================================================
echo.

echo [1/3] Launching ML Inference Service on Port 8001...
start "1-ML-Inference-Service" cmd /k "cd /d %~dp0ml-service && %~dp0.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8001"

timeout /t 2 /nobreak >nul

echo [2/3] Launching Core Business Backend on Port 8000...
start "2-Core-Business-Backend" cmd /k "cd /d %~dp0core-backend && %~dp0.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul

echo [3/3] Launching React + Vite Frontend on Port 5173...
start "3-React-Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo =========================================================================
echo   All 3 services running in separate windows!
echo   - Web Dashboard  : http://localhost:5173
echo   - Core API Docs  : http://127.0.0.1:8000/docs
echo   - ML API Docs    : http://127.0.0.1:8001/docs (Requires X-API-Key)
echo =========================================================================
echo.
pause
