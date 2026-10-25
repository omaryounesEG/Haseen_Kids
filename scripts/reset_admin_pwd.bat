@echo off
title Haseen Kids - Emergency Admin Password Reset
cd /d "%~dp0\.."

:: Check for administrative privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [Haseen Kids] Requesting Administrator Privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Locate Python
set "PY_EXE="
if exist "%~dp0..\venv\Scripts\python.exe" set "PY_EXE=%~dp0..\venv\Scripts\python.exe"
if not defined PY_EXE (
    for /f "tokens=*" %%i in ('where python 2^>nul') do (
        if not defined PY_EXE set "PY_EXE=%%i"
    )
)

if not defined PY_EXE (
    echo [ERROR] Python interpreter not found!
    pause
    exit /b 1
)

"%PY_EXE%" "%~dp0reset_admin_pwd.py"
