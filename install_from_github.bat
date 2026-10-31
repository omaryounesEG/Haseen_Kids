@echo off
setlocal enabledelayedexpansion
title Haseen Kids - Install / Update from GitHub

:: =====================================================================
::  HASEEN KIDS - one-line installer / updater
::
::  This file is meant to be launched from ANY folder (Cmd, Downloads,
::  even C:\Windows\System32 when Cmd is opened as administrator).
::  It therefore NEVER installs into the folder it happens to sit in.
::  It picks a safe install folder, keeps your existing database (parent
::  password, lists, logs) and then starts Setup.bat from that folder.
:: =====================================================================

set "REPO_ZIP=https://github.com/omaryounesEG/Haseen_Kids/archive/refs/heads/main.zip"
set "TEMP_ZIP=%TEMP%\Haseen_Kids_Latest.zip"
set "TEMP_EXTRACT=%TEMP%\Haseen_Kids_Extract"
set "TARGET="

echo ========================================================
echo   [Haseen Kids] Install / update from GitHub
echo ========================================================
echo.

:: ---------------------------------------------------------------------
:: 1. Decide WHERE to install
:: ---------------------------------------------------------------------
:: (a) explicit override
if defined HASEEN_INSTALL_DIR set "TARGET=%HASEEN_INSTALL_DIR%"

:: (b) we are already inside a real installation (e.g. running Update.bat)
if not defined TARGET if exist "%~dp0run.py" if exist "%~dp0core\service.py" set "TARGET=%~dp0"

:: (c) an earlier install in the default place
if not defined TARGET if exist "C:\Haseen_Kids\run.py" set "TARGET=C:\Haseen_Kids"

:: (d) otherwise the default location
if not defined TARGET set "TARGET=C:\Haseen_Kids"

:: (e) never install inside Windows / Program Files
echo !TARGET! | findstr /I /C:"\Windows" /C:"\Program Files" >nul
if not errorlevel 1 (
    set "TARGET=%LOCALAPPDATA%\Haseen_Kids"
    echo [i] The download folder is protected by Windows, so the program
    echo     will be installed in a normal folder instead.
)

:: (f) if the folder cannot be created/written, fall back to LOCALAPPDATA
if not exist "!TARGET!" mkdir "!TARGET!" >nul 2>&1
type nul > "!TARGET!\.write_test" 2>nul
if not exist "!TARGET!\.write_test" (
    set "TARGET=%LOCALAPPDATA%\Haseen_Kids"
    if not exist "!TARGET!" mkdir "!TARGET!" >nul 2>&1
) else (
    del /q "!TARGET!\.write_test" >nul 2>&1
)

echo [i] Install folder: !TARGET!
if not "%~dp0"=="!TARGET!\" (
    if /I not "%~dp0"=="!TARGET!" (
        echo [i] Note: this installer runs from "%~dp0"
        echo     but the program lives in "!TARGET!" - that is intentional.
    )
)
echo.

:: ---------------------------------------------------------------------
:: 2. Download the latest source archive
:: ---------------------------------------------------------------------
echo [1/3] Downloading the latest files from GitHub...
if exist "%TEMP_ZIP%" del /f /q "%TEMP_ZIP%" >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%REPO_ZIP%' -OutFile '%TEMP_ZIP%'"
if not exist "%TEMP_ZIP%" (
    echo [ERROR] Download failed. Check the internet connection and try again.
    pause
    exit /b 1
)

:: ---------------------------------------------------------------------
:: 3. Extract, then copy over the install folder WITHOUT touching data
:: ---------------------------------------------------------------------
echo [2/3] Applying the files (your password and settings are kept)...
if exist "%TEMP_EXTRACT%" rmdir /s /q "%TEMP_EXTRACT%" >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%TEMP_EXTRACT%' -Force"
if not exist "%TEMP_EXTRACT%" (
    echo [ERROR] Could not unpack the downloaded archive.
    pause
    exit /b 1
)

set "SRC="
for /d %%D in ("%TEMP_EXTRACT%\*") do set "SRC=%%~fD"
if not defined SRC (
    echo [ERROR] The archive was empty.
    pause
    exit /b 1
)

:: /XF : never copy database or recovery state over the existing ones
robocopy "!SRC!" "!TARGET!" /E /NFL /NDL /NJH /NJS /NP /XF *.db *.db-wal *.db-shm recovery.sig run_log.txt *.pid /XD .git venv __pycache__ logs tests\_shots >nul
if !ERRORLEVEL! GEQ 8 (
    echo [WARN] Some files could not be copied ^(robocopy code !ERRORLEVEL!^).
    echo        Close the program first, then run this file again.
)

rmdir /s /q "%TEMP_EXTRACT%" >nul 2>&1
del /f /q "%TEMP_ZIP%" >nul 2>&1
echo [OK] Files updated in: !TARGET!

:: ---------------------------------------------------------------------
:: 4. Start the setup / repair wizard from the install folder
:: ---------------------------------------------------------------------
echo [3/3] Preparing the environment...
echo ========================================================
pushd "!TARGET!"
if exist "!TARGET!\Repair.bat" (
    echo A quick health check runs first; it keeps your password and data.
    call "!TARGET!\Repair.bat" /auto
)
if exist "!TARGET!\Setup.bat" (
    call "!TARGET!\Setup.bat"
) else (
    echo [ERROR] Setup.bat is missing from !TARGET!
    pause
)
popd
endlocal
