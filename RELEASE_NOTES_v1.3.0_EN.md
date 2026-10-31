# Haseen Kids | حَصِين للأطفال — Release 1.3.0 🛡️

> Video sound fixed + a parent-controlled pause from the tray icon + a verified whitelist that covers every sub-domain.

## What's new in 1.3.0

### 🔊 Fixed: videos played with no sound at all
- **Root cause:** YouTube no longer serves a single progressive file (video + audio together)
  for most videos — it sends a video stream and a separate audio stream. The app was using
  the video URL only, so the player showed the picture and played **complete silence**.
- **Fix:** both streams are resolved and combined inside the player:
  - **MPV:** `--audio-file=<audio url>`
  - **VLC:** `:input-slave=<audio url>`
  - Direct mp4/m4a URLs are preferred over segmented manifests (m3u8) so the pairing works.
  - If a video really has no audio track, the child sees a clear message instead of silence.
- **Real proof:** capturing 6 seconds through VLC from the new audio track produced a 9.96 s
  stereo WAV with RMS amplitude **1021** (real sound), while the old video-only path produced
  a **0-byte** file — complete silence.

### ⏸️ Pause the whole protection from the tray icon (new)
- Right-click the Haseen icon next to the clock → **“Pause protection”**:
  **15 min / 30 min / 1 hour / 4 hours**, protected by the parent password.
- Protection resumes **by itself** when the timer ends, and there is a manual
  **“Resume now”** entry.
- The tray tooltip and status line show the remaining time, and the child's window shows
  “Protection paused — resumes in …”.
- The pause is stored in the database, so the proxy and the filter honour it instantly
  (verified live: a blocked site became reachable during the pause and blocked again after resume).

### 🌐 Verified: one entry covers everything — Classera, for example
- Adding `classera.com` once opens **every** sub-domain and inner page:
  `app.classera.com` · `lms.classera.com` · `school-142.classera.com` ·
  `cdn.static.classera.com` · `a.b.c.d.classera.com`, even with an explicit `:8443` port —
  and every path (`/ar/login`, `/student/course/12345/lesson/987?token=abc`, `/api/v1/media/video.m3u8`).
- Look-alikes stay out: `notclassera.com`, `classera.com.evil.net`, `classera.co`.
- **13 automated tests** cover these combinations.

## Install / update

**Updating an installed copy:** parent panel → “🔄 Updates & maintenance” →
**“🚀 Update now to the latest GitHub release”**, or `scripts\update.bat`.

**Fresh install (CMD):**
```cmd
curl -sSL https://raw.githubusercontent.com/omaryounesEG/Haseen_Kids/main/install_from_github.bat -o install_from_github.bat && install_from_github.bat
```

> Updating **never wipes** the parent password, the lists or the logs, and never cancels
> a running pause.

## Quality

| Item | Result |
|---|---|
| Automated tests | **52 / 52 passing** (was 41) |
| Video sound fix | verified by measuring a real audio signal |
| Temporary pause | verified live against a running proxy |
| Sub-domain coverage | 13 tests |

**Built by:** SAIP Consulting — **License:** MIT
