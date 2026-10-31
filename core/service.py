import threading
import asyncio
import time
import os
import sys
import atexit
import psutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager
from proxy.local_proxy import LocalProxyServer
from core.tracker import ActiveWindowTracker
from core.security import SecurityManager

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
HEARTBEAT_FILE = os.path.join(CORE_DIR, "daemon.heartbeat")
PID_FILE = os.path.join(CORE_DIR, "service.pid")

def check_single_instance():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            if psutil.pid_exists(old_pid):
                proc = psutil.Process(old_pid)
                if "python" in proc.name().lower():
                    print(f"[Haseen Service] Already running on PID {old_pid}. Exiting duplicate instance.")
                    sys.exit(0)
        except Exception:
            pass

    # Register current PID
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

def cleanup_pid():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                if int(f.read().strip()) == os.getpid():
                    os.remove(PID_FILE)
        except Exception:
            pass

atexit.register(cleanup_pid)

class HaseenCoreDaemon:
    def __init__(self):
        self.db = DBManager()
        self.proxy = LocalProxyServer(port=int(self.db.get_setting("proxy_port", "8089")))
        self.tracker = ActiveWindowTracker(self.db, poll_interval=3)
        self.security = SecurityManager(self.db)
        self.running = False

    def start_proxy_thread(self):
        def run_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.proxy.start())
            except Exception as e:
                print(f"[Proxy Warning] Local proxy error: {e}")

        t = threading.Thread(target=run_async, daemon=True)
        t.start()
        print("Proxy server thread started.")

    def run(self):
        self.running = True
        print(f"🛡️ [Haseen Kids] Core Service Daemon started on PID {os.getpid()}...")

        # Write initial heartbeat immediately
        with open(HEARTBEAT_FILE, "w") as f:
            f.write(str(time.time()))

        # 1. Start Local Proxy in background thread
        self.start_proxy_thread()

        # 2. Main monitoring and heartbeat loop
        while self.running:
            try:
                # Update heartbeat for watchdog
                with open(HEARTBEAT_FILE, "w") as f:
                    f.write(str(time.time()))

                # Sample active window & increment usage
                st = self.tracker.tick()

                # Enforce unapproved browser restriction
                self.security.check_and_kill_unapproved_browsers()

                time.sleep(3)
            except KeyboardInterrupt:
                print("Daemon stopped by user.")
                break
            except Exception as e:
                time.sleep(3)

if __name__ == "__main__":
    check_single_instance()
    daemon = HaseenCoreDaemon()
    daemon.run()
