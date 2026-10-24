@echo off
setlocal enabledelayedexpansion
title Haseen Kids - Auto Download & Setup from GitHub
cd /d "%~dp0"

echo ========================================================
echo   [Haseen Kids] التحميل والتحديث التلقائي المباشر من GitHub
echo ========================================================
echo.

set "REPO_ZIP=https://github.com/omaryounesEG/Haseen_Kids/archive/refs/heads/main.zip"
set "TEMP_ZIP=%TEMP%\Haseen_Kids_Latest.zip"
set "TEMP_EXTRACT=%TEMP%\Haseen_Kids_Extract"

where git >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    if exist "%~dp0.git" (
        echo [1/3] جاري سحب أحدث نسخة عبر Git...
        git pull origin main
        goto :run_setup
    )
)

echo [1/3] جاري تحميل أحدث إصدار من كود المشروع من GitHub...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%REPO_ZIP%' -OutFile '%TEMP_ZIP%'"

if not exist "%TEMP_ZIP%" (
    echo [ERROR] تعذر تحميل التحديث من GitHub. يرجى التحقق من اتصال الإنترنت.
    pause
    exit /b 1
)

echo [2/3] جاري فك ضغط الملفات وتحديث المشروع...
powershell -Command "Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%TEMP_EXTRACT%' -Force"

if exist "%TEMP_EXTRACT%\Haseen_Kids-main" (
    xcopy /E /Y /Q "%TEMP_EXTRACT%\Haseen_Kids-main\*" "%~dp0"
    rmdir /S /Q "%TEMP_EXTRACT%" >nul 2>&1
    del /F /Q "%TEMP_ZIP%" >nul 2>&1
    echo [OK] تم تحديث جميع الملفات بنجاح ✅
)

:run_setup
echo [3/3] جاري إطلاق معالج التثبيت والتهيئة التلقائية...
echo ========================================================
call "%~dp0Setup.bat"

endlocal
