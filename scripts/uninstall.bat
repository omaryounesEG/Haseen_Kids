@echo off
setlocal enabledelayedexpansion
title Haseen Kids - Uninstaller
cd /d "%~dp0\.."

set "PY_EXE="
if exist "%~dp0\..\venv\Scripts\python.exe" set "PY_EXE=%~dp0\..\venv\Scripts\python.exe"
if "!PY_EXE!"=="" set "PY_EXE=python"

echo [Haseen Kids] Launching Uninstaller...
"!PY_EXE!" "uninstall.py"
pause
endlocal
