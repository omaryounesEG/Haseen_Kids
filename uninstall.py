"""
Haseen Kids - Final removal tool (works fully offline).

Terminal output is intentionally ENGLISH ONLY: Windows CMD cannot render Arabic
reliably (CP437/CP1252), which garbles the text. The GUI stays Arabic.

Three independent offline ways to remove the program (a parent may have
forgotten the password). Any ONE of them is enough:

    1) Parent password
    2) 16-character Recovery Key (printed at install time)
    3) Windows Administrator rights (proves an adult owns the PC, no internet)

Usage:
    python uninstall.py                  interactive menu
    python uninstall.py --pwd XXX        password path
    python uninstall.py --key XXXX-...   recovery-key path
    python uninstall.py --admin          admin path (requires elevation)
    python uninstall.py --full           elevate, then remove everything
    add --delete-files to also delete the program folder.
"""

import os
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.db_manager import DBManager
from core.security import SecurityManager
import core.recovery as recovery


BANNER = """
==============================================================
        HASEEN KIDS - FINAL REMOVAL TOOL  (offline)
==============================================================
"""


def _print_summary(summary):
    print("\n" + "=" * 62)
    print("  DONE - your PC is back to its original state")
    print("=" * 62)
    print(f"  - Processes stopped        : {summary.get('processes', 0)}")
    print(f"  - Browser policies removed : {summary.get('policies', 0)}")
    print(f"  - Firewall rules removed   : {summary.get('firewall', 0)}")
    print(f"  - Autostart entries removed: {summary.get('autostart', 0)}")
    print(f"  - State files cleaned      : {summary.get('state', 0)}")
    if summary.get("folder"):
        print("  - The program folder will be deleted in 2 seconds.")
    print("\n  NOTE: restart your browser to see the change.")
    print("=" * 62)


def do_remove(delete_files=False, reset_password_only=False, new_password=None):
    if reset_password_only:
        db = DBManager()
        SecurityManager(db).set_admin_password(new_password or "haseen2026")
        db.set_setting("recovery_key_hash", "")
        print(f"\n[OK] New password set: {new_password or 'haseen2026'}")
        return True

    summary = recovery.full_remove(delete_folder=delete_files)
    _print_summary(summary)
    return True


def authenticate(pwd=None, key=None, admin=False):
    """Returns (ok, mode, message)."""
    db = DBManager()

    if admin:
        if recovery.is_admin():
            return True, "admin", "Administrator rights verified"
        return False, "admin", "This process is not elevated"

    if key:
        if recovery.verify_recovery_key(db, key):
            return True, "key", "Recovery key verified"
        return False, "key", "Invalid recovery key"

    if pwd is not None:
        if SecurityManager(db).verify_admin(pwd):
            return True, "password", "Password verified"
        return False, "password", "Wrong password"

    return False, None, "No verification method"


def _ask_delete():
    ans = input("\nAlso delete the whole program folder? [y/N]: ").strip().lower()
    return ans in ("y", "yes")


def interactive():
    print(BANNER)
    print("Forgot the password? No problem - any ONE of these works:\n")
    print("  [1] I have the parent password")
    print("  [2] I have the 16-character Recovery Key (from the install sheet)")
    print("  [3] I am the PC administrator - use Windows Administrator rights")
    print("  [4] Reset the password only (keep the program)")
    print("  [0] Exit\n")

    choice = input("Choose a method: ").strip()

    if choice == "1":
        pwd = input("Parent password: ").strip()
        ok, _, msg = authenticate(pwd=pwd)
        if not ok:
            print(f"\n[ERROR] {msg}")
            return 1
        return 0 if do_remove(delete_files=_ask_delete()) else 1

    if choice == "2":
        key = input("Recovery key (e.g. ABCD-EFGH-JKLM-NPQR): ").strip()
        ok, _, msg = authenticate(key=key)
        if not ok:
            print(f"\n[ERROR] {msg}")
            return 1
        return 0 if do_remove(delete_files=_ask_delete()) else 1

    if choice == "3":
        if not recovery.is_admin():
            print("\nRequesting Administrator rights - press Yes in the Windows prompt...")
            if recovery.elevate_and_run("--admin --delete-files"):
                return 0
            print("[ERROR] Elevation cancelled.")
            return 1
        return 0 if do_remove(delete_files=_ask_delete()) else 1

    if choice == "4":
        print("\nPassword reset needs the recovery key or Administrator rights.")
        key = input("Recovery key (leave empty to use Administrator rights): ").strip()
        if key:
            ok, _, msg = authenticate(key=key)
        else:
            ok = recovery.is_admin()
            msg = "OK" if ok else "Run this tool as administrator"
        if not ok:
            print(f"\n[ERROR] {msg}")
            return 1
        newp = input("New password (empty = haseen2026): ").strip() or "haseen2026"
        return 0 if do_remove(reset_password_only=True, new_password=newp) else 1

    return 0


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--pwd")
    parser.add_argument("--key")
    parser.add_argument("--admin", action="store_true")
    parser.add_argument("--full", action="store_true", help="elevate and remove everything")
    parser.add_argument("--delete-files", action="store_true")
    parser.add_argument("--reset-password", metavar="NEW")
    parser.add_argument("--yes", action="store_true", help="no prompts")
    args = parser.parse_args()

    if args.full and not recovery.is_admin():
        print("Requesting Administrator rights...")
        ok = recovery.elevate_and_run("--admin --delete-files" if args.delete_files else "--admin")
        if not ok:
            print("[ERROR] Elevation failed. Right-click the file -> Run as administrator.")
            return 1
        return 0

    if args.reset_password:
        if authenticate(key=args.key, admin=args.admin)[0]:
            return 0 if do_remove(reset_password_only=True, new_password=args.reset_password) else 1
        print("[ERROR] Verification failed")
        return 1

    if args.admin or args.key or args.pwd is not None:
        ok, _, msg = authenticate(pwd=args.pwd, key=args.key, admin=args.admin)
        if not ok:
            print(f"[ERROR] {msg}")
            return 1
        delete = args.delete_files or args.yes
        return 0 if do_remove(delete_files=delete) else 1

    try:
        return interactive()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
