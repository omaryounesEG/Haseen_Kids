"""Small UI helpers that keep the GUI thread free.

The rule these helpers exist for: **never call anything that talks to the
operating system or the network from the GUI thread**.  ShellExecute (used by
``QDesktopServices.openUrl``) or a blocking ``socket.connect_ex`` can take
seconds when the default browser is busy or a port is filtered, and while it
runs the whole window is frozen -- which looks exactly like "the program hung
and stopped".
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading


def open_external(url: str) -> threading.Thread:
    """Open *url* in the default browser WITHOUT blocking the GUI thread.

    ``os.startfile`` / ``QDesktopServices.openUrl`` both hand the request to
    ShellExecute and wait for it.  Doing that on a worker thread keeps the
    interface responsive even when the browser takes seconds to come up.
    Returns the thread (daemon), so callers can ignore it.
    """
    if not isinstance(url, str) or not url.strip():
        return threading.Thread(target=lambda: None, daemon=True)

    url = url.strip()

    def _open():
        try:
            if sys.platform == "win32":
                # ``start`` is a shell builtin: it returns immediately.
                subprocess.Popen(
                    ["cmd", "/c", "start", "", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            elif sys.platform == "darwin":
                subprocess.Popen(["open", url], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        except Exception:
            # Last resort: the Qt helper, still off the GUI thread.
            try:
                from PyQt6.QtCore import QUrl
                from PyQt6.QtGui import QDesktopServices
                QDesktopServices.openUrl(QUrl(url))
            except Exception:
                pass

    t = threading.Thread(target=_open, daemon=True, name="open-external")
    t.start()
    return t


def port_is_open(host: str, port: int, timeout: float = 0.3) -> bool:
    """Non-blocking-ish port probe with a short timeout.

    ``socket.connect_ex`` without a timeout can block for the OS retry window
    (two seconds on Windows when a local port is filtered), which froze the
    startup for ~2s.
    """
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0
    except Exception:
        return False
    finally:
        try:
            sock.close()
        except Exception:
            pass


def reveal_in_explorer(path: str) -> None:
    """Open a folder (or select a file) in Explorer without blocking."""
    if not path:
        return

    def _go():
        try:
            if os.path.isdir(path):
                os.startfile(path)  # noqa: S606 - intentional, local path
            elif os.path.exists(path):
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            else:
                parent = os.path.dirname(os.path.abspath(path))
                if os.path.isdir(parent):
                    os.startfile(parent)
        except Exception:
            pass

    threading.Thread(target=_go, daemon=True, name="reveal").start()
