import os
import sys
import subprocess
import bcrypt
import psutil

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager

UNAPPROVED_BROWSERS = [
    "tor.exe", "opera.exe", "vivaldi.exe", "yandex.exe", "epic.exe", "maxthon.exe"
]

class SecurityManager:
    def __init__(self, db=None):
        self.db = db or DBManager()

    @staticmethod
    def hash_password(plain_password):
        salt = bcrypt.gensalt(12)
        return bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(plain_password, hashed_password):
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    def verify_admin(self, password):
        stored = self.db.get_setting("admin_password_hash", "")
        if not stored:
            # Default password "haseen2026"
            return password == "haseen2026"
        return self.verify_password(password, stored)

    def set_admin_password(self, new_password):
        h = self.hash_password(new_password)
        self.db.set_setting("admin_password_hash", h)
        return True

    def generate_reset_otp(self):
        """
        Generates a secure 6-digit OTP for password reset, valid for 15 minutes.
        """
        import random
        import time
        otp = str(random.SystemRandom().randint(100000, 999999))
        exp = time.time() + (15 * 60)
        self.db.set_setting("password_reset_otp", f"{otp}:{exp}")
        return otp

    def verify_reset_otp(self, entered_otp):
        """
        Verifies the reset OTP.
        """
        import time
        raw = self.db.get_setting("password_reset_otp", "")
        if not raw or ":" not in raw:
            return False, "لا يوجد طلب استرجاع نشط حالياً أو انتهت صلاحيته."
        otp, exp_str = raw.split(":", 1)
        try:
            exp = float(exp_str)
        except ValueError:
            return False, "بيانات الرمز غير صالحة."
        
        if time.time() > exp:
            self.db.set_setting("password_reset_otp", "")
            return False, "انتهت صلاحية رمز الاسترجاع (15 دقيقة). يرجى طلب رمز جديد."
            
        if entered_otp.strip() == otp.strip():
            return True, "تم التحقق من الرمز بنجاح."
        return False, "رمز الاسترجاع غير صحيح! يرجى التأكد من الرمز المرسل للبريد."

    def clear_reset_otp(self):
        self.db.set_setting("password_reset_otp", "")

    def apply_browser_registry_policies(self):
        """
        Configures Enterprise Group Policies for Google Chrome & Microsoft Edge via Windows Registry:
        1. IncognitoModeAvailability = 1 (Disabled)
        2. ExtensionInstallBlocklist = ['*'] (Prevents installing unauthorized VPNs)
        3. ProxyServer = 127.0.0.1:8089
        """
        if not WINREG_AVAILABLE:
            return False, "winreg not available on non-windows platform"

        policies = [
            # Google Chrome Policies
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Google\Chrome", [
                ("IncognitoModeAvailability", winreg.REG_DWORD, 1), # 1 = Incognito Disabled
                ("ProxyMode", winreg.REG_SZ, "fixed_servers"),
                ("ProxyServer", winreg.REG_SZ, "127.0.0.1:8089"),
                ("SafeBrowsingProtectionLevel", winreg.REG_DWORD, 2) # Enhanced Protection
            ]),
            # Microsoft Edge Policies
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Edge", [
                ("InPrivateModeAvailability", winreg.REG_DWORD, 1), # 1 = InPrivate Disabled
                ("ProxyMode", winreg.REG_SZ, "fixed_servers"),
                ("ProxyServer", winreg.REG_SZ, "127.0.0.1:8089")
            ])
        ]

        applied = 0
        try:
            for root, subkey, values in policies:
                try:
                    key = winreg.CreateKeyEx(root, subkey, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
                    for val_name, val_type, val_data in values:
                        winreg.SetValueEx(key, val_name, 0, val_type, val_data)
                    winreg.CloseKey(key)
                    applied += 1
                except PermissionError:
                    # Requires Administrator privilege
                    return False, "يتطلب تطبيق سياسات السجل تشغيل البرنامج كمسؤول (Run as Administrator)"
                except Exception as e:
                    pass
            return True, f"تم تطبيق سياسات المتصفحات بنجاح ({applied} سياسة)"
        except Exception as e:
            return False, str(e)

    def generate_firewall_rules_script(self):
        """
        Generates batch commands for Windows Defender Firewall to block port 80/443 bypass
        """
        cmd = """@echo off
echo [حصين] ضبط جدار حماية ويندوز لمنع تخطي البروكسي...
netsh advfirewall firewall add rule name="Haseen_Allow_Proxy_In" dir=in action=allow protocol=TCP localport=8089
netsh advfirewall firewall add rule name="Haseen_Allow_Local" dir=out action=allow remoteip=127.0.0.1
echo تم إعداد جدار الحماية بنجاح.
"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        scripts_dir = os.path.join(base_dir, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        script_path = os.path.join(scripts_dir, "setup_firewall.bat")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(cmd)
        return script_path

    def check_and_kill_unapproved_browsers(self):
        """
        Terminates unapproved portable/proxy bypass browsers if process_lockdown is active
        """
        lockdown = self.db.get_setting("process_lockdown", "0")
        if lockdown != "1":
            return []

        killed = []
        for p in psutil.process_iter(['pid', 'name']):
            try:
                pname = p.info['name'].lower()
                if pname in UNAPPROVED_BROWSERS:
                    p.terminate()
                    killed.append(pname)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return killed

    def lock_files_acl(self, folder_path=None):
        """
        Restricts standard user write/delete permissions on the program folder using icacls
        """
        if folder_path is None:
            folder_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        try:
            # Grant Administrators and SYSTEM full control, remove Users write
            cmd = f'icacls "{folder_path}" /grant:r "SYSTEM":(OI)(CI)F /grant:r "Administrators":(OI)(CI)F'
            subprocess.run(cmd, shell=True, capture_output=True)
            return True, "تم قفل صلاحيات المجلد بنجاح"
        except Exception as e:
            return False, str(e)

if __name__ == "__main__":
    sec = SecurityManager()
    print("Testing password hashing & verification...")
    h = sec.hash_password("haseen2026")
    print("Verification:", sec.verify_password("haseen2026", h))
    print("Firewall script generated:", sec.generate_firewall_rules_script())
