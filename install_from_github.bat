@echo off
setlocal enabledelayedexpansion
title Haseen Kids - Auto Download & Setup from GitHub
cd /d "%~dp0"

echo ========================================================
echo   [Haseen Kids] Automated GitHub Downloader & Installer
echo ========================================================
echo.

set "REPO_ZIP=https://github.com/omaryounesEG/Haseen_Kids/archive/refs/heads/main.zip"
set "TEMP_ZIP=%TEMP%\Haseen_Kids_Latest.zip"
set "TEMP_EXTRACT=%TEMP%\Haseen_Kids_Extract"

where git >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    if exist "%~dp0.git" (
        echo [1/3] Syncing latest updates via Git...
        git pull origin main
        goto :run_setup
    )
)

echo [1/3] Downloading latest project release from GitHub...
powershell -NoProfile -Command "$ProgressPreference = 'SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%REPO_ZIP%' -OutFile '%TEMP_ZIP%'"

if not exist "%TEMP_ZIP%" (
    echo [ERROR] Failed to download package from GitHub. Please check your internet connection.
    pause
    exit /b 1
)

echo [2/3] Extracting files and applying update...
powershell -NoProfile -Command "$ProgressPreference = 'SilentlyContinue'; Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%TEMP_EXTRACT%' -Force; $root = Get-ChildItem -Path '%TEMP_EXTRACT%' -Directory | Select-Object -First 1; if ($root) { Get-ChildItem -Path $root.FullName | Where-Object { $_.Name -notmatch '\.db$' } | Copy-Item -Destination '%~dp0' -Recurse -Force }"

rmdir /S /Q "%TEMP_EXTRACT%" >nul 2>&1
del /F /Q "%TEMP_ZIP%" >nul 2>&1
echo [OK] Project files extracted successfully.

:run_setup
echo [3/3] Launching Setup Wizard...
echo ========================================================
if exist "%~dp0Setup.bat" (
    call "%~dp0Setup.bat"
) else (
    echo [ERROR] Setup.bat not found in %~dp0
    pause
)

endlocal
