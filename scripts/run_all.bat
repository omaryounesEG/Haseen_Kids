@echo off
chcp 65001 >nul
title تشغيل برنامج حصين للأطفال - Haseen Kids
cd /d "H:\Haseen_Kids"

echo ===================================================
echo     حَصِين للأطفال ^| Haseen Kids - الحماية الأسرية
echo ===================================================
echo.
echo [1/3] جاري تشغيل الخدمة الخلفية والبروكسي...
start "Haseen Service" /min "H:\Haseen_Kids\venv\Scripts\python.exe" "H:\Haseen_Kids\core\service.py"

echo [2/3] جاري تشغيل حارس المراقبة المزدوج...
start "Haseen Watchdog" /min "H:\Haseen_Kids\venv\Scripts\python.exe" "H:\Haseen_Kids\core\watchdog.py"

echo [3/3] جاري فتح واجهة البرنامج الرئيسية...
"H:\Haseen_Kids\venv\Scripts\python.exe" "H:\Haseen_Kids\ui\app.py"
