# Haseen Kids | حَصِين للأطفال — Release 1.3.3 🛡️

> Fixes the freeze when clicking the app-password button and when maximising the window

## What was really happening

A window freezes when the **GUI thread** is made to wait. Two such paths exist in the code,
and both were measured on the development machine:

| Path | Before | After |
|---|---|---|
| Proxy port probe at startup (`connect_ex` with no timeout) | **2.03 s** of a frozen window | 0.30 s (short timeout) |
| Opening the app-password link via `QDesktopServices.openUrl` | waits for ShellExecute **on the GUI thread** | opened on a worker thread, returns in **0.001 s** |
| 3-second gauge timer running three queries | timers could queue up and starve the event loop | every 5 s, re-entrancy guard, no repaint without a change |

## What is new

- **Scrollable tabs**: the main window and every tab of the parent panel now live inside a
  `QScrollArea`, so the lower buttons **no longer require maximising the window**.
- **Freeze watchdog**: a light thread monitors a GUI heartbeat; if it stops for 8 s it writes
  **every thread's stack** to `logs\haseen_freeze.log` — diagnosis becomes evidence, not a guess.
- **Diagnostic hotkey**: `Ctrl + Shift + F12` writes the report on demand and shows its path.
- **Links open off the GUI thread** (all free API-key pages and Google app passwords).
- Parent-panel buttons are fully visible, with a minimum window size of 840×560.

## Proof (measured after the fix)

| Test | Result |
|---|---|
| Main window construction time | **3.02 s → 1.32 s** |
| Event-loop turns at 1920×1080 maximised | 541 turns/s (healthy) |
| Four resizes up to 1920×1080 | 0.14 s |
| Probe of a closed port | 0.30 s (was 2.03) |
| Opening an external link | returns in 0.001 s |
| Automated tests | **61 / 61 passing** |

## If it freezes again

Run the program, and when it freezes press **Ctrl+Shift+F12** (or wait 8 seconds), then send
the file `logs\haseen_freeze.log` — it points at the exact line responsible.

**Built by:** SAIP Consulting — **License:** MIT
