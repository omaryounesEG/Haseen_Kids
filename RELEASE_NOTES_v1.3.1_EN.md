# Haseen Kids | حَصِين للأطفال — Release 1.3.1 🛡️

> The app no longer closes when you click the app-password button or save the mail
> settings + a self-repair tool + a visible pause button (tray and window)

## The main fix: an error can no longer close the program

**What you saw:** clicking “Get app password from Google” or saving the email settings
closed the program instantly, and afterwards it would not open at all.

**The real cause (two problems together):**

1. **PyQt terminates the whole process on any unhandled exception inside a button or an
   event.** So a single failed save (for example a read-only database) = a silent exit
   with no message.
2. The program was running from a **protected folder** (`C:\Windows\System32`), which
   makes the database read-only — so the save failed in the first place.

**What changed:**

| Fix | Effect |
|---|---|
| **Global crash guard** (`core/crashguard.py`) | Every error is written to `logs\haseen_error.log`, the parent sees a clear Arabic message, and the **app keeps running** |
| Actionable messages instead of a crash | “Database is read-only → run as administrator or move the folder” / “Component missing → run Repair.bat” |
| **Mail and AI checks run off the UI thread** | No more freezing while Gmail or an AI provider is tested; you can keep working |
| Refuses to run from protected Windows folders | A clear message instead of a mysterious exit |
| New `Repair.bat` | Verifies/rebuilds the environment, backs up the database, and **keeps** the parent password |
| `Unknown property cursor` QSS warnings fixed | A clean console |

## The pause is now easy to find

- **“⏸️ Pause” button at the top of the program window**, next to the language button —
  opens the duration list (15 min / 30 min / 1 hour / 4 hours) and asks the parent password.
- **Right-click the tray icon**: the same four durations + “▶️ Resume now” + a status line
  showing the remaining time.
- On first run a balloon explains that all controls live in the tray icon.
- Protection resumes **automatically** when the timer ends.

## If the program is not working on your machine now

1. Move the folder to `C:\Haseen_Kids` (never run it from `C:\Windows` or `Program Files`).
2. Run **`Repair.bat`** — it checks Python, rebuilds the environment if needed and backs up the database.
3. Start `scripts\run_all.bat` or the desktop shortcut.
4. If it happens again, send `logs\haseen_error.log` — it holds the error in plain text.


## Installer fix (`install_from_github.bat`) — important

**What happened on your machine:** the one-line CMD command extracted the files into the
**current folder** (which was `C:\Windows\System32` because the CMD window was elevated),
so the program and its database ended up inside a protected Windows folder — which broke
saving and, in turn, the program itself.

**What the script does now:**
- **It never installs into the folder it was started from.** It picks a safe target:
  `C:\Haseen_Kids` (or `%LOCALAPPDATA%\Haseen_Kids` when C: is not writable).
- `C:\Windows` and `Program Files` are refused automatically and redirected.
- Files are copied with `robocopy` while **excluding** `*.db`, `*.db-wal`, `*.db-shm` and
  `recovery.sig` — the parent password and the lists are never overwritten.
- It prints the final install path, runs a quick health check (`Repair.bat /auto`) and then `Setup.bat`.
- The published command now downloads the script to `%TEMP%` first, so nothing is written
  into the folder your CMD window happens to sit in:

```cmd
curl -sSL https://raw.githubusercontent.com/omaryounesEG/Haseen_Kids/main/install_from_github.bat -o "%TEMP%\haseen_install.bat" && "%TEMP%\haseen_install.bat"
```

**Verified for real:** a test install into a custom folder left the existing `haseen.db`
untouched, and an install aimed at `C:\Windows\System32` was refused and redirected with
nothing written into System32.

## Update

Parent panel → “🔄 Updates & maintenance” → **“🚀 Update now”**, or `scripts\update.bat`.
Updating never wipes the password, the lists or the logs.

## Quality

| Item | Result |
|---|---|
| Automated tests | **58 / 58 passing** |
| “Survives an error” test | executed for real: an exception inside a slot → the app stayed alive and logged it |
| UI render check | every window renders successfully (headless) |

**Built by:** SAIP Consulting — **License:** MIT
