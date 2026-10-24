@echo off
setlocal
title Haseen Kids - Uninstaller
cd /d "%~dp0\.."
echo [Haseen Kids] Launching Uninstaller...
"%~dp0\..\venv\Scripts\python.exe" "uninstall.py"
pause
endlocal
