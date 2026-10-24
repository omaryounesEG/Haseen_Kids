import threading
import asyncio
import time
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager
from proxy.local_proxy import LocalProxyServer
from core.tracker import ActiveWindowTracker
from core.security import SecurityManager

HEARTBEAT_FILE = "H:\\Haseen_Kids\\core\\daemon.heartbeat"

class HaseenCoreDaemon:
    def __init__(self):
        self.db = DBManager()
        self.proxy = LocalProxyServer(port=int(self.db.get_setting("proxy_port", "8089")))
        self.tracker = ActiveWindowTracker(self.db, poll_interval=3)
        self.security = SecurityManager(self.db)
        self.running = False

    def start_proxy_thread(self):
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.proxy.start())

        t = threading.Thread(target=run_async, daemon=True)
        t.start()
        print("Proxy server thread started.")

    def run(self):
        self.running = True
        print("🛡️ [حصين | Haseen Kids] Starting Core Service Daemon...")

        # 1. Start Local Proxy in background thread
        self.start_proxy_thread()

        # 2. Main monitoring and heartbeat loop
        while self.running:
            try:
                # Write heartbeat for watchdog
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
    daemon = HaseenCoreDaemon()
    daemon.run()
