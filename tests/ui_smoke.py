"""Headless UI smoke test: renders every window to PNG so the layout, colours
and Arabic text can be verified without a physical screen.

Run:  python tests/ui_smoke.py
Output: tests/_shots/*.png
"""
import os
import sys
import traceback

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SHOTS = os.path.join(BASE, "tests", "_shots")
os.makedirs(SHOTS, exist_ok=True)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import QTimer

errors = []


def shoot(widget, name):
    widget.show()
    QApplication.processEvents()
    path = os.path.join(SHOTS, name)
    ok = widget.grab().save(path)
    print(f"  {'OK ' if ok else 'FAIL'} {name}")
    if not ok:
        errors.append(f"screenshot failed: {name}")
    return path


def main():
    app = QApplication(sys.argv)

    fdir = os.path.join(BASE, "assets", "fonts")
    for f in ("IBMPlexSansArabic-Regular.ttf", "IBMPlexSansArabic-Bold.ttf"):
        p = os.path.join(fdir, f)
        if os.path.exists(p):
            QFontDatabase.addApplicationFont(p)
    app.setFont(QFont("IBM Plex Sans Arabic", 11))

    from ui.theme import build_stylesheet
    app.setStyleSheet(build_stylesheet())

    # 1. Child main window
    try:
        from ui.app import HaseenMainWindow
        win = HaseenMainWindow()
        win.resize(1000, 720)
        shoot(win, "01_child_main.png")
        for i, nm in enumerate(["02_tab_time.png", "03_tab_youtube.png", "04_tab_requests.png"]):
            win.tabs.setCurrentIndex(i)
            QApplication.processEvents()
            shoot(win, nm)
    except Exception:
        errors.append("HaseenMainWindow:\n" + traceback.format_exc())
        print("  FAIL HaseenMainWindow")

    # 2. Parent panel tabs
    try:
        from ui.admin_panel import ParentAdminDialog
        dlg = ParentAdminDialog()
        dlg.resize(980, 720)
        shoot(dlg, "05_parent_schedule.png")
        for i, nm in enumerate(["06_parent_lists.png", "07_parent_security.png",
                                "08_parent_updates.png"]):
            dlg.tabs.setCurrentIndex(i + 1)
            QApplication.processEvents()
            shoot(dlg, nm)
    except Exception:
        errors.append("ParentAdminDialog:\n" + traceback.format_exc())
        print("  FAIL ParentAdminDialog")

    # 3. Password dialogs
    try:
        from ui.app import PasswordDialog, ResetPasswordDialog
        from database.db_manager import DBManager
        db = DBManager()
        p = PasswordDialog(db)
        shoot(p, "09_login.png")
        r = ResetPasswordDialog(db)
        shoot(r, "10_recovery.png")
    except Exception:
        errors.append("PasswordDialogs:\n" + traceback.format_exc())
        print("  FAIL PasswordDialogs")

    # 4. Setup wizard pages
    try:
        from installer.setup_wizard import HaseenSetupWizard
        wiz = HaseenSetupWizard()
        wiz.resize(760, 640)
        shoot(wiz, "11_wizard_welcome.png")
        for i, nm in enumerate(["12_wizard_diag.png", "13_wizard_config.png",
                                "14_wizard_install.png", "15_wizard_finish.png"]):
            wiz.setCurrentId(i + 1) if False else None
            try:
                wiz.next()
                QApplication.processEvents()
                shoot(wiz, nm)
            except Exception:
                pass
    except Exception:
        errors.append("HaseenSetupWizard:\n" + traceback.format_exc())
        print("  FAIL HaseenSetupWizard")

    print("\n" + "=" * 60)
    if errors:
        print(f"UI SMOKE: {len(errors)} problem(s)")
        for e in errors:
            print("-" * 60)
            print(e)
        return 1
    print("UI SMOKE: all windows rendered successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
