import sqlite3
import os
import json
from datetime import datetime, date

DB_PATH = "H:\\Haseen_Kids\\database\\haseen.db"

class DBManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Settings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Domains filtering cache & rules
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS domains (
                    domain TEXT PRIMARY KEY,
                    category TEXT, -- SAFE, EDU, GAMING, ADULT, VIOLENCE, SCHOOL
                    action TEXT,   -- ALLOW, BLOCK
                    source TEXT,   -- LIST_WHITELIST, LIST_BLACKLIST, AI_CACHE, PARENT_RULE
                    title TEXT,
                    last_evaluated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_domains_action ON domains(action);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_domains_category ON domains(category);')

            # Weekly time schedule limits (minutes per category per weekday)
            # day_of_week: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS time_schedule (
                    day_of_week INTEGER PRIMARY KEY,
                    day_name TEXT,
                    entertainment_limit_mins INTEGER DEFAULT 60,
                    general_limit_mins INTEGER DEFAULT 120,
                    bedtime_start TEXT DEFAULT '21:00',
                    bedtime_end TEXT DEFAULT '07:00'
                )
            ''')

            # Daily usage tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_usage (
                    usage_date DATE PRIMARY KEY,
                    entertainment_used_seconds INTEGER DEFAULT 0,
                    general_used_seconds INTEGER DEFAULT 0,
                    school_used_seconds INTEGER DEFAULT 0,
                    last_active_timestamp TIMESTAMP
                )
            ''')

            # Exception requests & approvals
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exceptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT,
                    url TEXT,
                    child_reason TEXT,
                    perm_code TEXT,
                    temp_code TEXT,
                    status TEXT DEFAULT 'PENDING', -- PENDING, APPROVED_PERM, APPROVED_TEMP, REJECTED
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Activity and audit logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    domain TEXT,
                    url TEXT,
                    category TEXT,
                    action TEXT, -- ALLOW, BLOCK, REDIRECT_YOUTUBE
                    reason TEXT,
                    duration_seconds INTEGER DEFAULT 0
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_time ON activity_log(timestamp);')

            # Populate default schedule if empty
            cursor.execute('SELECT COUNT(*) FROM time_schedule')
            if cursor.fetchone()[0] == 0:
                day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                for i, name in enumerate(day_names):
                    ent = 120 if i in [4, 5] else 60
                    gen = 180 if i in [4, 5] else 120
                    cursor.execute('''
                        INSERT INTO time_schedule (day_of_week, day_name, entertainment_limit_mins, general_limit_mins)
                        VALUES (?, ?, ?, ?)
                    ''', (i, name, ent, gen))

            # Default settings
            defaults = {
                "admin_password_hash": "$2b$12$K1fK72eD0p6tFq49oTzN.OMkEreZ9vE7N0nE2eFvA/fF9GfO8mG4u", # "haseen2026"
                "parent_email": "parent@example.com",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": "587",
                "smtp_user": "",
                "smtp_app_password": "",
                "imap_server": "imap.gmail.com",
                "ai_provider": "gemini",
                "gemini_api_key": "",
                "deepseek_api_key": "",
                "proxy_port": "8089",
                "youtube_clean_mode": "1",
                "process_lockdown": "0",
                "language": "ar"
            }

            for k, v in defaults.items():
                cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (k, v))

            conn.commit()

    def set_setting(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)', (key, str(value)))
            conn.commit()

    def get_setting(self, key, default=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def get_all_settings(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM settings')
            return dict(cursor.fetchall())

    def get_domain_decision(self, domain):
        """Returns (action, category, source) or None if domain not evaluated yet"""
        if not domain:
            return None
        domain = domain.lower().strip()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Exact match
            cursor.execute('SELECT action, category, source FROM domains WHERE domain = ?', (domain,))
            row = cursor.fetchone()
            if row:
                return row

            # Subdomain wildcard check
            parts = domain.split('.')
            if len(parts) > 2:
                parent_domain = '.'.join(parts[1:])
                cursor.execute('SELECT action, category, source FROM domains WHERE domain = ?', (parent_domain,))
                row = cursor.fetchone()
                if row:
                    return row

        return None

    def save_domain_decision(self, domain, action, category, source, title=None):
        domain = domain.lower().strip()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO domains (domain, category, action, source, title, last_evaluated)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (domain, category, action, source, title))
            conn.commit()

    def get_today_usage(self):
        today = date.today().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT entertainment_used_seconds, general_used_seconds, school_used_seconds FROM daily_usage WHERE usage_date = ?', (today,))
            row = cursor.fetchone()
            if row:
                return {
                    "date": today,
                    "entertainment_seconds": row[0],
                    "general_seconds": row[1],
                    "school_seconds": row[2]
                }
            else:
                cursor.execute('INSERT OR IGNORE INTO daily_usage (usage_date, entertainment_used_seconds, general_used_seconds, school_used_seconds) VALUES (?, 0, 0, 0)', (today,))
                conn.commit()
                return {
                    "date": today,
                    "entertainment_seconds": 0,
                    "general_seconds": 0,
                    "school_seconds": 0
                }

    def increment_usage(self, category, seconds):
        today = date.today().isoformat()
        col = "general_used_seconds"
        if category in ["ENTERTAINMENT", "GAMING", "YOUTUBE"]:
            col = "entertainment_used_seconds"
        elif category in ["SCHOOL", "EDU"]:
            col = "school_used_seconds"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                INSERT INTO daily_usage (usage_date, {col}, last_active_timestamp)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(usage_date) DO UPDATE SET
                    {col} = {col} + ?,
                    last_active_timestamp = CURRENT_TIMESTAMP
            ''', (today, seconds, seconds))
            conn.commit()

    def get_today_schedule(self):
        weekday = datetime.now().weekday()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT entertainment_limit_mins, general_limit_mins, bedtime_start, bedtime_end, day_name
                FROM time_schedule WHERE day_of_week = ?
            ''', (weekday,))
            row = cursor.fetchone()
            if row:
                return {
                    "weekday": weekday,
                    "day_name": row[4],
                    "entertainment_limit_mins": row[0],
                    "general_limit_mins": row[1],
                    "bedtime_start": row[2],
                    "bedtime_end": row[3]
                }
            return {
                "weekday": weekday,
                "day_name": "Today",
                "entertainment_limit_mins": 60,
                "general_limit_mins": 120,
                "bedtime_start": "21:00",
                "bedtime_end": "07:00"
            }

    def log_activity(self, domain, url, category, action, reason="", duration_seconds=0):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO activity_log (domain, url, category, action, reason, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (domain, url, category, action, reason, duration_seconds))
            conn.commit()

    def add_exception_request(self, domain, url, reason, perm_code, temp_code):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO exceptions (domain, url, child_reason, perm_code, temp_code, status)
                VALUES (?, ?, ?, ?, ?, 'PENDING')
            ''', (domain, url, reason, perm_code, temp_code))
            exc_id = cursor.lastrowid
            conn.commit()
            return exc_id

    def verify_and_apply_code(self, code):
        """Checks if code matches a pending permanent or temporary exception"""
        code = str(code).strip()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Permanent unlock
            cursor.execute("SELECT id, domain FROM exceptions WHERE perm_code = ? AND status = 'PENDING'", (code,))
            row = cursor.fetchone()
            if row:
                exc_id, domain = row
                cursor.execute("UPDATE exceptions SET status = 'APPROVED_PERM' WHERE id = ?", (exc_id,))
                cursor.execute("INSERT OR REPLACE INTO domains (domain, category, action, source) VALUES (?, 'SAFE', 'ALLOW', 'PARENT_RULE')", (domain,))
                conn.commit()
                return True, f"تم فتح الموقع {domain} بشكل دائم بنجاح", "PERM", domain

            # Temporary 30m extension
            cursor.execute("SELECT id, domain FROM exceptions WHERE temp_code = ? AND status = 'PENDING'", (code,))
            row = cursor.fetchone()
            if row:
                exc_id, domain = row
                cursor.execute("UPDATE exceptions SET status = 'APPROVED_TEMP' WHERE id = ?", (exc_id,))
                conn.commit()
                return True, f"تم تمديد وقت التصفح 30 دقيقة للموقع {domain}", "TEMP", domain

        return False, "رمز الموافقة غير صحيح أو تم استخدامه مسبقاً", None, None

if __name__ == "__main__":
    db = DBManager()
    print("Database manager ready with WAL mode and schema.")
    print("Today schedule:", db.get_today_schedule())
    print("Today usage:", db.get_today_usage())
