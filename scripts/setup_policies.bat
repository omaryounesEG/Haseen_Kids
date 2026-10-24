@echo off
setlocal
title Haseen Kids - Setup Policies
cd /d "%~dp0\.."
echo [Haseen Kids] Applying Enterprise Browser Policies and Firewall rules...
"%~dp0\..\venv\Scripts\python.exe" -c "from core.security import SecurityManager; sm=SecurityManager(); ok,msg=sm.apply_browser_registry_policies(); print('Result:', msg)"
if exist "scripts\setup_firewall.bat" call "scripts\setup_firewall.bat"
echo Done.
pause
endlocal
