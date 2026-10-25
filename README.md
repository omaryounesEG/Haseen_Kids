# 🛡️ حَصِين للأطفال | Haseen Kids

> **نظام الحماية والرقابة الأسرية الذكي ومشغل يوتيوب المعزول بدون إعلانات نهائياً**  
> *متوافق مع Windows 7 و Windows 8 و Windows 10 و Windows 11*

---

## 🚀 التثبيت السريع بسطر واحد (One-Liner Installation)

يمكنك تثبيت البرنامج كاملاً مع كافة مكتباته بضغطة زر واحدة بنسخ أحد الأوامر التالية:

### 1️⃣ عبر موجه الأوامر (Command Prompt - CMD):
افتح **CMD** والصق السطر التالي ثم اضغط **Enter**:
```cmd
curl -sSL https://raw.githubusercontent.com/omaryounesEG/Haseen_Kids/main/install_from_github.bat -o install_from_github.bat && install_from_github.bat
```

### 2️⃣ عبر PowerShell:
افتح **PowerShell** والصق السطر التالي ثم اضغط **Enter**:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://raw.githubusercontent.com/omaryounesEG/Haseen_Kids/main/install_from_github.bat', 'install_from_github.bat'); .\install_from_github.bat"
```

---

## ✨ المميزات المعمارية والوظيفية

1. **مشغل يوتيوب المعزول (Ad-Free Isolated Player)**:
   - تشغيل مباشر وفوري للبث ومقاطع الفيديو دون تحميل مسبق ودون تخزين يستهلك القرص الصلب.
   - تجاوز وتخطي كافة إعلانات المقاطع والإعلانات المدمجة عبر محرك SponsorBlock.
2. **فلترة هرمية ثلاثية المراحل (3-Tier Filter Engine)**:
   - **Tier 1 (محلي فوري <5ms)**: قوائم بيضاء وسوداء لقواعد بيانات SQLite WAL.
   - **Tier 2 (تصنيف محلي)**: تحليل دلالي ذكي وسريع بالكلمات المفتاحية والـ Regex.
   - **Tier 3 (استدعاء ذكي مشروط)**: فحص بالذكاء الاصطناعي لا يُستهلك إلا للضرورة القصوى مع آلية حفظ محلي (Cache) لتوفير التوكنز.
3. **معالج تثبيت رسومي تفاعلي (5-Step Setup Wizard)**:
   - فحص جهوزية الجهاز (الذاكرة والمعالج وجدار الحماية).
   - فحص المتصفحات (Chrome, Edge, Brave, Firefox).
   - تحميل وتثبيت تلقائي لمتصفح Brave الرسمي الآمن للأطفال إن لم يكن متوفراً.
   - تثبيت إضافة المتصفح الخاصة بحصين تلقائياً.
4. **حارس مراقبة مزدوج ذاتي التعافي (Mutual Watchdog)**:
   - رصد صحة الخدمة الخلفية والبروكسي وإعادة التشغيل التلقائي عند أي محاولة إغلاق.
5. **لوحة تحكم ولي أمر محمية بكلمة مرور**:
   - كلمة المرور الافتراضية: `haseen2026`.
   - إدارة جداول الأوقات، القوائم البيضاء، نظام الاستثناءات المؤقتة برموز HMAC-SHA256 المشفرة.
   - تقارير أسبوعية تفصيلية لنشاط التصفح والمنصات التعليمية.

---

## 📁 ملفات التشغيل والإدارة السريعة

| الملف | الوظيفة |
| :--- | :--- |
| `Setup.bat` | تشغيل معالج التثبيت الرسومي الذكي وفحص المكتبات. |
| `install_from_github.bat` | تحميل وتحديث كود المشروع تلقائياً من GitHub وتثبيته. |
| `scripts\run_all.bat` | تشغيل الخدمة والبروكسي وحارس المراقبة والواجهة الرسومية. |
| `scripts\run_kids_app.bat` | تشغيل الواجهة الرسومية للطفل مباشرة. |
| `scripts\update.bat` | تحديث المشروع لآخر إصدار من GitHub بضغطة زر. |
| `scripts\uninstall.bat` | إلغاء التثبيت الآمن المحمي بكلمة مرور ولي الأمر. |

---

## 🔐 الأمان والخصوصية
- لا يتم حفظ أو تصدير أي بيانات تصفح خارج جهازك؛ كافة السجلات مشفرة محلياً داخل قاعدة بيانات `database/haseen.db`.
- إضافة المتصفح تعمل عبر وسيط محلي مشفر على المنفذ `127.0.0.1:8089`.

**المطور**: SAIP Consulting  
**الترخيص**: MIT License
