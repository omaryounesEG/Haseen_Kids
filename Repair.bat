@echo off
setlocal enabledelayedexpansion
title Haseen Kids - Repair (Fix installation)
cd /d "%~dp0"

echo ==============================================================
echo    HASEEN KIDS - REPAIR / FIX INSTALLATION
echo ==============================================================
echo  Folder: %CD%
echo.
echo  This repairs a broken install WITHOUT touching:
echo    - parent password      - whitelist / blacklist
echo    - browsing history     - your recovery key
echo.

:: ---------------------------------------------------------------
:: 0. Refuse to work from a protected folder (this is what breaks
::    saving: C:\Windows, System32, Program Files)
:: ---------------------------------------------------------------
echo %CD% | findstr /I /C:"\Windows" /C:"Program Files" >nul
if !ERRORLEVEL! EQU 0 (
    echo [ERROR] This folder is protected by Windows: %CD%
    echo         Move the whole Haseen_Kids folder to C:\Haseen_Kids
    echo         and run Repair.bat again.
    pause
    exit /b 1
)

:: ---------------------------------------------------------------
:: 1. Find a usable Python
:: ---------------------------------------------------------------
set "SYS_PY="
for %%P in (
    "%~dp0venv\Scripts\python.exe"
    "python"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python312\python.exe"
) do (
    if not defined SYS_PY (
        if exist %%P (
            set "SYS_PY=%%~P"
        ) else (
            %%P --version >nul 2>&1
            if !ERRORLEVEL! EQU 0 set "SYS_PY=%%~P"
        )
    )
)
if not defined SYS_PY (
    python --version >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "SYS_PY=python"
)
if not defined SYS_PY (
    echo [ERROR] Python not found. Install Python 3.11 x64 from python.org
    echo         and tick "Add python.exe to PATH", then run Setup.bat.
    pause
    exit /b 1
)
echo [1/5] Python found: !SYS_PY!

:: ---------------------------------------------------------------
:: 2. Rebuild a healthy local environment (removes a broken venv only)
:: ---------------------------------------------------------------
set "VENV_PY=%~dp0venv\Scripts\python.exe"
if exist "!VENV_PY!" (
    "!VENV_PY!" -c "import sys, PyQt6, yt_dlp, bcrypt, requests" >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo [2/5] Local environment is healthy - keeping it.
        goto :env_ready
    )
    echo [2/5] Local environment is broken - rebuilding it...
    rmdir /s /q "%~dp0venv" >nul 2>&1
) else (
    echo [2/5] Building the local environment...
)

"!SYS_PY!" -m venv "%~dp0venv"
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Could not create the environment. Check free space and permissions.
    pause
    exit /b 1
)
"%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%~dp0venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt" --quiet
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Installing the required packages failed. Check your internet connection.
    pause
    exit /b 1
)
:env_ready

:: ---------------------------------------------------------------
:: 3. Clean leftovers from crashed sessions
:: ---------------------------------------------------------------
echo [3/5] Cleaning stale locks and processes...
if exist "%~dp0core\service.pid" del /q "%~dp0core\service.pid" >nul 2>&1
if exist "%~dp0core\watchdog.pid" del /q "%~dp0core\watchdog.pid" >nul 2>&1
taskkill /f /im pythonw.exe /fi "WINDOWTITLE eq Haseen*" >nul 2>&1

:: ---------------------------------------------------------------
:: 4. Check the database and keep a backup copy
:: ---------------------------------------------------------------
echo [4/5] Checking the database...
if exist "%~dp0database\haseen.db" (
    if not exist "%~dp0database\backup" mkdir "%~dp0database\backup"
    copy /y "%~dp0database\haseen.db" "%~dp0database\backup\haseen_before_repair.db" >nul 2>&1
    echo       Database found and backed up ^(password and lists are kept^).
) else (
    echo       No database yet - a fresh one will be created with the default password.
)

"%~dp0venv\Scripts\python.exe" -c "from database.db_manager import DBManager; DBManager(); print('      Database is readable and writable.')"

:: ---------------------------------------------------------------
:: 5. Verify the program can import everything it needs
:: ---------------------------------------------------------------
echo [5/5] Verifying the program components...
"%~dp0venv\Scripts\python.exe" -c "import sys; sys.path.insert(0, r'%~dp0'); import proxy.filter_engine, core.security, core.recovery, ui.theme; print('      All components load correctly.')"
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] A component failed to load - see the message above.
    pause
    exit /b 1
)

echo.
echo ==============================================================
echo   REPAIR FINISHED - the program is ready to start.
echo   Run scripts\run_all.bat or the desktop shortcut.
echo ==============================================================
if exist "%~dp0logs\haseen_error.log" (
    echo   Previous errors are saved in: logs\haseen_error.log
)
echo.
pause
