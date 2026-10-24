@echo off
setlocal enabledelayedexpansion
title Haseen Kids
cd /d "%~dp0\.."

set "PY_EXE="

:: 1. Check if local venv is healthy
if exist "%~dp0\..\venv\Scripts\python.exe" (
    "%~dp0\..\venv\Scripts\python.exe" --version >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "PY_EXE=%~dp0\..\venv\Scripts\python.exe"
    )
)

:: 2. If venv is broken or moved to another drive, find system python
if "!PY_EXE!"=="" (
    python --version >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "PY_EXE=python"
    )
)

:: 3. Try standard Windows Python install locations (Windows 7 / 10 / 11)
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
    echo ========================================================
    echo  [ERROR] لم يتم العثور على مفسر بايثون على هذا الجهاز.
    echo  يرجى تثبيت Python 3.11 أو تشغيل Setup.bat
    echo ========================================================
    pause
    exit /b 1
)

:: 4. Auto-heal broken venv if on a new machine or drive
if not exist "%~dp0\..\venv\Scripts\python.exe" (
    echo [Haseen Kids] تهيئة البيئة البرمجية للجهاز الحالي...
    "!PY_EXE!" -m venv "%~dp0\..\venv"
    "%~dp0\..\venv\Scripts\python.exe" -m pip install -r "%~dp0\..\requirements.txt"
    set "PY_EXE=%~dp0\..\venv\Scripts\python.exe"
)

"!PY_EXE!" "%~dp0\..\run.py"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Haseen Kids exited with error code: %ERRORLEVEL%
    pause
)
endlocal
