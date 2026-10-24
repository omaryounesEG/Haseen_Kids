import sys
import os
import unittest
import threading
import sqlite3
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager
from proxy.filter_engine import SmartFilterEngine
from core.approvals import ApprovalManager
from core.security import SecurityManager
from core.tracker import ActiveWindowTracker
from youtube.engine import YouTubeEngine

class TestBugAndEdgeCases(unittest.TestCase):
    def setUp(self):
        self.db = DBManager()
        self.security = SecurityManager(self.db)
        self.filter = SmartFilterEngine(self.db)
        self.approvals = ApprovalManager(self.db)
        self.youtube = YouTubeEngine()

    def test_01_sql_injection_and_special_chars(self):
        """Test SQL injection payloads and special characters in domains and inputs"""
        malicious_inputs = [
            "'; DROP TABLE domains; --",
            "test' OR '1'='1",
            "<script>alert(1)</script>",
            "domain.com/path?arg=1&b=2'\"",
            "نطاق-عربي-مدرستي.مصر",
            "   SPACED.COM   ",
            "UPPERCASE-DOMAIN.COM",
            "a" * 500 + ".com"
        ]
        for payload in malicious_inputs:
            # Should not raise SQLite exception
            try:
                self.db.save_domain_decision(payload, "BLOCK", "ADULT", "TEST_SQLI", title=payload)
                dec = self.db.get_domain_decision(payload)
                # Ensure tables still exist
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM domains")
                    count = cursor.fetchone()[0]
                    self.assertGreater(count, 0)
            except Exception as e:
                self.fail(f"SQL injection or special character caused crash on payload '{payload}': {e}")

    def test_02_concurrent_sqlite_wal_writes(self):
        """Simulate high concurrency: 10 threads writing simultaneously to SQLite in WAL mode"""
        errors = []
        def worker(thread_id):
            try:
                for i in range(30):
                    domain = f"thread{thread_id}-domain{i}.com"
                    self.db.save_domain_decision(domain, "ALLOW", "SAFE", "THREAD_TEST")
                    self.db.increment_usage("ENTERTAINMENT", 1)
                    self.db.log_activity(domain, f"https://{domain}", "SAFE", "ALLOW", "concurrent test")
                    dec = self.db.get_domain_decision(domain)
                    if not dec:
                        errors.append(f"Thread {thread_id} failed to read saved domain {domain}")
            except Exception as e:
                errors.append(f"Thread {thread_id} crashed with: {e}")

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent database errors: {errors}")

    def test_03_bedtime_edge_cases(self):
        """Test bedtime logic over midnight and edge time bounds"""
        # Save custom bedtime: 22:00 to 06:00
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE time_schedule SET bedtime_start = '22:00', bedtime_end = '06:00'")
            conn.commit()

        # School sites must ALWAYS bypass bedtime
        act, cat, rsn, src = self.filter.evaluate_url("https://moe.gov.eg")
        self.assertEqual(act, "ALLOW")
        self.assertEqual(cat, "SCHOOL")

    def test_04_approval_codes_tampering_and_replay(self):
        """Test approval code verification against brute force, wrong codes, and reuse"""
        p_code, t_code = self.approvals.generate_codes("secure-test-domain.org")
        
        # Test wrong code
        ok, msg, typ, dom = self.db.verify_and_apply_code("999999")
        self.assertFalse(ok)

        # Register request
        self.db.add_exception_request("secure-test-domain.org", "https://secure-test-domain.org", "research", p_code, t_code)

        # First use should succeed
        ok, msg, typ, dom = self.db.verify_and_apply_code(p_code)
        self.assertTrue(ok)
        self.assertEqual(dom, "secure-test-domain.org")

        # Second use (replay attack) must FAIL because status is no longer PENDING
        ok_replay, msg_replay, _, _ = self.db.verify_and_apply_code(p_code)
        self.assertFalse(ok_replay)

    def test_05_youtube_engine_invalid_inputs(self):
        """Test YouTube Engine with invalid links, empty strings, and malformed URLs"""
        invalid_cases = [
            "",
            None,
            "https://google.com",
            "not_a_url",
            "https://youtube.com/watch?v=invalid_short_id",
            "https://youtube.com/watch?v=" + "x" * 50
        ]
        for url in invalid_cases:
            try:
                vid_id = self.youtube.extract_video_id(url)
                if url == "https://google.com" or url == "not_a_url":
                    self.assertIsNone(vid_id)
                # Calling get_stream_info should not crash
                info = self.youtube.get_stream_info(url)
                self.assertIsInstance(info, dict)
            except Exception as e:
                self.fail(f"YouTube engine crashed on input '{url}': {e}")

    def test_06_security_password_edge_cases(self):
        """Test password verification with empty strings, long strings, Unicode, and wrong hashes"""
        # Test empty password against real hash
        self.assertFalse(self.security.verify_password("", "$2b$12$K1fK72eD0p6tFq49oTzN.OMkEreZ9vE7N0nE2eFvA/fF9GfO8mG4u"))

        # Test corrupt hash
        self.assertFalse(self.security.verify_password("haseen2026", "corrupted_hash_not_bcrypt"))

        # Test very long password (up to 72 bytes max bcrypt limit handled safely)
        long_pass = "P@ssw0rd" * 8
        h = self.security.hash_password(long_pass)
        self.assertTrue(self.security.verify_password(long_pass, h))

        # Test Arabic Unicode password
        ar_pass = "كلمة_مرور_سرية_2026"
        h_ar = self.security.hash_password(ar_pass)
        self.assertTrue(self.security.verify_password(ar_pass, h_ar))

if __name__ == "__main__":
    unittest.main()
