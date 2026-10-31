# Haseen Kids | حَصِين للأطفال — Release 1.3.2 🛡️

> Installer fix: the one-line CMD command no longer installs inside `C:\Windows\System32`

## What went wrong

The one-line installer extracted the files into the **current folder** — which was
`C:\Windows\System32` because the CMD window was elevated. The program and its database
(`database\haseen.db`) were scattered inside a protected Windows folder, so saving failed
and the program stopped working.

## What is fixed

| Fix | Detail |
|---|---|
| **Never installs into the folder it runs from** | Picks a safe target: `C:\Haseen_Kids`, or `%LOCALAPPDATA%\Haseen_Kids` when C: is not writable |
| **Refuses protected folders** | `C:\Windows` and `Program Files` are rejected and the install is redirected |
| **Protects the parent password** | Copies with `robocopy` while excluding `*.db`, `*.db-wal`, `*.db-shm` and `recovery.sig` |
| **Clear path reporting** | Prints the final install folder, then runs `Repair.bat /auto` and `Setup.bat` |
| **Safe CMD command** | The script is downloaded to `%TEMP%` first, so nothing is written into the folder your CMD sits in |

## Install / update command (use this one)

```cmd
curl -sSL https://raw.githubusercontent.com/omaryounesEG/Haseen_Kids/main/install_from_github.bat -o "%TEMP%\haseen_install.bat" && "%TEMP%\haseen_install.bat"
```

**PowerShell:**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=Join-Path $env:TEMP 'haseen_install.bat'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://raw.githubusercontent.com/omaryounesEG/Haseen_Kids/main/install_from_github.bat',$d); & $d"
```

## Proof (real tests)

| Test | Result |
|---|---|
| Install into a custom folder that already had `haseen.db` | The file was **left untouched** (content verified) |
| Install aimed at `C:\Windows\System32\HaseenTest` | **Refused** and redirected to `%LOCALAPPDATA%`; nothing written into System32 |
| Files copied | 73 files, including `Repair.bat` and `core/crashguard.py` |
| Automated tests | **58 / 58 passing** |

## If your current copy is broken

1. Move/delete the program folder from `C:\Windows\System32` (needs administrator rights).
2. Run the install command above — it installs into `C:\Haseen_Kids`.
3. If you have `C:\Windows\System32\database\haseen.db`, copy it to `C:\Haseen_Kids\database\`
   **before** the first start to keep your parent password.

**Built by:** SAIP Consulting — **License:** MIT
