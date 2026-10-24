@echo off
setlocal
title Haseen Kids
cd /d "%~dp0\.."
"%~dp0\..\venv\Scripts\python.exe" "%~dp0\..\run.py"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Haseen Kids exited with error code: %ERRORLEVEL%
    pause
)
endlocal
