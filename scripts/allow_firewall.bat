@echo off
setlocal
title Haseen Kids - Allow Firewall
echo ========================================================
echo   [Haseen Kids] السماح للبرنامج في جدار حماية ويندوز
echo   (يرجى التشغيل كمسؤول Run as Administrator)
echo ========================================================
echo.

set PY_EXE=%~dp0\..\venv\Scripts\python.exe

echo [1/3] حذف أي قواعد حظر قديمة لـ Python...
netsh advfirewall firewall delete rule name="python.exe" dir=in 2>nul
netsh advfirewall firewall delete rule name="Haseen_Python_Allow" 2>nul

echo [2/3] إضافة قاعدة سماح لـ Python في الشبكات الخاصة والعامة...
netsh advfirewall firewall add rule name="Haseen_Python_Allow" dir=in action=allow program="%PY_EXE%" profile=any enable=yes

echo [3/3] السماح بالمنفذ المحلي 8089...
netsh advfirewall firewall add rule name="Haseen_Port_8089" dir=in action=allow protocol=TCP localport=8089 profile=any enable=yes

echo.
echo ========================================================
echo   تم فك الحجب والسماح للبرنامج في جدار الحماية بنجاح!
echo ========================================================
pause
endlocal
