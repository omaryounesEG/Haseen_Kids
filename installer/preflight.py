import os
import sys
import platform
import subprocess
import urllib.request
import winreg
import psutil

class SystemPreflightChecker:
    def __init__(self):
        self.os_version = platform.platform()
        self.is_win7 = "Windows-7" in self.os_version or platform.release() == "7"

    def check_system_resources(self):
        """Checks RAM and CPU to ensure smooth operation"""
        mem = psutil.virtual_memory()
        total_ram_gb = round(mem.total / (1024 ** 3), 2)
        avail_ram_gb = round(mem.available / (1024 ** 3), 2)
        cpu_count = psutil.cpu_count(logical=True)
        return {
            "os": self.os_version,
            "is_win7": self.is_win7,
            "total_ram_gb": total_ram_gb,
            "avail_ram_gb": avail_ram_gb,
            "cpu_cores": cpu_count,
            "sufficient_ram": total_ram_gb >= 1.5
        }

    def detect_browsers(self):
        """Scans system for Chrome, Edge, Firefox, and Brave"""
        browsers = {
            "chrome": {"name": "Google Chrome", "installed": False, "path": ""},
            "edge": {"name": "Microsoft Edge", "installed": False, "path": ""},
            "brave": {"name": "Brave Browser", "installed": False, "path": ""},
            "firefox": {"name": "Mozilla Firefox", "installed": False, "path": ""}
        }

        # Check standard paths
        search_paths = {
            "chrome": [
                os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe")
            ],
            "edge": [
                os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
                os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe")
            ],
            "brave": [
                os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\BraveSoftware\Brave-Browser\Application\brave.exe"),
                os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe")
            ],
            "firefox": [
                os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe")
            ]
        }

        for b_id, paths in search_paths.items():
            for p in paths:
                if os.path.isfile(p):
                    browsers[b_id]["installed"] = True
                    browsers[b_id]["path"] = p
                    break

        return browsers

    def download_and_install_brave(self, progress_callback=None):
        """
        Downloads official Brave standalone silent installer and installs it if missing.
        """
        installer_url = "https://laptop-updates.brave.com/latest/winx64"
        temp_dir = os.environ.get("TEMP", "C:\\Temp")
        installer_path = os.path.join(temp_dir, "BraveStandaloneSetup.exe")

        try:
            if progress_callback:
                progress_callback("جاري تحميل متصفح Brave الرسمي الآمن من الموقع المعتمد...")

            def reporthook(blocknum, blocksize, totalsize):
                if progress_callback and totalsize > 0:
                    percent = min(100, int((blocknum * blocksize / totalsize) * 100))
                    progress_callback(f"جاري تحميل متصفح Brave ({percent}%)...")

            urllib.request.urlretrieve(installer_url, installer_path, reporthook=reporthook)

            if progress_callback:
                progress_callback("جاري تثبيت متصفح Brave في صمت...")

            # Run silent installer
            cmd = f'"{installer_path}" /silent /install'
            res = subprocess.run(cmd, shell=True, capture_output=True)

            # Check if installed
            browsers = self.detect_browsers()
            if browsers["brave"]["installed"]:
                return True, "تم تثبيت متصفح Brave بنجاح ✅"
            else:
                return True, "اكتمل التثبيت، يرجى إعادة فحص المتصفحات."
        except Exception as e:
            return False, f"تعذر تحميل أو تثبيت Brave تلقائياً: {str(e)}"

    def setup_firewall_rules_automatic(self):
        """Configures Windows Firewall loopback rule for proxy and Python"""
        try:
            py_exe = sys.executable
            # Allow Python inbound
            cmd1 = f'netsh advfirewall firewall add rule name="Haseen_Python_Allow" dir=in action=allow program="{py_exe}" profile=any enable=yes'
            # Allow port 8089 inbound
            cmd2 = 'netsh advfirewall firewall add rule name="Haseen_Port_8089" dir=in action=allow protocol=TCP localport=8089 profile=any enable=yes'
            subprocess.run(cmd1, shell=True, capture_output=True)
            subprocess.run(cmd2, shell=True, capture_output=True)
            return True, "تم إعداد جدار حماية ويندوز تلقائياً بنجاح ✅"
        except Exception as e:
            return False, f"ملاحظة جدار الحماية: {str(e)}"

if __name__ == "__main__":
    checker = SystemPreflightChecker()
    res = checker.check_system_resources()
    print("Resources:", res)
    browsers = checker.detect_browsers()
    for b, info in browsers.items():
        print(f"Browser {info['name']}: Installed={info['installed']}")
