import os
import sys
import time
import subprocess
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

SERVICE_SCRIPT = os.path.join(BASE_DIR, "core", "service.py")
WATCHDOG_SCRIPT = os.path.join(BASE_DIR, "core", "watchdog.py")
UI_SCRIPT = os.path.join(BASE_DIR, "ui", "app.py")
PY_EXE = sys.executable

def clean_stale_pid_files():
    """Removes dead PID files left by aborted sessions"""
    for fname in ["service.pid", "watchdog.pid"]:
        pfile = os.path.join(BASE_DIR, "core", fname)
        if os.path.exists(pfile):
            try:
                os.remove(pfile)
            except Exception:
                pass

def main():
    print("=" * 65)
    print("      🛡️  حَصِين للأطفال | Haseen Kids - الحماية الأسرية الذكية")
    print("=" * 65)
    print(f"المسار الرئيسي: {BASE_DIR}")
    print(f"مفسر بايثون: {PY_EXE}\n")

    # Clean old locks
    clean_stale_pid_files()

    flags = 0
    if os.name == 'nt':
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

    # 1. Start Service Daemon
    print("[1/3] تشغيل الخدمة الخلفية والبروكسي المحلي (Core Daemon)...")
    try:
        subprocess.Popen([PY_EXE, SERVICE_SCRIPT], cwd=BASE_DIR, creationflags=flags)
        print("  -> تم إطلاق الخدمة بنجاح ✅")
    except Exception as e:
        print(f"  -> تعذر إطلاق الخدمة كعملية منفصلة: {e}")

    # 2. Start Watchdog
    print("[2/3] تشغيل حارس المراقبة المزدوج (Mutual Watchdog)...")
    try:
        subprocess.Popen([PY_EXE, WATCHDOG_SCRIPT], cwd=BASE_DIR, creationflags=flags)
        print("  -> تم إطلاق حارس المراقبة بنجاح ✅")
    except Exception as e:
        print(f"  -> تعذر إطلاق الحارس: {e}")

    # 3. Launch UI Application in foreground
    print("[3/3] فتح الواجهة الرسومية للبرنامج (UI Dashboard)...")
    print("=" * 65)
    try:
        res = subprocess.run([PY_EXE, UI_SCRIPT], cwd=BASE_DIR)
        if res.returncode != 0:
            print(f"\n⚠️ انتهت الواجهة برمز خروج: {res.returncode}")
    except Exception as e:
        print("\n❌ حدث خطأ أثناء تشغيل الواجهة الرسومية:")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
