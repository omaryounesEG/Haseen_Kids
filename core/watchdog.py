import time
import os
import sys
import subprocess

HEARTBEAT_FILE = "H:\\Haseen_Kids\\core\\daemon.heartbeat"
SERVICE_SCRIPT = "H:\\Haseen_Kids\\core\\service.py"

def run_watchdog():
    print("🛡️ [حصين] Mutual Watchdog Process started.")
    py_exe = sys.executable

    while True:
        try:
            now = time.time()
            stale = True

            if os.path.exists(HEARTBEAT_FILE):
                try:
                    with open(HEARTBEAT_FILE, "r") as f:
                        ts = float(f.read().strip())
                    if now - ts < 10.0:
                        stale = False
                except Exception:
                    stale = True

            if stale:
                print("⚠️ [Watchdog Alert] Haseen Service heartbeat lost or not running! Respawning...")
                subprocess.Popen([py_exe, SERVICE_SCRIPT], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                time.sleep(4)

            time.sleep(2)
        except KeyboardInterrupt:
            break
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    run_watchdog()
