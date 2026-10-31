import sys
import os
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen" # Run headless without showing desktop window

from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt6.QtCore import Qt

# Monkey-patch QMessageBox to prevent modal event loops during automated headless testing
QMessageBox.information = lambda parent, title, text, *args, **kwargs: QMessageBox.StandardButton.Ok
QMessageBox.warning = lambda parent, title, text, *args, **kwargs: QMessageBox.StandardButton.Ok
QMessageBox.critical = lambda parent, title, text, *args, **kwargs: QMessageBox.StandardButton.Ok
QMessageBox.question = lambda parent, title, text, *args, **kwargs: QMessageBox.StandardButton.Yes

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.app import HaseenMainWindow, PasswordDialog
from ui.admin_panel import ParentAdminDialog

class TestUIUX(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def setUp(self):
        from database.db_manager import DBManager
        DBManager().set_setting("language", "ar")

    def test_01_main_window_elements_and_rtl(self):
        """Verify main window controls, bilingual direction, and theme"""
        win = HaseenMainWindow()
        self.assertIsNotNone(win)
        self.assertIn("Haseen", win.windowTitle())

        # Check default RTL direction for Arabic
        self.assertEqual(win.layoutDirection(), Qt.LayoutDirection.RightToLeft)

        # Check tabs count and names
        self.assertEqual(win.tabs.count(), 3)
        self.assertIn("رصيد الوقت", win.tabs.tabText(0))
        self.assertIn("يوتيوب", win.tabs.tabText(1))
        self.assertIn("طلب استثناء", win.tabs.tabText(2))

        # Check progress bars
        self.assertIsNotNone(win.bar_ent)
        self.assertIsNotNone(win.bar_gen)

        win.close()

    def test_02_language_toggle_bilingual(self):
        """Test language toggle from Arabic (RTL) to English (LTR)"""
        win = HaseenMainWindow()
        initial_lang = win.current_lang

        win.toggle_language()
        # Should now be opposite
        self.assertNotEqual(win.current_lang, initial_lang)
        if win.current_lang == "en":
            self.assertEqual(win.layoutDirection(), Qt.LayoutDirection.LeftToRight)
        else:
            self.assertEqual(win.layoutDirection(), Qt.LayoutDirection.RightToLeft)

        # Revert
        win.toggle_language()
        win.close()

    def test_03_password_dialog(self):
        """Test parent login dialog authentication logic"""
        dlg = PasswordDialog()
        self.assertEqual(dlg.layoutDirection(), Qt.LayoutDirection.RightToLeft)

        # Test entering password
        dlg.pwd_input.setText("haseen2026")
        self.assertEqual(dlg.get_password(), "haseen2026")

        dlg.close()

    def test_04_parent_admin_console(self):
        """Verify parent administration panel and its 5 tabs"""
        admin = ParentAdminDialog()
        self.assertIsNotNone(admin)
        # 5 tabs: schedule, lists, security/AI, updates/maintenance, child requests
        self.assertEqual(admin.tabs.count(), 5)

        # Tab 0: Schedule
        self.assertIn("الأوقات", admin.tabs.tabText(0))
        self.assertEqual(len(admin.spin_boxes), 7) # All 7 weekdays configured
        self.assertIsNotNone(admin.time_bed_start)
        self.assertIsNotNone(admin.time_bed_end)

        # Tab 1: Domains & Rules
        self.assertIn("القوائم", admin.tabs.tabText(1))
        self.assertGreater(admin.table_domains.rowCount(), 0)

        # Test adding custom domain through UI
        admin.in_domain.setText("uxtest-custom.com")
        admin.cmb_cat.setCurrentText("EDU")
        admin.cmb_act.setCurrentText("ALLOW")
        admin.add_domain_rule()

        # Check rule was added to table
        found = False
        for r in range(admin.table_domains.rowCount()):
            item = admin.table_domains.item(r, 0)
            if item and item.text() == "uxtest-custom.com":
                found = True
                break
        self.assertTrue(found, "Newly added rule should appear in the domains table")

        # Tab 2: AI & Protection
        self.assertIn("الحماية", admin.tabs.tabText(2))
        self.assertIsNotNone(admin.chk_lockdown)
        self.assertIsNotNone(admin.chk_yt_clean)

        # Tab 3: Updates
        self.assertIn("التحديثات", admin.tabs.tabText(3))

        admin.close()

    def test_05_child_requests_and_code_flow(self):
        """Test exception request submission and approval code verification via UI"""
        win = HaseenMainWindow()

        # Fill request
        win.req_domain.setText("scratch-learning.org")
        win.req_reason.setText("مشروع برمجة مدرسي")
        # Click submit
        win.submit_child_request()

        # Verify exception was created in DB
        with win.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT perm_code FROM exceptions WHERE domain = 'scratch-learning.org' AND status = 'PENDING'")
            row = c.fetchone()
            self.assertIsNotNone(row)
            p_code = row[0]

        # Enter approval code in UI
        win.code_input.setText(p_code)
        win.submit_approval_code()

        # Verify domain is now allowed
        dec = win.db.get_domain_decision("scratch-learning.org")
        self.assertIsNotNone(dec)
        self.assertEqual(dec[0], "ALLOW")

        win.close()

if __name__ == "__main__":
    unittest.main()


class TestTrayPauseMenu(unittest.TestCase):
    """Right-click on the tray icon must offer 15/30/60/240 minutes."""

    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from ui.app import HaseenMainWindow
        self.win = HaseenMainWindow()

    def tearDown(self):
        try:
            self.win.db.clear_pause()
        except Exception:
            pass
        self.win.tray_icon.hide()
        self.win.close()

    def test_menu_has_the_four_durations_and_resume(self):
        labels = [a.text() for a in self.win.menu_pause.actions()]
        self.assertEqual(len(labels), 4, labels)
        for word in ("15", "30", "ساعة", "4"):
            self.assertTrue(any(word in l for l in labels), f"missing {word} in {labels}")
        self.assertIn("استئناف", self.win.act_resume.text())
        self.assertFalse(self.win.act_resume.isEnabled())

    def test_tray_reflects_the_pause_state(self):
        self.win.db.set_pause(30)
        self.win.refresh_pause_state()
        self.assertTrue(self.win.act_resume.isEnabled())
        self.assertIn("متوقفة", self.win.act_pause_status.text())
        self.assertIn("متوقفة", self.win.tray_icon.toolTip())
        self.assertFalse(self.win.menu_pause.isEnabled())

        self.win.db.clear_pause()
        self.win.refresh_pause_state()
        self.assertFalse(self.win.act_resume.isEnabled())
        self.assertIn("نشطة", self.win.act_pause_status.text())

    def test_pause_requires_the_parent_password(self):
        import ui.app as app_module
        calls = {}

        class FakeDlg:
            def __init__(self, db=None, parent=None, title=None, prompt=None):
                calls["asked"] = True

            def exec(self):
                from PyQt6.QtWidgets import QDialog
                return QDialog.DialogCode.Rejected

        original = app_module.PasswordDialog
        app_module.PasswordDialog = FakeDlg
        try:
            self.win.pause_protection(15)      # parent cancels the prompt
        finally:
            app_module.PasswordDialog = original
        self.assertTrue(calls.get("asked"), "the parent must be asked for the password")
        self.assertFalse(self.win.db.is_paused(), "no pause without a correct password")
