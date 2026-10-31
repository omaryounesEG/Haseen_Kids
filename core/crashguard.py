"""
Haseen Kids - crash guard.

PyQt aborts the whole process when a Python exception escapes an event handler
or a slot. To a parent that looks like "I clicked a button and the program
closed and never opened again". This module makes the application survive any
error: the exception is written to logs/haseen_error.log, the user gets a clear
Arabic message, and the program keeps running.

Usage (must happen before any widget is created):

    from core.crashguard import SafeApplication, install_exception_hooks
    install_exception_hooks()
    app = SafeApplication(sys.argv)
"""
import datetime
import os
import sys
import threading
import traceback

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "haseen_error.log")

_dialog_open = False
_open_boxes = []


def _ensure_log_dir():
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception:
        pass


def log_exception(exc_type=None, exc_value=None, exc_tb=None, context=""):
    """Appends the traceback to logs/haseen_error.log and returns the text."""
    _ensure_log_dir()
    if exc_type is None:
        exc_type, exc_value, exc_tb = sys.exc_info()
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n===== {stamp} {('- ' + context) if context else ''} =====\n{tb}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(entry)
    except Exception:
        pass
    try:
        sys.stderr.write(entry)
    except Exception:
        pass
    return tb


def read_last_error(max_chars=4000):
    try:
        if not os.path.exists(LOG_FILE):
            return ""
        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as fh:
            data = fh.read()
        return data[-max_chars:]
    except Exception:
        return ""


def clear_error_log():
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
    except Exception:
        pass


def friendly_message(tb=""):
    """Turns a traceback into something a parent can act on."""
    low = (tb or "").lower()
    if "readonly database" in low or "attempt to write a readonly" in low:
        return ("قاعدة البيانات محمية من الكتابة.\n"
                "الحل: شغّل البرنامج كمسؤول (Run as administrator) أو انقل مجلد البرنامج "
                "إلى مكان عادي مثل C:\\Haseen_Kids بدل C:\\Windows أو Program Files.")
    if "database is locked" in low:
        return ("قاعدة البيانات مشغولة بعملية أخرى.\n"
                "الحل: أغلق أي نسخة أخرى من البرنامج ثم أعد المحاولة.")
    if "no such table" in low:
        return ("ملف قاعدة البيانات تالف أو قديم.\n"
                "الحل: شغّل Repair.bat لإصلاح التثبيت مع الحفاظ على نسخة احتياطية.")
    if "no module named" in low:
        return ("مكوّن مطلوب غير مثبّت في البيئة المحلية.\n"
                "الحل: شغّل Repair.bat لإعادة بناء البيئة تلقائياً.")
    if "smtplib" in low or "smtp" in low or "getaddrinfo" in low or "timed out" in low:
        return ("تعذّر الاتصال بسيرفر البريد (الشبكة أو كلمة مرور التطبيق).\n"
                "تحقق من الإنترنت ومن كلمة مرور التطبيق ثم أعد المحاولة.")
    return "حدث خطأ غير متوقع، لكن البرنامج ما زال يعمل. التفاصيل محفوظة في مجلد logs."


def _show_error_dialog(summary, tb):
    """One dialog at a time, never blocking the event loop permanently."""
    global _dialog_open
    if _dialog_open:
        return
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        if QApplication.instance() is None:
            return
        _dialog_open = True
        box = QMessageBox()
        box.setWindowTitle("حَصِين للأطفال — تنبيه")
        box.setIcon(QMessageBox.Icon.Warning)
        box.setText(summary)
        box.setInformativeText("التفاصيل محفوظة في logs\\haseen_error.log")
        box.setDetailedText(tb[-2500:])
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        # Non-modal on purpose: a modal exec() here would block the very event
        # loop we are trying to protect (and hangs automated runs).
        from PyQt6.QtCore import Qt
        box.setWindowModality(Qt.WindowModality.NonModal)
        box.finished.connect(lambda _=0: _release_box())
        box.show()
        _open_boxes.append(box)
    except Exception:
        _dialog_open = False


def _release_box():
    global _dialog_open
    _dialog_open = False
    while _open_boxes:
        try:
            _open_boxes.pop()
        except Exception:
            break


def install_exception_hooks(verbose_dialogs=True):
    """Catches every uncaught exception instead of letting Qt abort the app."""
    def hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        tb = log_exception(exc_type, exc_value, exc_tb)
        if verbose_dialogs:
            _show_error_dialog(friendly_message(tb), tb)

    sys.excepthook = hook

    def thread_hook(args):
        log_exception(args.exc_type, args.exc_value, args.exc_traceback,
                      context=f"thread:{getattr(args.thread, 'name', '?')}")

    try:
        threading.excepthook = thread_hook
    except Exception:
        pass


def make_safe_application():
    """Returns a QApplication subclass whose notify() never lets an error kill it."""
    from PyQt6.QtCore import QEvent
    from PyQt6.QtWidgets import QApplication

    class SafeApplication(QApplication):
        def notify(self, receiver, event):
            try:
                return super().notify(receiver, event)
            except Exception:
                tb = log_exception(context=f"event:{event.type().name}")
                _show_error_dialog(friendly_message(tb), tb)
                return False

    return SafeApplication


def safe(slot, context="slot"):
    """Decorator for slots: on error, log + inform the user, keep the app alive."""
    def wrapper(*args, **kwargs):
        try:
            return slot(*args, **kwargs)
        except Exception:
            tb = log_exception(context=context)
            _show_error_dialog(friendly_message(tb), tb)
            return None
    return wrapper
