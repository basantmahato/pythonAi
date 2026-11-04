@echo off
echo Starting House Price Model Training Pipeline...
"%~dp0.venv\Scripts\python.exe" "%~dp0ml-training\train.py"
pause

