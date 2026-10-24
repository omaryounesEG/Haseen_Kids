@echo off
setlocal
title Haseen Kids - UI
cd /d "%~dp0\.."
"%~dp0\..\venv\Scripts\python.exe" "ui\app.py"
endlocal
