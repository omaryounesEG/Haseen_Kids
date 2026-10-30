@echo off
title Haseen Kids - Final Removal / Recovery (Offline)
cd /d "%~dp0"

echo ==============================================================
echo   HASEEN KIDS - REMOVAL AND PASSWORD RECOVERY
echo   This tool works fully OFFLINE.
echo ==============================================================
echo.

set "PY_EXE="
if exist "%~dp0venv\Scripts\python.exe" set "PY_EXE=%~dp0venv\Scripts\python.exe"
if not defined PY_EXE (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        if not defined PY_EXE set "PY_EXE=%%i"
    )
)
if not defined PY_EXE (
    echo [ERROR] Python was not found on this PC.
    echo         Copy the folder again from GitHub, or install Python 3.9+.
    pause
    exit /b 1
)

"%PY_EXE%" "%~dp0uninstall.py"
echo.
pause
