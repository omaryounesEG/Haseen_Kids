import os
import sys
import time
import subprocess
import psutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_SCRIPT = os.path.join(BASE_DIR, "core", "service.py")
WATCHDOG_SCRIPT = os.path.join(BASE_DIR, "core", "watchdog.py")
UI_SCRIPT = os.path.join(BASE_DIR, "ui", "app.py")
PY_EXE = sys.executable

def is_script_running(script_name):
    target = os.path.normpath(script_name).lower()
    for p in psutil.process_iter(['pid', 'name']):
        try:
            cmd = ' '.join(p.cmdline()).lower()
            if target in cmd:
                return True
        except Exception:
            pass
    return False

def main():
    print("=" * 65)
    print("      🛡️  حَصِين للأطفال | Haseen Kids - الحماية الأسرية الذكية")
    print("=" * 65)

    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

    # 1. Start Service Daemon if not running
    if not is_script_running(SERVICE_SCRIPT):
        print("[1/3] تشغيل الخدمة الخلفية والبروكسي المحلي (Core Daemon)...")
        subprocess.Popen([PY_EXE, SERVICE_SCRIPT], creationflags=flags)
        time.sleep(1.5)
    else:
        print("[1/3] الخدمة الخلفية والبروكسي قيد التشغيل بالفعل ✅")

    # 2. Start Watchdog if not running
    if not is_script_running(WATCHDOG_SCRIPT):
        print("[2/3] تشغيل حارس المراقبة المزدوج (Mutual Watchdog)...")
        subprocess.Popen([PY_EXE, WATCHDOG_SCRIPT], creationflags=flags)
        time.sleep(1.0)
    else:
        print("[2/3] حارس المراقبة قيد التشغيل بالفعل ✅")

    # 3. Launch UI Application in foreground
    print("[3/3] فتح الواجهة الرسومية للبرنامج (UI Dashboard)...")
    print("=" * 65)
    subprocess.run([PY_EXE, UI_SCRIPT])

if __name__ == "__main__":
    main()
