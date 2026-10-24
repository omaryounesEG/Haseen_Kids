@echo off
setlocal enabledelayedexpansion
title Haseen Kids - Master Setup
cd /d "%~dp0"

echo ========================================================
echo   [Haseen Kids] معالج التثبيت الذكي لنظام حصين للأطفال
echo ========================================================
echo.

set "PY_EXE="

:: 1. Check if local venv already exists and has PyQt6
if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" -c "import PyQt6" >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "PY_EXE=%~dp0venv\Scripts\python.exe"
        goto :launch
    )
)

:: 2. Find base Python on system
set "BASE_PY="
python --version >nul 2>&1
if !ERRORLEVEL! EQU 0 set "BASE_PY=python"

if "!BASE_PY!"=="" (
    py --version >nul 2>&1
    if !ERRORLEVEL! EQU 0 set "BASE_PY=py"
)

if "!BASE_PY!"=="" (
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
            set "BASE_PY=%%~P"
            goto :found_base
        )
    )
)
:found_base

if "!BASE_PY!"=="" (
    echo ========================================================
    echo  [!] لم يتم العثور على مفسر بايثون على هذا الجهاز.
    echo  جاري تحميل وتثبيت بايثون الرسمي تلقائياً...
    echo ========================================================
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"
    if exist "%TEMP%\python_installer.exe" (
        echo  جاري تثبيت Python في صمت...
        "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        timeout /t 10 /nobreak >nul
        set "BASE_PY=python"
    ) else (
        echo  [X] يرجى تثبيت Python 3.11 من الموقع الرسمي: https://www.python.org
        pause
        exit /b 1
    )
)

:: 3. Prepare clean local venv on THIS machine
echo [1/2] جاري تهيئة بيئة العمل الخاصة بجهازك محلياً (venv)...
if not exist "%~dp0venv\Scripts\python.exe" (
    "!BASE_PY!" -m venv "%~dp0venv"
)

:: 4. Auto-install all required libraries on this PC
echo [2/2] جاري تثبيت المكتبات المطلوبة (PyQt6, yt-dlp, psutil, pillow)...
"%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
"%~dp0venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if %ERRORLEVEL% NEQ 0 (
    echo [!] فشل تثبيت بعض المكتبات عبر pip، جاري المحاولة المباشرة...
    "%~dp0venv\Scripts\python.exe" -m pip install PyQt6 pywin32 psutil yt-dlp cryptography requests bcrypt pillow
)

set "PY_EXE=%~dp0venv\Scripts\python.exe"

:launch
echo.
echo [OK] تم تجهيز كافة المكتبات بنجاح ✅
echo جاري فتح معالج التثبيت الرسومي...
echo ========================================================
"!PY_EXE!" "%~dp0installer\setup_wizard.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] حدث خطأ أثناء تشغيل معالج التثبيت: كود %ERRORLEVEL%
    pause
)
endlocal
