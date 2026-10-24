@echo off
chcp 65001 >nul
title تثبيت سياسات المتصفحات الإجبارية - حصين
cd /d "H:\Haseen_Kids"

echo ========================================================
echo   تطبيق سياسات الأمان الإجبارية على Chrome و Edge
echo   (يجب تشغيل هذا الملف كمسؤول Run as Administrator)
echo ========================================================
echo.

"H:\Haseen_Kids\venv\Scripts\python.exe" -c "from core.security import SecurityManager; sm=SecurityManager(); ok,msg=sm.apply_browser_registry_policies(); print('النتيجة:', msg)"

echo.
echo سيتم الآن إعداد قواعد جدار الحماية (Firewall)...
call "H:\Haseen_Kids\scripts\setup_firewall.bat"

echo.
echo اكتمل إعداد السياسات بنجاح.
pause
