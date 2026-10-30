@echo off
setlocal enabledelayedexpansion
title Haseen Kids - Setup (1-Click)
cd /d "%~dp0"

echo ========================================================
echo    HASEEN KIDS  -  One-Click Setup
echo ========================================================
echo   Step 1/4  Find Python
echo   Step 2/4  Prepare local environment
echo   Step 3/4  Install required packages
echo   Step 4/4  Launch the setup wizard
echo ========================================================
echo.

:: ---------------------------------------------------------------- STEP 1
set "PY_EXE="
set "BASE_PY="

:: Already prepared on this machine? Then skip straight to launch.
if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" -c "import PyQt6" >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "PY_EXE=%~dp0venv\Scripts\python.exe"
        echo [1/4] Local environment found - OK
        goto :seed
    )
)

python --version >nul 2>&1
if !ERRORLEVEL! EQU 0 set "BASE_PY=python"
if "!BASE_PY!"=="" (
    py -3 --version >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "BASE_PY=py -3"
)

if "!BASE_PY!"=="" (
    for %%P in (
        "%LocalAppData%\Programs\Python\Python313\python.exe"
        "%LocalAppData%\Programs\Python\Python312\python.exe"
        "%LocalAppData%\Programs\Python\Python311\python.exe"
        "%LocalAppData%\Programs\Python\Python310\python.exe"
        "%ProgramFiles%\Python313\python.exe"
        "%ProgramFiles%\Python312\python.exe"
        "%ProgramFiles%\Python311\python.exe"
        "C:\Python313\python.exe"
        "C:\Python312\python.exe"
        "C:\Python311\python.exe"
        "C:\Python310\python.exe"
    ) do (
        if exist %%P (
            set "BASE_PY=%%~P"
            goto :got_python
        )
    )
)
:got_python

if "!BASE_PY!"=="" (
    echo [1/4] Python not found - downloading the official installer...
    powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\haseen_python.exe'"
    if not exist "%TEMP%\haseen_python.exe" (
        echo [X] Could not download Python. Install it manually from python.org
        echo     Remember to tick "Add Python to PATH".
        pause
        exit /b 1
    )
    echo       Installing Python silently - please wait...
    "%TEMP%\haseen_python.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    timeout /t 8 /nobreak >nul
    set "BASE_PY=python"
)
echo [1/4] Python found - OK

:: ---------------------------------------------------------------- STEP 2
echo [2/4] Preparing local environment...
if not exist "%~dp0venv\Scripts\python.exe" (
    "!BASE_PY!" -m venv "%~dp0venv"
    if !ERRORLEVEL! NEQ 0 (
        echo [X] Could not create the virtual environment.
        pause
        exit /b 1
    )
)

:: ---------------------------------------------------------------- STEP 3
echo [3/4] Installing packages (this may take a couple of minutes)...
"%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%~dp0venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt" --quiet
if !ERRORLEVEL! NEQ 0 (
    echo       Retrying core packages one by one...
    "%~dp0venv\Scripts\python.exe" -m pip install PyQt6 pywin32 psutil yt-dlp cryptography requests bcrypt pillow
)
set "PY_EXE=%~dp0venv\Scripts\python.exe"

:: Verify PyQt6 really works before launching the GUI
"%PY_EXE%" -c "import PyQt6" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [X] PyQt6 could not be installed. Check your internet connection.
    echo     Then run this file again.
    pause
    exit /b 1
)
echo [3/4] Packages ready - OK

:seed
:: ---------------------------------------------------------------- STEP 3b
:: Seed the built-in safe/blocked website lists once (never overwrites parent rules)
"%PY_EXE%" "%~dp0database\seed_lists.py" --if-empty

:: ---------------------------------------------------------------- STEP 4
echo [4/4] Launching the setup wizard...
echo ========================================================
"%PY_EXE%" "%~dp0installer\setup_wizard.py"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
    echo.
    echo [ERROR] Setup wizard exited with code %RC%
    echo         Run this file again, or check the log above.
    pause
)
endlocal
