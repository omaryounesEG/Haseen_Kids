@echo off
setlocal
title Haseen Kids - Updater
cd /d "%~dp0\.."

echo ========================================================
echo   [Haseen Kids] Checking and Downloading Latest Updates
echo ========================================================
echo.

where git >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    git pull origin main
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [OK] All project files updated successfully!
    ) else (
        echo.
        echo [!] Git pull failed. Please check your internet connection.
    )
) else (
    echo [!] Git tool not found on this system.
    echo Running automated GitHub package update...
    call "%~dp0\..\install_from_github.bat"
)

echo.
pause
endlocal
