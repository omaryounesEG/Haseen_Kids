@echo off
setlocal
title Haseen Kids - Core Daemon
cd /d "%~dp0\.."
"%~dp0\..\venv\Scripts\python.exe" "core\service.py"
pause
endlocal
