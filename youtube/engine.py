import os
import re
import json
import urllib.parse
import urllib.request
import subprocess
import yt_dlp

class YouTubeEngine:
    def __init__(self):
        node_path = "C:\\Program Files\\nodejs\\node.exe"
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'nocheckcertificate': True
        }
        if os.path.isfile(node_path):
            self.ydl_opts['js_runtimes'] = {'node': {'path': node_path}}

        self.vlc_path = self._find_vlc_path()
        self.mpv_path = self._find_mpv_path()

    def _find_vlc_path(self):
        candidates = [
            "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
            "C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe",
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
        return None

    def _find_mpv_path(self):
        candidates = [
            "H:\\Haseen_Kids\\bin\\mpv.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "mpv", "mpv.exe")
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
        # Check if in PATH
        try:
            res = subprocess.run(["where", "mpv"], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip().splitlines()[0]
        except Exception:
            pass
        return None

    @staticmethod
    def extract_video_id(url):
        """Extracts 11-character YouTube video ID from various URL formats"""
        if not url:
            return None
        patterns = [
            r'(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/shorts\/)([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$'
        ]
        for pat in patterns:
            match = re.search(pat, url)
            if match:
                return match.group(1)
        return None

    def get_sponsorblock_segments(self, video_id):
        """
        Queries the SponsorBlock API for segments to skip (sponsors, intros, selfpromo, etc.)
        Returns a list of dicts: [{'start': 10.5, 'end': 34.2, 'category': 'sponsor'}, ...]
        """
        if not video_id:
            return []
        api_url = f"https://sponsor.ajay.app/api/skipSegments?videoID={video_id}&categories=[\"sponsor\",\"intro\",\"outro\",\"selfpromo\",\"interaction\"]"
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'HaseenKids/1.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    segments = []
                    for seg in data:
                        if 'segment' in seg and len(seg['segment']) == 2:
                            segments.append({
                                'start': seg['segment'][0],
                                'end': seg['segment'][1],
                                'category': seg.get('category', 'sponsor')
                            })
                    return segments
        except Exception:
            # Silently fallback if sponsorblock is unreachable
            pass
        return []

    # --- stream selection -------------------------------------------------
    # YouTube stopped serving progressive (video+audio in one file) formats for
    # most videos: the video and the audio arrive as two separate streams. Giving
    # the player only the video stream is why playback had no sound at all.
    @staticmethod
    def _pick(formats, want_video=True, want_audio=True, prefer_ext=None,
              prefer_direct=True):
        """Best format carrying the requested tracks, highest quality first.

        `prefer_direct` keeps HLS/DASH *manifests* out of the way: when the video
        and the audio come from two different URLs, pairing a .m3u8 manifest with
        a separate audio file fails in every player. A direct googlevideo mp4 URL
        pairs correctly, so direct streams win whenever they exist.
        """
        def has_v(f):
            return f.get('vcodec') not in (None, 'none') and bool(f.get('url'))

        def has_a(f):
            return f.get('acodec') not in (None, 'none') and bool(f.get('url'))

        def is_manifest(f):
            proto = (f.get('protocol') or '') + ' ' + (f.get('ext') or '')
            return ('m3u8' in proto) or ('dash' in proto)

        cands = []
        for f in formats:
            if not f.get('url'):
                continue
            if want_video and not has_v(f):
                continue
            if want_audio and not has_a(f):
                continue
            cands.append(f)

        if not cands:
            return None

        # 1) direct (non-manifest) streams
        if prefer_direct:
            direct = [f for f in cands if not is_manifest(f)]
            if direct:
                cands = direct

        # 2) container preference (mp4 wide support, m4a for audio)
        if prefer_ext:
            preferred = [f for f in cands if f.get('ext') == prefer_ext]
            if preferred:
                cands = preferred

        # 3) resolution first, then bitrate
        return max(cands, key=lambda f: ((f.get('height') or 0),
                                         (f.get('tbr') or f.get('abr') or 0)))

    def get_stream_info(self, video_url_or_id):
        """
        Resolves a YouTube video into playable URLs.

        Returns `muxed_url` when one file already has both tracks, otherwise a
        `video_url` + `audio_url` pair that the player must combine. `stream_url`
        stays for backwards compatibility (= muxed, else video).
        """
        video_id = self.extract_video_id(video_url_or_id)
        clean_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else video_url_or_id

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=False)
                formats = info.get('formats', []) or []

                # 1) A single file that already carries both tracks
                muxed = info.get('url') if (info.get('acodec') not in (None, 'none')
                                            and info.get('vcodec') not in (None, 'none')) else None
                if not muxed:
                    best_muxed = self._pick(formats, True, True, prefer_ext='mp4')
                    muxed = best_muxed.get('url') if best_muxed else None

                video_url = audio_url = None
                if not muxed:
                    # 2) Separate streams: pick mp4/h264 video for the widest
                    #    player support, and m4a/aac audio for the same reason.
                    v = self._pick(formats, True, False, prefer_ext='mp4')
                    a = self._pick(formats, False, True, prefer_ext='m4a')
                    video_url = v.get('url') if v else None
                    audio_url = a.get('url') if a else None

                    # If the chosen "video" secretly has audio too, no pairing needed
                    if v and v.get('acodec') not in (None, 'none'):
                        muxed, video_url, audio_url = video_url, None, None

                stream_url = muxed or video_url

                title = info.get('title', 'Unknown Title')
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail')
                uploader = info.get('uploader', 'Unknown Channel')

                sponsor_segments = self.get_sponsorblock_segments(video_id) if video_id else []

                return {
                    "video_id": video_id,
                    "stream_url": stream_url,
                    "muxed_url": muxed,
                    "video_url": video_url,
                    "audio_url": audio_url,
                    "has_audio": bool(muxed or audio_url),
                    "title": title,
                    "duration": duration,
                    "thumbnail": thumbnail,
                    "uploader": uploader,
                    "sponsor_segments": sponsor_segments,
                    "original_url": clean_url
                }
        except Exception as e:
            return {"error": str(e), "original_url": clean_url}

    def play_video(self, video_url_or_id):
        """
        Launches the isolated clean player (MPV, VLC, or the system player).

        When YouTube hands us separate video and audio streams, both are passed to
        the player (mpv: --audio-file, VLC: :input-slave) so the child hears the
        sound — otherwise the video would play silently.
        """
        info = self.get_stream_info(video_url_or_id)
        if "error" in info or not info.get("stream_url"):
            raw_err = str(info.get('error', 'No stream URL'))
            # Clean ANSI terminal escape codes
            clean_err = re.sub(r'\[[0-9;]*[mGKH]', '', raw_err)
            if "is unavailable" in clean_err:
                msg = "هذا المقطع غير متوفر على يوتيوب حالياً (ربما تم حذفه أو جعله خاصاً من قِبل الناشر)."
            elif "Private video" in clean_err:
                msg = "هذا الفيديو خاص ولا يمكن تشغيله."
            else:
                msg = f"تعذر استخراج البث النظيف: {clean_err}"
            return False, msg

        if not info.get("has_audio"):
            return False, "تعذر إيجاد مسار الصوت لهذا الفيديو، لذلك لن يعمل الصوت. جرّب فيديو آخر."

        video_url = info.get("video_url") or info["stream_url"]
        audio_url = info.get("audio_url")
        muxed = info.get("muxed_url")
        title = info["title"]
        sponsor_segs = info.get("sponsor_segments", [])

        # Priority 1: MPV (understands a separate audio track natively)
        if self.mpv_path:
            mpv_args = [self.mpv_path, muxed or video_url,
                        f"--title=حصين - {title}",
                        "--volume=100",
                        "--force-window=yes"]
            if audio_url and not muxed:
                mpv_args.append(f"--audio-file={audio_url}")
            try:
                subprocess.Popen(mpv_args)
                return True, "تم التشغيل عبر مشغل MPV المعزول" + (" (صوت + صورة)" if audio_url and not muxed else "")
            except Exception:
                pass

        # Priority 2: VLC (:input-slave attaches the audio track to the video)
        if self.vlc_path:
            vlc_args = [self.vlc_path, muxed or video_url,
                        "--meta-title", f"حصين: {title}",
                        "--play-and-exit",
                        "--volume-step", "4"]
            if audio_url and not muxed:
                vlc_args.append(f":input-slave={audio_url}")
            try:
                subprocess.Popen(vlc_args)
                return True, "تم التشغيل عبر مشغل VLC المعزول" + (" (صوت + صورة)" if audio_url and not muxed else "")
            except Exception as e:
                return False, f"خطأ أثناء تشغيل VLC: {e}"

        # Priority 3: system player — it can only open a single URL, so it works
        # only when the stream already contains both tracks.
        if muxed:
            try:
                os.startfile(muxed)
                return True, "تم التشغيل عبر مشغل الوسائط المعتمد في ويندوز"
            except Exception:
                pass

        return False, ("لم يتم العثور على مشغل وسائط يدعم دمج الصوت والصورة (VLC أو MPV). "
                       "ثبّت VLC المجاني ليعمل الصوت مع الفيديو.")

if __name__ == "__main__":
    engine = YouTubeEngine()
    test_id = "aqz-KE-bpKQ"
    print(f"Testing YouTube Engine for {test_id}...")
    res = engine.get_stream_info(test_id)
    print("Result title:", res.get("title"))
    print("Stream URL found:", bool(res.get("stream_url")))
    print("Sponsor segments found:", len(res.get("sponsor_segments", [])))
    print("VLC Path detected:", engine.vlc_path)
