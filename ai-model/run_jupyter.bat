@echo off
echo Starting JupyterLab in ml-training...
cd /d "%~dp0ml-training"
"%~dp0.venv\Scripts\jupyter-lab.exe" --notebook-dir="%~dp0ml-training"
pause

