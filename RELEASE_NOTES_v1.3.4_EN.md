# Haseen Kids | حَصِين للأطفال — Release 1.3.4 🛡️

> One copy only — this ends the "several icons next to the clock" problem

## The real reason it stopped: multiple copies

You noticed more than one copy running by the clock, and that is the disease itself:

| Copy | What it does |
|---|---|
| First | proxy on port 8089 + tracker + writes to `haseen.db` |
| Second | fights for the same port, writes the same database, slows the PC |
| Third | each copy thinks the others are stuck, so things close or stop |

Two code-level causes made the copies multiply:

1. **No single-instance lock** — every shortcut click or startup entry created a new copy.
2. **Hard-coded `H:\` paths** inside `core/service.py` and `core/watchdog.py`
   (`H:\Haseen_Kids\core\service.pid`). Your install lives in `C:\Haseen_Kids`, so neither
   could see the other and each kept spawning an extra service.

## What is fixed

| Fix | Effect |
|---|---|
| **Windows mutex single-instance lock** | A second launch raises the open window and exits immediately |
| **Clear Arabic message** | "البرنامج مفتوح بالفعل…" instead of a silent duplicate |
| **Relative paths** in `service.py` / `watchdog.py` | No extra service copies on any machine |
| **Automatic duplicate killing removed** | A first attempt could close the running copy itself — removed entirely |
| **`logs\haseen_freeze.log`** | Not created when there is no freeze — that is normal. Created only after an 8-second GUI stall or on `Ctrl+Shift+F12` |

## Proof (real tests on the machine)

| Test | Result |
|---|---|
| Second launch while the first runs | exits with code 0 and raises the existing window |
| Lock across two processes | `first acquire: True` / `second: False` |
| Window stays alive | still running after 20 seconds (no silent exit) |
| Service/watchdog paths | `H:\...` → derived from the file location |
| Automated tests | **61 / 61 passing** |

## What to do now (two steps)

1. **Close every running Haseen copy**: right-click each tray icon → Exit, or end the
   `python.exe` processes that point at `Haseen_Kids` in Task Manager
   (new builds cannot duplicate themselves, but old open copies stay until closed).
2. Update with the usual command:

```cmd
curl -sSL https://raw.githubusercontent.com/omaryounesEG/Haseen_Kids/main/install_from_github.bat -o "%TEMP%\haseen_install.bat" && "%TEMP%\haseen_install.bat"
```

After the update: one copy, one icon, and any further launch raises the same window.

## If a freeze returns

Press `Ctrl + Shift + F12` and send `logs\haseen_freeze.log`.
If the file does not exist, the interface never actually froze — the copies were competing.

**Built by:** SAIP Consulting — **License:** MIT
