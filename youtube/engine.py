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

    def get_stream_info(self, video_url_or_id):
        """
        Extracts stream URL, title, duration, thumbnail, and sponsor segments in < 1 second.
        """
        video_id = self.extract_video_id(video_url_or_id)
        clean_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else video_url_or_id

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=False)
                stream_url = info.get('url')
                if not stream_url:
                    formats = info.get('formats', [])
                    # Priority 1: Progressive MP4 (both audio & video)
                    progs = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') != 'none' and f.get('url')]
                    if progs:
                        stream_url = progs[-1].get('url')
                    else:
                        # Priority 2: HLS m3u8 (native for VLC/MPV)
                        m3u8s = [f for f in formats if 'm3u8' in f.get('protocol', '') and f.get('url')]
                        if m3u8s:
                            stream_url = m3u8s[-1].get('url')
                        elif formats:
                            stream_url = formats[-1].get('url')

                title = info.get('title', 'Unknown Title')
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail')
                uploader = info.get('uploader', 'Unknown Channel')

                sponsor_segments = self.get_sponsorblock_segments(video_id) if video_id else []

                return {
                    "video_id": video_id,
                    "stream_url": stream_url,
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
        Launches isolated clean stream player (MPV or VLC) without any ads.
        """
        info = self.get_stream_info(video_url_or_id)
        if "error" in info or not info.get("stream_url"):
            return False, f"Failed to extract stream: {info.get('error', 'No stream URL')}"

        stream_url = info["stream_url"]
        title = info["title"]
        sponsor_segs = info.get("sponsor_segments", [])

        # Priority 1: MPV
        if self.mpv_path:
            mpv_args = [self.mpv_path, stream_url, f"--title=حصين - {title}"]
            # Add sponsorblock EDL or scripts if configured
            try:
                subprocess.Popen(mpv_args)
                return True, "Started MPV Player"
            except Exception as e:
                pass

        # Priority 2: VLC
        if self.vlc_path:
            vlc_args = [self.vlc_path, stream_url, "--meta-title", f"حصين: {title}", "--play-and-exit"]
            try:
                subprocess.Popen(vlc_args)
                return True, "Started VLC Player"
            except Exception as e:
                return False, f"Error launching VLC: {e}"

        return False, "No external player (MPV/VLC) available. Use internal embedded player."

if __name__ == "__main__":
    engine = YouTubeEngine()
    test_id = "aqz-KE-bpKQ"
    print(f"Testing YouTube Engine for {test_id}...")
    res = engine.get_stream_info(test_id)
    print("Result title:", res.get("title"))
    print("Stream URL found:", bool(res.get("stream_url")))
    print("Sponsor segments found:", len(res.get("sponsor_segments", [])))
    print("VLC Path detected:", engine.vlc_path)
