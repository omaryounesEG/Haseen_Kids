@echo off
setlocal
title Haseen Kids - Watchdog
cd /d "%~dp0\.."
"%~dp0\..\venv\Scripts\python.exe" "core\watchdog.py"
pause
endlocal
