import sys
import os
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager
from youtube.engine import YouTubeEngine
from proxy.filter_engine import SmartFilterEngine
from core.approvals import ApprovalManager
from core.tracker import ActiveWindowTracker
from core.reports import WeeklyReportGenerator
from core.updater import SecureGitHubUpdater
from core.security import SecurityManager

class TestHaseenKids(unittest.TestCase):
    def setUp(self):
        self.db = DBManager()

    def test_01_db_manager(self):
        self.db.set_setting("test_key", "test_val")
        self.assertEqual(self.db.get_setting("test_key"), "test_val")

        sched = self.db.get_today_schedule()
        self.assertIn("entertainment_limit_mins", sched)
        self.assertIn("general_limit_mins", sched)

        usage = self.db.get_today_usage()
        self.assertIn("entertainment_seconds", usage)

    def test_02_tier1_seeded_domains(self):
        row = self.db.get_domain_decision("moe.gov.eg")
        self.assertIsNotNone(row)
        action, cat, src = row
        self.assertEqual(action, "ALLOW")
        self.assertEqual(cat, "SCHOOL")

        row_bad = self.db.get_domain_decision("pornhub.com")
        self.assertIsNotNone(row_bad)
        action, cat, src = row_bad
        self.assertEqual(action, "BLOCK")

    def test_03_youtube_engine(self):
        yt = YouTubeEngine()
        vid_id = yt.extract_video_id("https://www.youtube.com/watch?v=aqz-KE-bpKQ")
        self.assertEqual(vid_id, "aqz-KE-bpKQ")

        # Test SponsorBlock API
        segs = yt.get_sponsorblock_segments(vid_id)
        self.assertIsInstance(segs, list)

        # Test stream info extraction
        info = yt.get_stream_info(vid_id)
        self.assertIn("stream_url", info)
        self.assertTrue(bool(info.get("stream_url")))

    def test_04_smart_filter_engine(self):
        fe = SmartFilterEngine(self.db)
        act, cat, rsn, src = fe.evaluate_url("https://moe.gov.eg/info")
        self.assertEqual(act, "ALLOW")
        self.assertEqual(cat, "SCHOOL")

        act, cat, rsn, src = fe.evaluate_url("https://www.youtube.com/watch?v=aqz-KE-bpKQ")
        self.assertEqual(act, "REDIRECT_YOUTUBE")

    def test_05_approvals_and_codes(self):
        am = ApprovalManager(self.db)
        p_code, t_code = am.generate_codes("testsite.com")
        self.assertEqual(len(p_code), 6)
        self.assertEqual(len(t_code), 6)

        # Register exception and test code verification
        exc_id = self.db.add_exception_request("testsite.com", "https://testsite.com", "study", p_code, t_code)
        self.assertIsNotNone(exc_id)

        ok, msg, typ, dom = self.db.verify_and_apply_code(p_code)
        self.assertTrue(ok)
        self.assertEqual(dom, "testsite.com")

        # Decision should now be in domains table
        row = self.db.get_domain_decision("testsite.com")
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "ALLOW")

    def test_06_active_window_tracker(self):
        tracker = ActiveWindowTracker(self.db)
        cat = tracker.classify_window("منصة مدرستي التعليمية - Google Chrome", "chrome.exe")
        self.assertEqual(cat, "SCHOOL")

        cat_ent = tracker.classify_window("Roblox Game Client", "roblox.exe")
        self.assertEqual(cat_ent, "ENTERTAINMENT")

    def test_07_weekly_reports(self):
        rep = WeeklyReportGenerator(self.db)
        stats = rep.gather_week_stats()
        self.assertIn("entertainment_hours", stats)
        self.assertIn("school_hours", stats)

    def test_08_security_passwords(self):
        sec = SecurityManager(self.db)
        h = sec.hash_password("admin_secret_123")
        self.assertTrue(sec.verify_password("admin_secret_123", h))
        self.assertFalse(sec.verify_password("wrong_password", h))

    def test_09_updater(self):
        updater = SecureGitHubUpdater()
        has_up, ver, info, err = updater.check_for_updates()
        self.assertIsInstance(has_up, bool)

if __name__ == "__main__":
    unittest.main()
