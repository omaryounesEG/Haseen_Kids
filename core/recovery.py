"""
Offline recovery & removal helpers for Haseen Kids.

The parent must always be able to undo everything **without internet and even
with a forgotten password**. Three independent offline paths are supported:

1. Recovery Key  - a 16-character key generated at install time and shown to the
                   parent once (printed / saved to a text file).
2. Windows Admin - elevating to Administrator proves an adult owns the PC.
3. Password      - the normal admin password.

All three lead to `full_remove()` which reverts every change the program made.
"""

import os
import sys
import secrets
import string
import hashlib
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

KEY_FILE = os.path.join(BASE_DIR, "recovery.sig")

KEY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no I/O/0/1 to avoid misreading


def _format_key(raw):
    """ABCD-EFGH-JKLM-NPQR"""
    return "-".join(raw[i:i + 4] for i in range(0, len(raw), 4))


def generate_recovery_key():
    """Creates a new random 16-char recovery key (formatted for handwriting)."""
    raw = "".join(secrets.choice(KEY_ALPHABET) for _ in range(16))
    return _format_key(raw)


def normalize_key(key):
    """Uppercases and strips separators so 'hsn7 k3m9...' still verifies."""
    return "".join(ch for ch in (key or "").upper() if ch.isalnum())


def _hash_key(key):
    return hashlib.sha256(normalize_key(key).encode("utf-8")).hexdigest()


def store_recovery_key(db, key):
    """Stores the key hash in the DB and a copy beside the app (survives DB loss)."""
    from core.security import SecurityManager
    db.set_setting("recovery_key_hash", SecurityManager.hash_password(normalize_key(key)))
    try:
        with open(KEY_FILE, "w", encoding="utf-8") as f:
            f.write(_hash_key(key))
    except Exception:
        pass
    return True


def verify_recovery_key(db, key):
    """True if the key matches either the DB hash or the on-disk signature."""
    from core.security import SecurityManager
    normalized = normalize_key(key)
    if len(normalized) != 16:
        return False

    stored = db.get_setting("recovery_key_hash", "") if db else ""
    if stored and SecurityManager.verify_password(normalized, stored):
        return True

    try:
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "r", encoding="utf-8") as f:
                if f.read().strip() == _hash_key(key):
                    return True
    except Exception:
        pass
    return False


def write_recovery_note(key, version="1.3.1"):
    """Writes a printable note to Documents and returns its path."""
    folder = os.path.join(os.path.expanduser("~"), "Documents")
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception:
        folder = BASE_DIR
    path = os.path.join(folder, "Haseen_Kids_RecoveryKey.txt")
    content = (
        "=====================================================\n"
        "   حَصِين للأطفال | HASEEN KIDS\n"
        "   مفتاح الاسترجاع / Recovery Key\n"
        "=====================================================\n\n"
        f"  مفتاح الاسترجاع:  {key}\n\n"
        "  احتفظ بهذه الورقة في مكان آمن ولا تعطها للطفل.\n"
        "  هذا المفتاح يسمح بإزالة البرنامج أو إعادة تعيين كلمة المرور\n"
        "  حتى لو نسيت كلمة المرور ولا يوجد اتصال بالإنترنت.\n\n"
        "  طريقة الاستخدام:\n"
        "  1) شغّل Haseen_Remove.bat من مجلد البرنامج\n"
        "  2) اختر: [2] استرجاع بمفتاح الاسترجاع\n"
        "  3) اكتب المفتاح أعلاه\n\n"
        f"  الإصدار: {version}\n"
        "=====================================================\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ---------------------------------------------------------------------------
# Removal
# ---------------------------------------------------------------------------
def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate_and_run(extra_args=""):
    """Re-launches this script elevated (UAC). Returns True if it spawned."""
    try:
        import ctypes
        params = f'"{os.path.abspath(sys.argv[0])}" --full {extra_args}'
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, BASE_DIR, 1)
        return rc > 32
    except Exception:
        return False


def kill_haseen_processes():
    killed = 0
    try:
        import psutil
        me = os.getpid()
        for p in psutil.process_iter(['pid', 'cmdline']):
            try:
                if p.pid == me:
                    continue
                cmd = " ".join(p.info.get('cmdline') or []).lower()
                if "haseen" in cmd and ("run.py" in cmd or "service.py" in cmd or
                                        "watchdog.py" in cmd or "ui\\app.py" in cmd or "ui/app.py" in cmd):
                    p.kill()
                    killed += 1
            except Exception:
                pass
    except Exception:
        pass
    return killed


def revert_browser_policies():
    """Removes the proxy/incognito policies for Chrome, Edge, Brave, Chromium."""
    removed = 0
    try:
        import winreg
    except ImportError:
        return 0

    targets = [
        (r"SOFTWARE\Policies\Google\Chrome", None),
        (r"SOFTWARE\Policies\Microsoft\Edge", None),
        (r"SOFTWARE\Policies\BraveSoftware\Brave", None),
        (r"SOFTWARE\Policies\Chromium", None),
    ]
    values = ["ProxyMode", "ProxyServer", "ProxyPacUrl", "ProxyBypassList",
              "IncognitoModeAvailability", "InPrivateModeAvailability",
              "URLBlocklist", "URLAllowlist", "SafeSearchesEnabled", "ForceSafeSearch"]
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for subkey, _ in targets:
            try:
                key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
            except FileNotFoundError:
                continue
            except PermissionError:
                continue
            for name in values:
                try:
                    winreg.DeleteValue(key, name)
                    removed += 1
                except FileNotFoundError:
                    pass
                except PermissionError:
                    pass
            try:
                winreg.CloseKey(key)
            except Exception:
                pass
    return removed


def revert_firewall_rules():
    removed = 0
    rules = ["Haseen_Allow_Proxy_In", "Haseen_Allow_Local", "Haseen Kids Proxy",
             "Haseen_Block_DNS_Alt", "Haseen_Allow_8089"]
    for name in rules:
        try:
            r = subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={name}"],
                capture_output=True, text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            if "Ok" in (r.stdout or "") or "Deleted" in (r.stdout or ""):
                removed += 1
        except Exception:
            pass
    return removed


def remove_autostart():
    """Removes startup folder shortcuts and the HKCU Run entry."""
    removed = 0
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "HaseenKids")
        winreg.CloseKey(key)
        removed += 1
    except Exception:
        pass

    for folder in [
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup"),
        os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
    ]:
        try:
            for f in os.listdir(folder):
                if f.lower().startswith(("haseenkids", "حصين", "حَصِين")) and f.lower().endswith(".lnk"):
                    os.remove(os.path.join(folder, f))
                    removed += 1
        except Exception:
            pass
    return removed


def remove_state_files():
    removed = 0
    for rel in ["core/service.pid", "core/watchdog.pid", "core/daemon.heartbeat",
                "temp_update", "Backup_OldVersion", "recovery.sig"]:
        p = os.path.join(BASE_DIR, rel)
        try:
            if os.path.isdir(p):
                import shutil
                shutil.rmtree(p, ignore_errors=True)
                removed += 1
            elif os.path.exists(p):
                os.remove(p)
                removed += 1
        except Exception:
            pass
    return removed


def full_remove(delete_folder=False):
    """Reverts every change and returns a summary dict."""
    summary = {
        "processes": kill_haseen_processes(),
        "policies": revert_browser_policies(),
        "firewall": revert_firewall_rules(),
        "autostart": remove_autostart(),
        "state": remove_state_files(),
    }
    if delete_folder:
        summary["folder"] = schedule_self_delete()
    return summary


def schedule_self_delete():
    """Deletes the install folder after this process exits (Windows-safe)."""
    bat = os.path.join(os.environ.get("TEMP", BASE_DIR), "haseen_selfdelete.bat")
    try:
        with open(bat, "w", encoding="utf-8") as f:
            f.write("@echo off\r\n")
            f.write("timeout /t 2 /nobreak >nul\r\n")
            f.write(f'rmdir /s /q "{BASE_DIR}"\r\n')
            f.write('del /f /q "%~f0"\r\n')
        subprocess.Popen(["cmd", "/c", "start", "", "/min", bat], shell=False)
        return True
    except Exception:
        return False
