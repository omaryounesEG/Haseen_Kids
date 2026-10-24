@echo off
setlocal
title Haseen Kids - Updater
cd /d "%~dp0\.."

echo ========================================================
echo   [Haseen Kids] جاري فحص وتنزيل آخر التحديثات من GitHub...
echo ========================================================
echo.

where git >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    git pull origin main
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [OK] تم تحديث كافة الملفات بنجاح إلى آخر إصدار! ✅
    ) else (
        echo.
        echo [!] تعذر التحديث عبر git، تأكد من الاتصال بالإنترنت.
    )
) else (
    echo [!] لم يتم العثور على أداة git على هذا الجهاز.
    echo يمكنك التحديث التلقائي أيضاً من داخل البرنامج عبر:
    echo لوحة تحكم ولي الأمر -> تبويب التحديثات -> فحص التحديثات.
)

echo.
pause
endlocal
