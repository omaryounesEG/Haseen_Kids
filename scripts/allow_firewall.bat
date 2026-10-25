@echo off
setlocal
title Haseen Kids - Windows Firewall Configuration
echo ========================================================
echo   [Haseen Kids] Windows Defender Firewall Configurator
echo   (Please Run as Administrator)
echo ========================================================
echo.

set PY_EXE=%~dp0\..\venv\Scripts\python.exe

echo [1/3] Removing stale block rules...
netsh advfirewall firewall delete rule name="python.exe" dir=in 2>nul
netsh advfirewall firewall delete rule name="Haseen_Python_Allow" 2>nul

echo [2/3] Adding inbound allow rule for Python...
netsh advfirewall firewall add rule name="Haseen_Python_Allow" dir=in action=allow program="%PY_EXE%" profile=any enable=yes

echo [3/3] Allowing local loopback port 8089...
netsh advfirewall firewall add rule name="Haseen_Port_8089" dir=in action=allow protocol=TCP localport=8089 profile=any enable=yes

echo.
echo ========================================================
echo   Firewall rules configured successfully!
echo ========================================================
pause
endlocal
