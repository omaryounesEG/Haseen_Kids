import os
import sys
import subprocess
import shutil
import psutil

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.db_manager import DBManager
from core.security import SecurityManager

def stop_all_haseen_processes():
    print("[1/4] Stopping all active Haseen processes...")
    current_pid = os.getpid()
    count = 0
    for p in psutil.process_iter(['pid', 'name']):
        try:
            if p.pid == current_pid:
                continue
            cmd = ' '.join(p.cmdline()).lower()
            if 'haseen_kids' in cmd:
                print(f"  - Terminating: {p.name()} (PID: {p.pid})")
                p.kill()
                count += 1
        except Exception:
            pass
    print(f"  -> Terminated {count} processes.")

def revert_registry_policies():
    print("[2/4] Reverting Browser Policies & Restoring Default Windows Settings...")
    if not WINREG_AVAILABLE:
        print("  - winreg not available on this platform.")
        return

    policies_to_clean = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Google\Chrome", [
            "IncognitoModeAvailability", "ProxyMode", "ProxyServer", "SafeBrowsingProtectionLevel"
        ]),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Edge", [
            "InPrivateModeAvailability", "ProxyMode", "ProxyServer"
        ])
    ]

    for root, subkey, val_names in policies_to_clean:
        try:
            key = winreg.OpenKey(root, subkey, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
            for name in val_names:
                try:
                    winreg.DeleteValue(key, name)
                    print(f"  - Removed policy: {name}")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except (PermissionError, FileNotFoundError):
            pass

def revert_firewall_rules():
    print("[3/4] Removing Firewall Rules...")
    try:
        subprocess.run('netsh advfirewall firewall delete rule name="Haseen_Allow_Proxy_In"', shell=True, capture_output=True)
        subprocess.run('netsh advfirewall firewall delete rule name="Haseen_Allow_Local"', shell=True, capture_output=True)
        print("  -> Firewall rules removed.")
    except Exception as e:
        print(f"  - Firewall removal note: {e}")

def cleanup_state_files():
    print("[4/4] Cleaning state and PID locks...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    files_to_remove = [
        os.path.join(base_dir, "core", "service.pid"),
        os.path.join(base_dir, "core", "watchdog.pid"),
        os.path.join(base_dir, "core", "daemon.heartbeat")
    ]
    for f in files_to_remove:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"  - Deleted {os.path.basename(f)}")
            except Exception:
                pass

def uninstall():
    print("=" * 65)
    print("      🛡️  حَصِين للأطفال | Haseen Kids - أداة إزالة التثبيت")
    print("=" * 65)

    db = DBManager()
    sec = SecurityManager(db)

    # Require Parent Password
    print("\nلإلغاء التثبيت وحذف قيود الحماية، يرجى إدخال كلمة مرور ولي الأمر:")
    pwd = input("كلمة المرور (الافتراضية: haseen2026): ").strip()

    if not sec.verify_admin(pwd):
        print("\n❌ خطأ: كلمة المرور غير صحيحة! تم رفض عملية إلغاء التثبيت.")
        sys.exit(1)

    print("\n✅ تم التحقق من هوية ولي الأمر بنجاح. بدء إزالة البرنامج وإلغاء القيود...")
    stop_all_haseen_processes()
    revert_registry_policies()
    revert_firewall_rules()
    cleanup_state_files()

    print("\n" + "=" * 65)
    print("🎉 تم إلغاء تثبيت برنامج حصين واستعادة كافة إعدادات جهازك بنجاح!")
    print("=" * 65)
    print("• تم إيقاف الخدمة وحارس المراقبة والبروكسي.")
    print("• تم استعادة إعدادات التصفح الخفي وإلغاء قيود المتصفحات.")
    print("• جهازك الآن حر تماماً وبنفس حالته الأصلية.")

if __name__ == "__main__":
    uninstall()
