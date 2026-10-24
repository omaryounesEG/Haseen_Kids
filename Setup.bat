@echo off
setlocal
title Haseen Kids - Setup Wizard
cd /d "%~dp0"
echo [Haseen Kids] Launching Graphical Setup Wizard...
"%~dp0venv\Scripts\python.exe" "%~dp0installer\setup_wizard.py"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Setup Wizard exited with code: %ERRORLEVEL%
    pause
)
endlocal
