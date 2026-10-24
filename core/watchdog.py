import time
import os
import sys
import subprocess
import psutil

HEARTBEAT_FILE = "H:\\Haseen_Kids\\core\\daemon.heartbeat"
SERVICE_PID_FILE = "H:\\Haseen_Kids\\core\\service.pid"
WATCHDOG_PID_FILE = "H:\\Haseen_Kids\\core\\watchdog.pid"
SERVICE_SCRIPT = "H:\\Haseen_Kids\\core\\service.py"

def check_single_instance():
    if os.path.exists(WATCHDOG_PID_FILE):
        try:
            with open(WATCHDOG_PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            if psutil.pid_exists(old_pid):
                proc = psutil.Process(old_pid)
                if "python" in proc.name().lower():
                    print(f"[Watchdog] Already running on PID {old_pid}. Exiting.")
                    sys.exit(0)
        except Exception:
            pass

    with open(WATCHDOG_PID_FILE, "w") as f:
        f.write(str(os.getpid()))

def is_service_alive():
    # 1. Check PID file
    pid = None
    if os.path.exists(SERVICE_PID_FILE):
        try:
            with open(SERVICE_PID_FILE, "r") as f:
                pid = int(f.read().strip())
        except Exception:
            pid = None

    if pid and psutil.pid_exists(pid):
        try:
            proc = psutil.Process(pid)
            if "python" in proc.name().lower():
                # Process is alive; now check heartbeat freshness (within 20s)
                if os.path.exists(HEARTBEAT_FILE):
                    try:
                        with open(HEARTBEAT_FILE, "r") as f:
                            ts = float(f.read().strip())
                        if time.time() - ts < 20.0:
                            return True
                    except Exception:
                        pass
        except Exception:
            pass

    return False

def run_watchdog():
    check_single_instance()
    print("🛡️ [Haseen Kids] Mutual Watchdog Process active.")
    py_exe = sys.executable

    # Initial grace period: wait 8 seconds on startup before evaluating service health
    time.sleep(8)

    while True:
        try:
            if not is_service_alive():
                print("⚠️ [Watchdog Alert] Haseen Service not running or frozen! Respawning...")
                # Launch detached service
                flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                subprocess.Popen([py_exe, SERVICE_SCRIPT], creationflags=flags)
                # Wait 10s after respawn before checking again
                time.sleep(10)
            else:
                time.sleep(4)
        except KeyboardInterrupt:
            break
        except Exception as e:
            time.sleep(4)

if __name__ == "__main__":
    run_watchdog()
