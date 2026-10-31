"""One copy only.

A second copy of the program looks harmless but it is not: two processes start
two proxies on port 8089, two trackers write to the same SQLite file, and the
parent sees *several* icons next to the clock while the first window stops
answering (database locks + CPU contention).  This module guarantees a single
instance and brings the running window to the front instead.
"""

from __future__ import annotations

import ctypes
import os
import sys
import threading

_MUTEX_NAME = "Local\\HaseenKids_SingleInstance_v1"
_handle = None
_lock = threading.Lock()


def _is_windows() -> bool:
    return sys.platform == "win32"


def acquire_mutex(name: str = _MUTEX_NAME) -> bool:
    """True when this process is the first one (and owns the mutex)."""
    global _handle
    if not _is_windows():
        # POSIX fallback: an exclusive file lock in the temp folder.
        import fcntl
        import tempfile
        path = os.path.join(tempfile.gettempdir(), "haseen_kids.lock")
        f = open(path, "a+")
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            _handle = f
            return True
        except OSError:
            f.close()
            return False

    with _lock:
        if _handle:
            return True
        ERROR_ALREADY_EXISTS = 183
        # use_last_error=True is required: ctypes otherwise reports a stale
        # GetLastError() and the guard silently lets a second copy through.
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.CreateMutexW(None, False, name)
        last_error = ctypes.get_last_error()
        if not handle:
            return True  # cannot create -> do not block the program
        if last_error == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return False
        _handle = handle
        return True


def release_mutex() -> None:
    global _handle
    with _lock:
        if _handle and _is_windows():
            try:
                ctypes.windll.kernel32.ReleaseMutex(_handle)
                ctypes.windll.kernel32.CloseHandle(_handle)
            except Exception:
                pass
        _handle = None


def find_existing_window() -> int:
    """Return the HWND of a running Haseen window, or 0."""
    if not _is_windows():
        return 0
    found = []

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32 = ctypes.windll.user32

    def _cb(hwnd, _lparam):
        try:
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value or ""
            if ("حصين" in title or "Haseen" in title) and user32.IsWindowVisible(hwnd):
                found.append(hwnd)
                return False  # stop enumerating
        except Exception:
            pass
        return True

    try:
        user32.EnumWindows(WNDENUMPROC(_cb), None)
    except Exception:
        return 0
    return found[0] if found else 0


def focus_existing_window() -> bool:
    """Restore + raise the window of the copy that is already running."""
    hwnd = find_existing_window()
    if not hwnd:
        return False
    try:
        user32 = ctypes.windll.user32
        SW_RESTORE = 9
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def already_running_notice(title="حَصِين للأطفال | Haseen Kids") -> None:
    """Tell the user (in Arabic) that the program is already open."""
    message = (
        "البرنامج مفتوح بالفعل ويعمل الآن.\n\n"
        "تم إظهار النافذة المفتوحة بدلاً من تشغيل نسخة ثانية،\n"
        "لأن تشغيل أكثر من نسخة يسبب تهنيج البرنامج وبطء الجهاز.\n\n"
        "لو لم تظهر النافذة، ابحث عن أيقونة حَصِين بجوار الساعة."
    )
    if os.environ.get("HASEEN_NO_DIALOGS"):
        print("[single-instance] already running")
        return
    try:
        if _is_windows():
            ctypes.windll.user32.MessageBoxW(None, message, title, 0x00000040 | 0x00040000)
            return
    except Exception:
        pass
    try:
        print("[single-instance] already running")
    except Exception:
        pass


def ensure_single_instance(verbose=True) -> bool:
    """Main entry point: True = continue, False = another copy owns the app."""
    if acquire_mutex():
        return True
    focus_existing_window()
    if verbose:
        already_running_notice()
    return False


def check_only() -> bool:
    """True when no other copy holds the app.

    Used by the launcher (``run.py``), which must NOT keep the mutex: it spawns
    the interface as a child process and the child is the real owner.  We try,
    and release immediately.
    """
    if acquire_mutex():
        release_mutex()
        return True
    return False


def find_duplicate_ui_instances(app_dir: str | None = None) -> list:
    """List leftover interface processes of THIS installation (never kills).

    Copies started by an older build have no mutex, so after an upgrade they can
    still be running (several icons next to the clock, several proxies, one
    SQLite file under contention).  We only ever kill ``ui/app.py`` of the same
    install folder and never our own process.
    """
    try:
        import psutil
    except Exception:
        return 0

    base = (app_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    base_norm = os.path.normcase(base)
    me = os.getpid()
    pids = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            pid = proc.info["pid"]
            if pid == me:
                continue
            # Only ever touch Python interpreters.  Matching the command line
            # alone is not enough: a launcher (.bat / bash / cmd wrapper) that
            # carries the same path in its command line would be killed too,
            # and then the program dies with it.
            name = (proc.info.get("name") or "").lower()
            if not name.startswith("python"):
                continue
            cmdline = proc.info.get("cmdline") or []
            joined = " ".join(cmdline)
            if "ui" not in joined or "app.py" not in joined:
                continue
            if base_norm not in os.path.normcase(joined):
                continue
            pids.append(pid)
        except Exception:
            continue
    return pids
