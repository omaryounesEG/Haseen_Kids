@echo off
setlocal enabledelayedexpansion
title Haseen Kids - UI
cd /d "%~dp0\.."

set "PY_EXE="

if exist "%~dp0\..\venv\Scripts\python.exe" (
    "%~dp0\..\venv\Scripts\python.exe" --version >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "PY_EXE=%~dp0\..\venv\Scripts\python.exe"
    )
)

if "!PY_EXE!"=="" (
    python --version >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "PY_EXE=python"
    )
)

if "!PY_EXE!"=="" (
    for %%P in (
        "%LocalAppData%\Programs\Python\Python311\python.exe"
        "%LocalAppData%\Programs\Python\Python312\python.exe"
        "%ProgramFiles%\Python311\python.exe"
        "%ProgramFiles%\Python312\python.exe"
        "C:\Python311\python.exe"
        "C:\Python312\python.exe"
        "C:\Python38\python.exe"
    ) do (
        if exist %%P (
            set "PY_EXE=%%~P"
            goto :found_py
        )
    )
)
:found_py

if "!PY_EXE!"=="" (
    echo [ERROR] Python not found on this system.
    pause
    exit /b 1
)

:: Verify PyQt6 is available
"!PY_EXE!" -c "import PyQt6" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [Haseen Kids] Installing required libraries (PyQt6, etc.)...
    "!PY_EXE!" -m pip install -r "%~dp0\..\requirements.txt"
)

"!PY_EXE!" "ui\app.py"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] App exited with error code: %ERRORLEVEL%
    pause
)
endlocal
