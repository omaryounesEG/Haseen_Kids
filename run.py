import os
import sys
import socket
import time
import subprocess
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Always work from the program's own folder, never from wherever the shortcut,
# Explorer or a console happened to start us. Without this, launching from
# C:\Windows\System32 makes every relative path point at System32.
try:
    os.chdir(BASE_DIR)
except Exception:
    pass

SERVICE_SCRIPT = os.path.join(BASE_DIR, "core", "service.py")
WATCHDOG_SCRIPT = os.path.join(BASE_DIR, "core", "watchdog.py")
UI_SCRIPT = os.path.join(BASE_DIR, "ui", "app.py")
PY_EXE = sys.executable
PROXY_PORT = 8089

# Folders that look writable but are not (Windows redirects/protects them).
FORBIDDEN_ROOTS = (
    os.path.join(os.environ.get("SystemRoot", r"C:\Windows")).lower(),
    os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files")).lower(),
    os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")).lower(),
)


def is_bad_location(path=None):
    p = (path or BASE_DIR).lower()
    for root in FORBIDDEN_ROOTS:
        if root and p.startswith(root):
            return True
    return False


def port_in_use(port=PROXY_PORT):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.6):
            return True
    except Exception:
        return False


def clean_stale_pid_files():
    """Removes PID files left behind by a crashed session."""
    for fname in ("service.pid", "watchdog.pid"):
        pfile = os.path.join(BASE_DIR, "core", fname)
        if not os.path.exists(pfile):
            continue
        try:
            with open(pfile, "r", encoding="utf-8", errors="ignore") as fh:
                pid = int((fh.read() or "0").strip() or 0)
        except Exception:
            pid = 0
        alive = False
        if pid:
            try:
                import psutil
                alive = psutil.pid_exists(pid)
            except Exception:
                alive = False
        if not alive:
            try:
                os.remove(pfile)
            except Exception:
                pass


def check_install():
    """Returns a list of human-readable problems found before starting."""
    problems = []
    if not os.path.isdir(os.path.join(BASE_DIR, "core")):
        problems.append("مجلد core غير موجود بجوار run.py — النسخة غير مكتملة أو غير مستخرجة بالكامل.")
    if not os.path.exists(os.path.join(BASE_DIR, "database", "db_manager.py")):
        problems.append("ملفات قاعدة البيانات غير موجودة — استخرج الحزمة كاملة ثم شغّل Repair.bat.")
    if is_bad_location():
        problems.append(
            "البرنامج يعمل من مجلد محمي (" + BASE_DIR + ").\n"
            "هذا يمنع الحفظ في قاعدة البيانات ويجعل البرنامج يتوقف عن العمل.\n"
            "الحل: انقل مجلد البرنامج إلى مكان عادي مثل C:\\Haseen_Kids ثم شغّل Setup.bat.")
    return problems


def show_message(title, text):
    """Native message box so the message is seen even when started from a shortcut."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text, title, 0x00000030 | 0x00040000)
    except Exception:
        print(f"{title}: {text}")


def launch_detached(script):
    flags = 0
    if os.name == "nt":
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    return subprocess.Popen([PY_EXE, script], cwd=BASE_DIR, creationflags=flags)


def main():
    print("=" * 65)
    print("      [Haseen Kids] Smart Family Protection System")
    print("=" * 65)
    print(f"Base Directory: {BASE_DIR}")
    print(f"Python Runtime: {PY_EXE}\n")

    problems = check_install()
    for p in problems:
        print("[!] " + p.replace("\n", "\n    "))
    if any("محمي" in p for p in problems):
        print("\n[!] التشغيل من مجلد محمي غير مدعوم. لن يتم بدء الخدمات.")
        show_message("حَصِين للأطفال",
                     "البرنامج موجود داخل مجلد محمي (مثل C:\\Windows أو Program Files)."
                     + chr(10) + chr(10)
                     + "انقل مجلد البرنامج إلى مكان عادي مثل C:\\Haseen_Kids ثم شغّل Setup.bat."
                     + chr(10) + chr(10)
                     + "بدون ذلك لن يستطيع البرنامج حفظ الإعدادات.")
        return 2

    clean_stale_pid_files()

    already_running = port_in_use()
    if already_running:
        print("[i] Local proxy already listening on 127.0.0.1:%d — reusing it." % PROXY_PORT)
    else:
        print("[1/3] Starting Core Daemon & Local Proxy...")
        try:
            launch_detached(SERVICE_SCRIPT)
            for _ in range(20):
                if port_in_use():
                    break
                time.sleep(0.5)
            print("  -> Core Daemon " + ("ready." if port_in_use() else "still starting..."))
        except Exception as e:
            print(f"  -> Daemon launch notice: {e}")

        print("[2/3] Starting Mutual Watchdog...")
        try:
            launch_detached(WATCHDOG_SCRIPT)
            print("  -> Watchdog launched successfully.")
        except Exception as e:
            print(f"  -> Watchdog launch notice: {e}")

    print("[3/3] Launching Haseen Kids UI Dashboard...")
    print("=" * 65)
    try:
        ui_cmd = [PY_EXE, UI_SCRIPT] + [arg for arg in sys.argv[1:] if arg != "--help"]
        res = subprocess.run(ui_cmd, cwd=BASE_DIR)
        if res.returncode != 0:
            print(f"\n[!] UI process exited with code: {res.returncode}")
            log = os.path.join(BASE_DIR, "logs", "haseen_error.log")
            if os.path.exists(log):
                print(f"[!] آخر خطأ مُسجَّل في: {log}")
                try:
                    with open(log, "r", encoding="utf-8", errors="replace") as fh:
                        print(fh.read()[-1500:])
                except Exception:
                    pass
    except Exception:
        print("\n[!] Failed to launch UI process:")
        traceback.print_exc()



if __name__ == "__main__":
    try:
        main()
    except Exception:
        tb = traceback.format_exc()
        print(tb)
        try:
            os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
            with open(os.path.join(BASE_DIR, "logs", "run_error.log"), "a", encoding="utf-8") as fh:
                fh.write("\n" + time.strftime("%Y-%m-%d %H:%M:%S") + "\n" + tb)
        except Exception:
            pass
