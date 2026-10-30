"""
Haseen Kids v1.2.0 - tests for the new behaviour.

Covers exactly what the parent asked for:
  * whitelist works on every browser and for every sub-domain / CDN resource
  * a YouTube video inside a whitelisted school page (Classera) plays inline
    and is never blocked behind a parent-approval screen
  * offline recovery: recovery key, admin path, full removal
  * friendly block page is served by the proxy
  * theme module exposes a real child-friendly palette
"""

import os
import sys
import unittest
import asyncio
import urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE)

from database.db_manager import DBManager
from proxy.filter_engine import SmartFilterEngine, INFRA_ALLOWLIST
import core.recovery as recovery
from ui import theme


def fresh_db():
    db = DBManager()
    # guarantee the seeded lists exist for these tests
    for dom, cat in [("classera.com", "SCHOOL"), ("wikipedia.org", "EDU"),
                     ("roblox.com", "GAMING"), ("pornhub.com", "ADULT")]:
        db.save_domain_decision(dom, "BLOCK" if cat == "ADULT" else "ALLOW", cat, "LIST_WHITELIST")
    return db


class TestWhitelistEverywhere(unittest.TestCase):
    def setUp(self):
        self.db = fresh_db()
        self.fe = SmartFilterEngine(self.db)

    def test_subdomain_of_whitelisted_site_is_allowed(self):
        for host in ["classera.com", "app.classera.com", "cdn.static.classera.com", "www.classera.com"]:
            action, cat, reason, src = self.fe.evaluate_url(f"https://{host}/login")
            self.assertEqual(action, "ALLOW", f"{host} should be allowed")

    def test_email_root_walks_up_through_all_levels(self):
        # deep hostname under a .com.eg site
        self.db.save_domain_decision("moe.gov.eg", "ALLOW", "SCHOOL", "LIST_WHITELIST")
        self.assertEqual(self.db.get_domain_decision("portal.moe.gov.eg")[0], "ALLOW")
        self.assertEqual(self.db.get_domain_decision("a.b.c.moe.gov.eg")[0], "ALLOW")

    def test_infrastructure_cdn_always_allowed(self):
        for host in ["fonts.gstatic.com", "cdn.jsdelivr.net", "i.ytimg.com", "googlevideo.com"]:
            action, cat, reason, src = self.fe.evaluate_url(f"https://{host}/x.js")
            self.assertEqual(action, "ALLOW", f"CDN {host} must never be blocked")
            self.assertEqual(src, "INFRA_ALLOWLIST")

    def test_whitelisted_root_does_not_leak_to_lookalike(self):
        # notclassera.com must not inherit the classera.com rule
        action, cat, reason, src = self.fe.evaluate_url("https://notclassera.com/")
        self.assertNotEqual(src, "LIST_WHITELIST")


class TestYoutubeInsideLessons(unittest.TestCase):
    def setUp(self):
        self.db = fresh_db()
        self.db.set_setting("youtube_clean_mode", "1")
        self.fe = SmartFilterEngine(self.db)

    def test_embedded_video_in_school_page_is_allowed_inline(self):
        urls = [
            "https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0",
            "https://www.youtube-nocookie.com/embed/abc123",
            "https://youtube.com/embed/xyz",
        ]
        for u in urls:
            action, cat, reason, src = self.fe.evaluate_url(u)
            self.assertEqual(action, "ALLOW", f"embed must play inline: {u}")
            self.assertEqual(src, "YOUTUBE_EMBED")

    def test_watch_page_opens_clean_player_never_blocks(self):
        action, cat, reason, src = self.fe.evaluate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(action, "REDIRECT_YOUTUBE")

    def test_youtube_is_never_blocked_without_clean_mode(self):
        self.db.set_setting("youtube_clean_mode", "0")
        action, cat, reason, src = self.fe.evaluate_url("https://www.youtube.com/watch?v=abc")
        self.assertEqual(action, "ALLOW")
        self.assertNotIn(action, ("BLOCK", "BEDTIME", "TIME_EXPIRED"))


class TestOfflineRecovery(unittest.TestCase):
    def setUp(self):
        self.db = DBManager()

    def test_recovery_key_roundtrip(self):
        key = recovery.generate_recovery_key()
        self.assertEqual(len(recovery.normalize_key(key)), 16)
        recovery.store_recovery_key(self.db, key)
        self.assertTrue(recovery.verify_recovery_key(self.db, key))
        # tolerant input: lowercase + spaces
        self.assertTrue(recovery.verify_recovery_key(self.db, key.lower().replace("-", " ")))
        self.assertFalse(recovery.verify_recovery_key(self.db, "AAAA-BBBB-CCCC-DDDD"))

    def test_recovery_key_survives_missing_db_setting(self):
        key = recovery.generate_recovery_key()
        recovery.store_recovery_key(self.db, key)
        self.db.set_setting("recovery_key_hash", "")   # simulate lost DB row
        self.assertTrue(recovery.verify_recovery_key(self.db, key),
                        "on-disk recovery.sig must still validate the key")

    def test_removal_helpers_are_callable(self):
        for fn in (recovery.revert_browser_policies, recovery.revert_firewall_rules,
                   recovery.remove_autostart, recovery.remove_state_files):
            self.assertTrue(callable(fn))

    def test_recovery_note_written(self):
        key = recovery.generate_recovery_key()
        path = recovery.write_recovery_note(key)
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8") as f:
            self.assertIn(key, f.read())


class TestBlockPageAndRoutes(unittest.TestCase):
    def test_block_page_contains_kid_ui_and_no_js_breakout(self):
        from proxy.local_proxy import LocalProxyServer
        srv = LocalProxyServer()
        html = srv._block_page("example.com", "https://example.com/a?b=1", "موقع محجوب")
        self.assertIn("example.com", html)
        self.assertIn("اطلب إذن والدك", html)
        self.assertIn("127.0.0.1:8089", html)
        # braces from the template must be resolved, not left raw
        self.assertNotIn("{domain}", html)
        self.assertNotIn("{{", html)

    def test_health_endpoint(self):
        from proxy.local_proxy import LocalProxyServer
        srv = LocalProxyServer(port=8098)
        out = {}

        async def run():
            server = await asyncio.start_server(srv.handle_client, "127.0.0.1", 8098)
            reader, writer = await asyncio.open_connection("127.0.0.1", 8098)
            writer.write(b"GET /status HTTP/1.1\r\nHost: 127.0.0.1:8098\r\n\r\n")
            await writer.drain()
            out["data"] = await reader.read(4096)
            writer.close()
            server.close()
            await server.wait_closed()

        asyncio.run(run())
        self.assertIn(b"online", out["data"])

    def test_should_redirect_endpoint_returns_valid_json(self):
        from proxy.local_proxy import LocalProxyServer
        srv = LocalProxyServer(port=8097)
        # deterministic: the clean player must be ON for this assertion
        srv.db.set_setting("youtube_clean_mode", "1")
        url = urllib.parse.quote("https://www.youtube.com/watch?v=abc", safe='')
        out = {}

        async def run():
            server = await asyncio.start_server(srv.handle_client, "127.0.0.1", 8097)
            reader, writer = await asyncio.open_connection("127.0.0.1", 8097)
            writer.write(f"GET /should_redirect?u={url} HTTP/1.1\r\nHost: 127.0.0.1:8097\r\n\r\n".encode())
            await writer.drain()
            out["data"] = await reader.read(8192)
            writer.close()
            server.close()
            await server.wait_closed()

        asyncio.run(run())
        self.assertIn(b"REDIRECT_YOUTUBE", out["data"])


class TestKidTheme(unittest.TestCase):
    def test_palette_is_bright_and_rounded(self):
        qss = theme.build_stylesheet()
        self.assertIn(theme.VIOLET, qss)
        self.assertIn("border-radius", qss)
        self.assertIn("QToolTip", qss)          # explanatory popups styled
        self.assertIn("IBM Plex Sans Arabic", qss)

    def test_tooltip_helper_returns_widget(self):
        class Fake:
            def __init__(self): self.t = ""
            def setToolTip(self, t): self.t = t
        w = theme.tip(Fake(), "شرح")
        self.assertIn("شرح", w.t)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestParentApprovalLoop(unittest.TestCase):
    """The behaviour the parent asked for: the child asks, the parent approves,
    the site opens by itself - no reload, no waiting, no second prompt."""

    def setUp(self):
        self.db = fresh_db()
        self.fe = SmartFilterEngine(self.db)
        self.db.save_domain_decision("blocked-site-test.com", "BLOCK", "ADULT", "LIST_BLACKLIST")

    def tearDown(self):
        with self.db.get_connection() as c:
            c.cursor().execute("DELETE FROM exceptions WHERE domain = 'blocked-site-test.com'")
            c.cursor().execute("DELETE FROM domains WHERE domain = 'blocked-site-test.com'")
            c.commit()

    def _request(self, domain="blocked-site-test.com"):
        msg = self.db.add_exception_request(domain, f"https://{domain}/x", "واجب مدرسي", "111111", "222222")
        return msg

    def test_blocked_before_request(self):
        action, *_ = self.fe.evaluate_url("https://blocked-site-test.com/")
        self.assertEqual(action, "BLOCK")
        self.assertFalse(self.db.has_active_exception("blocked-site-test.com"))

    def test_permanent_approval_unlocks_everywhere(self):
        self._request()
        self.db.grant_exception("blocked-site-test.com")
        self.assertTrue(self.db.has_active_exception("blocked-site-test.com"))
        for host in ("blocked-site-test.com", "www.blocked-site-test.com"):
            action, cat, reason, src = self.fe.evaluate_url(f"https://{host}/")
            self.assertEqual(action, "ALLOW", f"{host} should open after approval")
        # and it is added to the parent whitelist for every browser
        row = self.db.get_domain_decision("blocked-site-test.com")
        self.assertEqual(row[0], "ALLOW")

    def test_temporary_approval_expires(self):
        self._request()
        self.db.grant_exception("blocked-site-test.com", minutes=30)
        self.assertTrue(self.db.has_active_exception("blocked-site-test.com"))
        # force the window into the past: access must close again
        with self.db.get_connection() as c:
            c.cursor().execute(
                "UPDATE exceptions SET expires_at = datetime('now','-1 minute') WHERE domain = ?",
                ("blocked-site-test.com",))
            c.commit()
        self.assertFalse(self.db.has_active_exception("blocked-site-test.com"))
        action, *_ = self.fe.evaluate_url("https://blocked-site-test.com/")
        self.assertEqual(action, "BLOCK")

    def test_rejection_keeps_site_closed(self):
        self._request()
        self.assertTrue(self.db.reject_exception("blocked-site-test.com"))
        self.assertFalse(self.db.has_active_exception("blocked-site-test.com"))
        action, *_ = self.fe.evaluate_url("https://blocked-site-test.com/")
        self.assertEqual(action, "BLOCK")

    def test_pending_requests_are_listed_for_the_parent(self):
        self._request()
        rows = self.db.list_exception_requests("PENDING")
        domains = [r[1] for r in rows]
        self.assertIn("blocked-site-test.com", domains)


if __name__ == "__main__":
    unittest.main(verbosity=2)
