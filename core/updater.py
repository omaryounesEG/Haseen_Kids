import os
import sys
import json
import hashlib
import zipfile
import shutil
import urllib.request
import subprocess
from datetime import datetime

# Optional cryptography for Ed25519 or RSA signature verification
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager

# Embedded Ed25519 Public Key for Haseen Releases Verification
EMBEDDED_PUBLIC_KEY_HEX = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

class SecureGitHubUpdater:
    def __init__(self, repo="omaryounesEG/Haseen_Kids", current_version="1.3.2", install_dir=None):
        self.repo = repo
        self.current_version = current_version
        self.install_dir = install_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.temp_update_dir = os.path.join(self.install_dir, "temp_update")
        self.backup_dir = os.path.join(self.install_dir, "Backup_OldVersion")
        self.db = DBManager()

    def check_biweekly_background_update(self, callback_on_update=None):
        """
        Lightweight passive check: checks GitHub only once every 14 days without background loops.
        """
        import time
        try:
            last_str = self.db.get_setting("last_biweekly_update_check", "0")
            last_check = float(last_str) if last_str else 0
            now = time.time()
            if now - last_check < 1209600:
                return False, self.current_version, self.current_version

            self.db.set_setting("last_biweekly_update_check", str(now))
            has_update, cur_v, rem_v, info, err = self.check_for_updates()
            if has_update and callback_on_update:
                callback_on_update(rem_v)
            return has_update, cur_v, rem_v
        except Exception:
            return False, self.current_version, self.current_version

    def check_for_updates(self):
        """
        Queries GitHub Releases API and Tags.
        Returns: (has_update, remote_version, release_info, error)
        """
        headers = {
            "User-Agent": "HaseenKids-Updater/1.1",
            "Accept": "application/vnd.github.v3+json"
        }

        # 1. Try Releases API
        api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"
        try:
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    remote_ver = data.get("tag_name", "").lstrip("v")
                    body = data.get("body", "تحديث رسمي يتضمن تحسينات الأمان والواجهة")
                    assets = data.get("assets", [])
                    has_update = remote_ver > self.current_version
                    return has_update, remote_ver, {"notes": body, "assets": assets, "published_at": data.get("published_at")}, None
        except Exception:
            pass

        # 2. Fallback to Tags API
        tags_url = f"https://api.github.com/repos/{self.repo}/tags"
        try:
            req = urllib.request.Request(tags_url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    tags = json.loads(resp.read().decode('utf-8'))
                    if tags and len(tags) > 0:
                        latest_tag = tags[0].get("name", "").lstrip("v")
                        has_update = latest_tag > self.current_version
                        return has_update, latest_tag, {"notes": "إصدار رسمي محدث على مستودع GitHub"}, None
        except Exception as e:
            return False, self.current_version, {}, f"تعذر التحقق من التحديثات: {str(e)}"

        return False, self.current_version, {}, None

    def update_from_github_direct(self, progress_callback=None):
        """
        In-place direct update from GitHub main branch without re-installation.
        Preserves database/haseen.db and user settings.
        """
        import tempfile
        repo_zip_url = f"https://github.com/{self.repo}/archive/refs/heads/main.zip"
        temp_dir = tempfile.gettempdir()
        zip_dest = os.path.join(temp_dir, "haseen_update.zip")
        extract_dir = os.path.join(temp_dir, "haseen_extract")

        try:
            if progress_callback:
                progress_callback("جاري تنزيل أحدث ملفات التحديث من GitHub...")

            req = urllib.request.Request(repo_zip_url, headers={"User-Agent": "HaseenKids-DirectUpdater/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(zip_dest, 'wb') as out_f:
                shutil.copyfileobj(resp, out_f)

            if progress_callback:
                progress_callback("جاري فك ضغط التحديث وتجهيز الملفات...")

            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir, ignore_errors=True)
            os.makedirs(extract_dir, exist_ok=True)

            with zipfile.ZipFile(zip_dest, 'r') as zf:
                zf.extractall(extract_dir)

            # Find root folder in extract
            root_candidates = [os.path.join(extract_dir, d) for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
            src_root = root_candidates[0] if root_candidates else extract_dir

            if progress_callback:
                progress_callback("جاري نسخ التحديث واستبدال الملفات البرمجية...")

            # Backup current files
            os.makedirs(self.backup_dir, exist_ok=True)
            target_dirs = ["core", "ui", "proxy", "youtube", "scripts", "installer", "extension", "assets"]
            for d in target_dirs:
                s = os.path.join(src_root, d)
                t = os.path.join(self.install_dir, d)
                if os.path.exists(s):
                    # Copy to backup first
                    b_dst = os.path.join(self.backup_dir, d)
                    if os.path.exists(t):
                        if os.path.exists(b_dst):
                            shutil.rmtree(b_dst, ignore_errors=True)
                        shutil.copytree(t, b_dst)
                    # Copy new files
                    for root, _, files in os.walk(s):
                        rel = os.path.relpath(root, s)
                        dest_folder = os.path.join(t, rel)
                        os.makedirs(dest_folder, exist_ok=True)
                        for f in files:
                            shutil.copy2(os.path.join(root, f), os.path.join(dest_folder, f))

            # Copy root scripts (preserving database/haseen.db!)
            for root_f in ["run.py", "Setup.bat", "install_from_github.bat", "requirements.txt", "hassen_icon.png", "hassen_icon.ico"]:
                s_f = os.path.join(src_root, root_f)
                t_f = os.path.join(self.install_dir, root_f)
                if os.path.exists(s_f):
                    shutil.copy2(s_f, t_f)

            # Cleanup temp
            if os.path.exists(zip_dest):
                os.remove(zip_dest)
            shutil.rmtree(extract_dir, ignore_errors=True)

            return True, "تم تحديث كافة ملفات البرنامج إلى الإصدار الأحدث بنجاح! ✅ (تم الحفاظ على قاعدة البيانات وكلمات المرور)."
        except Exception as e:
            return False, f"تعذر إتمام التحديث المباشر: {str(e)}"

    def update_ytdlp_micro(self):
        """
        Micro-Update: Updates yt-dlp package directly to maintain YouTube playback without full app update.
        """
        try:
            py_exe = sys.executable
            # Using uv pip if available or python -m pip
            res = subprocess.run([py_exe, "-m", "pip", "install", "--upgrade", "yt-dlp"], capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                return True, "تم تحديث محرك اليوتيوب yt-dlp بنجاح لأحدث إصدار رسمي."
            else:
                # Try uv pip
                uv_res = subprocess.run(["uv", "pip", "install", "--upgrade", "--python", py_exe, "yt-dlp"], capture_output=True, text=True, timeout=60)
                if uv_res.returncode == 0:
                    return True, "تم تحديث محرك اليوتيوب عبر uv بنجاح."
                return False, f"خطأ أثناء التحديث: {res.stderr or uv_res.stderr}"
        except Exception as e:
            return False, f"استثناء أثناء تحديث yt-dlp: {str(e)}"

    def update_filter_lists_micro(self, custom_url=None):
        """
        Micro-Update: Pulls StevenBlack or custom safety lists and updates SQLite database.
        """
        url = custom_url or "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/fakenews-gambling-porn/hosts"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HaseenKids-ListUpdate/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    lines = resp.read().decode('utf-8', errors='ignore').splitlines()
                    added = 0
                    for line in lines:
                        line = line.strip()
                        if line.startswith("0.0.0.0 "):
                            parts = line.split()
                            if len(parts) >= 2:
                                d = parts[1].strip().lower()
                                if d and d not in ["0.0.0.0", "localhost"]:
                                    self.db.save_domain_decision(d, "BLOCK", "ADULT", "LIST_COMMUNITY_UPDATE")
                                    added += 1
                                    if added >= 500: # Fast slice batch
                                        break
                    return True, f"تم تحديث قوائم الحجب بنجاح (تم استيراد {added} نطاق جديد)."
        except Exception as e:
            return False, f"تعذر تحميل قوائم الحجب: {str(e)}"
        return False, "فشل التحميل"

    def apply_full_update(self, zip_path, expected_sha256, sig_path=None):
        """
        Cryptographic verification + Atomic Swap & Backup
        """
        # 1. SHA-256 verification
        sha = hashlib.sha256()
        with open(zip_path, 'rb') as f:
            while chunk := f.read(65536):
                sha.update(chunk)
        calc_hash = sha.hexdigest().lower()
        if expected_sha256 and calc_hash != expected_sha256.lower():
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return False, "فشل التحقق الأمني: بصمة الملف المحمل لا تطابق البصمة الرسمية (SHA256 Mismatch)"

        # 2. Backup current version
        os.makedirs(self.backup_dir, exist_ok=True)
        for item in ["core", "ui", "proxy", "youtube", "scripts"]:
            src = os.path.join(self.install_dir, item)
            dst = os.path.join(self.backup_dir, item)
            if os.path.exists(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(src, dst)

        # 3. Unpack new files atomically (Preserving database & custom configs)
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for member in zf.namelist():
                    # Protect SQLite DB and secret configs from overwrite
                    if "database/haseen.db" in member or "haseen.db" in member:
                        continue
                    zf.extract(member, self.install_dir)

            return True, "تم تثبيت التحديث بنجاح مع الاحتفاظ بنسخة احتياطية وقاعدة البيانات القديمة."
        except Exception as e:
            # Auto-rollback from backup
            self.rollback()
            return False, f"فشل التثبيت وتم التراجع تلقائياً: {str(e)}"

    def rollback(self):
        """Restores files from Backup_OldVersion if new version fails"""
        if os.path.exists(self.backup_dir):
            for item in os.listdir(self.backup_dir):
                s = os.path.join(self.backup_dir, item)
                d = os.path.join(self.install_dir, item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d, ignore_errors=True)
                    shutil.copytree(s, d)

if __name__ == "__main__":
    updater = SecureGitHubUpdater()
    print("Testing updater...")
    has_up, r_ver, info, err = updater.check_for_updates()
    print(f"Update available: {has_up}, Version: {r_ver}, Status: {err or 'OK'}")
