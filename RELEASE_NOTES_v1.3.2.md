# حَصِين للأطفال | Haseen Kids — الإصدار 1.3.2 🛡️

> إصلاح أمر التثبيت المباشر (CMD): لم يعد يثبّت داخل `C:\Windows\System32`

## المشكلة التي حدثت

أمر التثبيت المباشر كان يحمّل الملفات ويستخرجها في **المجلد الحالي** — وكان
`C:\Windows\System32` لأن نافذة CMD مفتوحة كمسؤول. فتناثرت ملفات البرنامج
وقاعدة بياناته (`database\haseen.db`) داخل مجلد محمي، فتعطّل الحفظ، ثم توقّف البرنامج.

## ما أُصلح في هذا الإصدار

| الإصلاح | التفصيل |
|---|---|
| **لا تثبيت في مجلد التشغيل** | يختار مجلداً آمناً: `C:\Haseen_Kids`، وإذا لم يكن قابلاً للكتابة → `%LOCALAPPDATA%\Haseen_Kids` |
| **رفض المجلدات المحمية** | `C:\Windows` و`Program Files` تُرفض تلقائياً ويُحوَّل التثبيت لمكان سليم |
| **حماية كلمة المرور** | نسخ بـ `robocopy` مع استثناء `*.db` و`*.db-wal` و`*.db-shm` و`recovery.sig` — لا تُمسح القوائم ولا كلمة السر |
| **مسار واضح** | يطبع مجلد التثبيت النهائي، ثم يشغّل `Repair.bat /auto` ثم `Setup.bat` |
| **أمر CMD آمن** | السكربت يُحمَّل إلى `%TEMP%` أولاً حتى لا يُكتب أي ملف في مجلد نافذة CMD |

## أمر التثبيت / التحديث (استخدم هذا)

```cmd
curl -sSL https://raw.githubusercontent.com/omaryounesEG/Haseen_Kids/main/install_from_github.bat -o "%TEMP%\haseen_install.bat" && "%TEMP%\haseen_install.bat"
```

**PowerShell:**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=Join-Path $env:TEMP 'haseen_install.bat'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://raw.githubusercontent.com/omaryounesEG/Haseen_Kids/main/install_from_github.bat',$d); & $d"
```

## الدليل (اختبار فعلي)

| الاختبار | النتيجة |
|---|---|
| تثبيت في مجلد مخصص مع وجود `haseen.db` قديم | الملف **بقي كما هو** ولم يُستبدل (تم التحقق من محتواه) |
| محاولة تثبيت في `C:\Windows\System32\HaseenTest` | **رُفضت** وحُوّلت إلى `%LOCALAPPDATA%`، ولم يُكتب شيء داخل System32 |
| عدد الملفات المنسوخة | 73 ملفاً تشمل `Repair.bat` و`core/crashguard.py` |
| اختبارات آلية | **58 / 58 ناجحة** |

## إن كانت نسختك الحالية معطّلة

1. انقل/احذف مجلد البرنامج من `C:\Windows\System32` (يحتاج صلاحيات مسؤول).
2. شغّل أمر التثبيت أعلاه — سيثبّت في `C:\Haseen_Kids`.
3. إن كان لديك `C:\Windows\System32\database\haseen.db` انسخه إلى `C:\Haseen_Kids\database\`
   **قبل** أول تشغيل للحفاظ على كلمة المرور.

**المطور:** SAIP Consulting — **الترخيص:** MIT
