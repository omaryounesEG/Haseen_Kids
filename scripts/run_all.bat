@echo off
setlocal
title Haseen Kids
cd /d "%~dp0\.."
"%~dp0\..\venv\Scripts\python.exe" "%~dp0\..\run.py"
endlocal
