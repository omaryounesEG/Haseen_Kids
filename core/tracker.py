import time
import os
import sys
import psutil
from datetime import datetime

try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager

SCHOOL_KEYWORDS = [
    "مدرستي", "وزارة التربية", "بنك المعرفة", "classroom", "teams", "word",
    "powerpoint", "excel", "khan", "wikipedia", "edmodo", "duolingo", "scratch",
    "nafham", "نفهم", "school"
]

ENTERTAINMENT_KEYWORDS = [
    "youtube", "roblox", "minecraft", "steam", "discord", "twitch", "fortnite",
    "tiktok", "instagram", "facebook", "netflix", "anime", "playstation", "epic games"
]

class ActiveWindowTracker:
    def __init__(self, db=None, poll_interval=5):
        self.db = db or DBManager()
        self.poll_interval = poll_interval
        self.running = False

    def get_active_window_info(self):
        """Returns (window_title, process_name, pid)"""
        if not WIN32_AVAILABLE:
            return "Unknown Window", "unknown.exe", 0
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return "", "", 0
            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc_name = ""
            if pid > 0:
                try:
                    proc_name = psutil.Process(pid).name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    proc_name = "system"
            return title, proc_name, pid
        except Exception:
            return "", "", 0

    def classify_window(self, title, proc_name):
        text = f"{title} {proc_name}".lower()

        for kw in SCHOOL_KEYWORDS:
            if kw in text:
                return "SCHOOL"

        for kw in ENTERTAINMENT_KEYWORDS:
            if kw in text:
                return "ENTERTAINMENT"

        return "GENERAL"

    def tick(self):
        """Single sampling tick (e.g. called every 5 seconds)"""
        title, proc_name, pid = self.get_active_window_info()
        if not title and not proc_name:
            return None

        cat = self.classify_window(title, proc_name)
        # Update SQLite usage
        self.db.increment_usage(cat, self.poll_interval)

        # Check today limits
        today_usage = self.db.get_today_usage()
        today_sched = self.db.get_today_schedule()

        ent_limit_sec = today_sched["entertainment_limit_mins"] * 60
        gen_limit_sec = today_sched["general_limit_mins"] * 60

        state = {
            "title": title,
            "process": proc_name,
            "category": cat,
            "entertainment_left_secs": max(0, ent_limit_sec - today_usage["entertainment_seconds"]),
            "general_left_secs": max(0, gen_limit_sec - today_usage["general_seconds"]),
            "school_spent_secs": today_usage["school_seconds"],
            "entertainment_expired": today_usage["entertainment_seconds"] >= ent_limit_sec,
            "general_expired": today_usage["general_seconds"] >= gen_limit_sec
        }
        return state

    def run_loop(self):
        self.running = True
        print("Active Window & Time Tracker loop started.")
        while self.running:
            try:
                state = self.tick()
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                time.sleep(self.poll_interval)

    def stop(self):
        self.running = False

if __name__ == "__main__":
    tracker = ActiveWindowTracker(poll_interval=2)
    print("Testing active window tracking (3 samples)...")
    for _ in range(3):
        st = tracker.tick()
        if st:
            print(f"Active: '{st['title'][:35]}' | Proc: {st['process']} | Cat: {st['category']} | Ent Left: {st['entertainment_left_secs']}s")
        time.sleep(2)
