# 🛡️ حَصِين للأطفال | Haseen Kids

> **نظام الحماية والرقابة الأسرية الذكي + مشغل يوتيوب معزول بدون إعلانات**
> *متوافق مع Windows 7 SP1 و 8 و 10 و 11*

**الإصدار الحالي: `1.3.1`** — [آخر إصدار | Latest release](https://github.com/omaryounesEG/Haseen_Kids/releases/latest)

---

## English (short version)

**Haseen Kids** is a Windows family-protection app for Arabic-speaking households:
a single whitelist that works on **every browser** (Chrome, Edge, Brave, Firefox),
an **isolated ad-free YouTube player**, an Arabic block page where the child asks and
the parent approves in one click (the site then opens by itself), and **fully offline
recovery/removal** even if the parent password is forgotten.

- **Requirements:** Windows 7 SP1 → 11, 4 GB RAM, Python 3.11 (installed by the setup).
- **Install (one line, CMD):**
  ```cmd
  curl -sSL https://raw.githubusercontent.com/omaryounesEG/Haseen_Kids/main/install_from_github.bat -o install_from_github.bat && install_from_github.bat
  ```
  or download the ZIP from [Releases](https://github.com/omaryounesEG/Haseen_Kids/releases/latest)
  and double-click `Setup.bat`.
- **Updates never wipe** the parent password or the lists: `database/haseen.db` is excluded
  from Git and from every update copy.
- **Forgotten password / removal (offline):** `Haseen_Remove.bat` → recovery key, or the
  Windows Administrator account, or the password.
- **Quality:** 58/58 automated tests passing; see `tests/BUG_REPORT.md` and `tests/UX_UI_REPORT.md`.
- **License:** MIT — **Built by:** SAIP Consulting.

اقرأ الشرح الكامل بالعربية أسفل الصفحة 👇

---

## 🚀 التثبيت السريع — طريقة واحدة فقط

نسخة جديدة من التثبيت: **ملف واحد، 4 خطوات معلنة، بلا إعدادات مخفية.**

### الطريقة الأولى (الأسهل): من داخل المجلد
انقر نقراً مزدوجاً على:

```
Setup.bat
```

المعالج يتولّى: البحث عن بايثون ← بناء البيئة ← تثبيت المكتبات ← فحص الجهاز والمتصفحات ←
كلمة مرور ولي الأمر ← **مفتاح الاسترجاع** ← فتح البرنامج وتسجيله في بدء التشغيل.

### الطريقة الثانية: من GitHub بسطر واحد

**CMD:**
```cmd
curl -sSL https://raw.githubusercontent.com/omaryounesEG/Haseen_Kids/main/install_from_github.bat -o install_from_github.bat && install_from_github.bat
```

**PowerShell:**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://raw.githubusercontent.com/omaryounesEG/Haseen_Kids/main/install_from_github.bat', 'install_from_github.bat'); .\install_from_github.bat"
```

> التحديث **لا يمسح** كلمة المرور ولا القوائم ولا السجلات (`database/haseen.db` مستثناة دائماً).

---

## 🆘 نسيان كلمة المرور / الحذف النهائي بدون إنترنت

انقر `Haseen_Remove.bat` (أو شغّل `scripts\reset_admin_pwd.bat`). ثلاث طرق مستقلة، **كلها تعمل بلا إنترنت**:

| الطريقة | كيف | متى تُستخدم |
|---|---|---|
| 🔑 **مفتاح الاسترجاع** | `Haseen_Remove.bat` ← اختر 2 ← الصق المفتاح (مثل `A1B2-C3D4-E5F6-G7H8`) | المفتاح معروض في المعالج ويُحفظ في `Documents\Haseen_Recovery_Key.txt` |
| 🪟 **حساب Administrator** | `Haseen_Remove.bat` ← اختر 3 (يطلب صلاحيات المسؤول) | لا مفتاح ولا بريد — يكفي حساب مسؤول ويندوز |
| 🔓 **كلمة المرور** | `Haseen_Remove.bat` ← اختر 1 | تتذكرها لكن تريد الحذف الكامل |

خيارات سريعة من سطر الأوامر:

```bat
python uninstall.py --status                       :: هل كلمة المرور/المفتاح مضبوطان؟
python uninstall.py --key A1B2-C3D4-E5F6-G7H8      :: إزالة نهائية بمفتاح الاسترجاع
python uninstall.py --admin                        :: إزالة نهائية بحساب المسؤول
python uninstall.py --delete-files --key ...       :: إزالة + حذف كل ملفات البرنامج
```

---

## ✨ المميزات

1. **قائمة بيضاء واحدة تعمل على كل المتصفحات** (Chrome / Edge / Brave / Firefox):
   الموقع المسموح يُفتح بكل صفحاته الفرعية (`app.classera.com`، `cdn.classera.com`…) وموارده.
2. **فيديو يوتيوب داخل الدرس يُفتح تلقائياً** — بدون حجب، وبدون انتظار موافقة:
   `/embed/` يعمل داخل الصفحة، و`/watch` ينتقل للمشغل النظيف، والباقي يمرّ.
3. **مشغل يوتيوب معزول بدون إعلانات** (SponsorBlock) وبث مباشر بلا تحميل مسبق.
4. **فلترة هرمية ثلاثية**: قوائم محلية فورية (<5ms) ← تحليل محلي ← فحص AI مشروط مع كاش.
5. **صفحة حجب عربية تفاعلية**: الطفل يطلب الإذن، ولي الأمر يوافق، والموقع يفتح تلقائياً بلا إعادة تحميل يدوية.
6. **لوحة ولي أمر كاملة**: جداول أوقات، قوائم، استثناءات مؤقتة، تقارير، تحديث بضغطة، عرض الإصدار الحالي مقابل GitHub.
7. **حارس مزدوج (Watchdog)** + أيقونة في صينية النظام؛ لا يمكن للطفل إغلاق البرنامج إلا بكلمة مرور.
7أ. **إيقاف مؤقت للحماية من الأيقونة المصغّرة** (زر يمين): 15 دقيقة / 30 دقيقة / ساعة / 4 ساعات
   بكلمة مرور ولي الأمر، ويعود الحجب تلقائياً عند انتهاء المدة (مع زر «استئناف الآن»).
8. **مفتاح استرجاع ومفتاح إزالة نهائية يعملان بدون إنترنت** حتى لو نُسيت كلمة المرور.
9. **واجهة أطفال**: ألوان مبهجة، خط IBM Plex Sans Arabic مكبّر، حواف دائرية، وشرح توضيحي (tooltip) لكل زر.
10. **لا يُغلق عند أي خطأ**: أي استثناء يُسجَّل في `logs\haseen_error.log` مع رسالة عربية واضحة
    والبرنامج يكمل عمله (كان أي خطأ ينهي البرنامج سابقاً)، وفحص البريد/API يعمل في الخلفية بلا تهنيج.
11. **إيقاف مؤقت ظاهر**: زر «⏸️ إيقاف مؤقت» أعلى النافذة + زر يمين على أيقونة الترس (15/30/ساعة/4 ساعات).

---

## 📁 أهم الملفات

| الملف | الوظيفة |
| :--- | :--- |
| `Setup.bat` | التثبيت الكامل بضغطة (بحث بايثون + مكتبات + معالج رسومي). |
| `Haseen_Remove.bat` | الاسترجاع أو الحذف النهائي بدون إنترنت (3 طرق). |
| `Repair.bat` | **إصلاح ذاتي**: يفحص/يعيد بناء البيئة ويعالج القاعدة مع نسخة احتياطية (لا يمسح كلمة المرور). |
| `install_from_github.bat` | تثبيت/تحديث من GitHub مع الحفاظ على قاعدة البيانات. |
| `scripts\run_all.bat` | تشغيل الخدمة + البروكسي + الحارس + الواجهة. |
| `scripts\update.bat` | تحديث فوري لآخر إصدار. |
| `scripts\reset_admin_pwd.bat` | إعادة تعيين كلمة المرور بصلاحيات المسؤول. |
| `tests\run_all_tests.py` | **36 اختباراً آلياً** (وظائف + أخطاء + واجهة + ميزات 1.2.0). |
| `tests\BUG_REPORT.md` | تقرير الأخطاء المكتشفة والمُصلحة. |
| `tests\UX_UI_REPORT.md` | تقرير تجربة الاستخدام والهوية البصرية. |

---

## 🔐 الأمان والخصوصية
- لا تُصدَّر أي بيانات تصفح خارج الجهاز؛ كل شيء محلي في `database/haseen.db`.
- الوسيط المحلي على `127.0.0.1:8089` فقط، ولا يستقبل اتصالات خارجية.
- كلمات المرور بـ **bcrypt**، والاستثناءات برموز **HMAC-SHA256**.
- الإصدار 1.2.0 أصلح ثغرة مسح كلمة المرور أثناء التحديث نهائياً.

**المطور**: SAIP Consulting — **الترخيص**: MIT
