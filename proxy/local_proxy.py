import asyncio
import json
import os
import sys
import urllib.parse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager
from proxy.filter_engine import SmartFilterEngine
from youtube.engine import YouTubeEngine
from core.approvals import ApprovalManager

# ---------------------------------------------------------------------------
# Kid-friendly block page (same palette as the desktop app)
# ---------------------------------------------------------------------------
BLOCKED_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>حَصِين • هذا الموقع مغلق</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg1:#241b52; --bg2:#3b2a7a; --card:#ffffff; --ink:#2b2350; --muted:#6b6390;
    --violet:#7c5cff; --pink:#ff6b9d; --teal:#22c1a8; --yellow:#ffd166; --orange:#ff9f1c;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
    padding:24px; font-family:'IBM Plex Sans Arabic','Segoe UI',Tahoma,sans-serif;
    background:linear-gradient(135deg,var(--bg1) 0%,var(--bg2) 55%,#4a2f8f 100%);
    color:var(--ink);
  }}
  .card {{
    background:var(--card); width:100%; max-width:640px; border-radius:28px;
    padding:36px 30px; box-shadow:0 24px 60px rgba(20,10,60,.45);
    border:4px solid rgba(255,255,255,.5);
  }}
  .mascot {{
    width:92px; height:92px; margin:0 auto 14px; border-radius:50%;
    background:linear-gradient(135deg,var(--yellow),var(--orange));
    display:flex; align-items:center; justify-content:center; font-size:46px;
    box-shadow:0 10px 24px rgba(255,159,28,.45);
    animation:bob 2.6s ease-in-out infinite;
  }}
  @keyframes bob {{ 0%,100%{{transform:translateY(0)}} 50%{{transform:translateY(-8px)}} }}
  h1 {{ text-align:center; margin:0 0 6px; font-size:30px; color:var(--violet); letter-spacing:-.3px; }}
  .sub {{ text-align:center; color:var(--muted); font-size:16px; line-height:1.7; margin:0 0 18px; }}
  .domain {{
    background:#f4f1ff; border:2px dashed var(--violet); color:#4b3aa3;
    padding:12px; border-radius:16px; text-align:center; font-size:18px;
    font-weight:700; margin:0 0 14px; word-break:break-all;
  }}
  .reason {{
    background:#fff7e8; border-right:6px solid var(--orange); border-radius:14px;
    padding:12px 14px; font-size:15px; color:#7a5a13; margin-bottom:22px;
  }}
  .btn {{
    border:none; border-radius:16px; padding:14px 26px; font-size:17px; font-weight:700;
    cursor:pointer; font-family:inherit; transition:transform .15s, box-shadow .15s;
    color:#fff; background:linear-gradient(135deg,var(--violet),var(--pink));
    box-shadow:0 8px 20px rgba(124,92,255,.4);
  }}
  .btn:hover {{ transform:translateY(-2px); }}
  .btn.green {{ background:linear-gradient(135deg,var(--teal),#34d399); box-shadow:0 8px 20px rgba(34,193,168,.4); }}
  .btn.ghost {{ background:#f4f1ff; color:var(--violet); box-shadow:none; }}
  label {{ display:block; font-weight:700; margin:16px 0 6px; font-size:15px; }}
  input[type=text], textarea {{
    width:100%; padding:12px 14px; border-radius:14px; border:2px solid #e4e0f7;
    font-family:inherit; font-size:15px; background:#fbfaff; color:var(--ink); outline:none;
  }}
  input[type=text]:focus, textarea:focus {{ border-color:var(--violet); }}
  .row {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }}
  .row .btn {{ flex:1; min-width:180px; }}
  .waiting {{ display:none; text-align:center; background:#eefaf7; border:2px solid var(--teal);
              border-radius:18px; padding:20px; margin-top:18px; }}
  .waiting h3 {{ margin:0 0 8px; color:#0f766e; font-size:19px; }}
  .pulse {{ animation:pulse 1.6s infinite; }}
  @keyframes pulse {{ 0%,100%{{opacity:.55}} 50%{{opacity:1}} }}
  .foot {{ text-align:center; color:var(--muted); font-size:13px; margin-top:22px; }}
  .divider {{ height:2px; background:linear-gradient(90deg,transparent,#eee9ff,transparent); margin:24px 0 4px; }}
  .hint {{ font-size:13px; color:var(--muted); margin-top:6px; }}
</style>
</head>
<body>
<div class="card">
  <div class="mascot">🦉</div>
  <h1>هذا الموقع مغلق حالياً</h1>
  <p class="sub">فريق <strong>حَصِين</strong> يحميك — الموقع ليس ضمن قائمة المواقع المسموح بها.</p>
  <div class="domain">{domain}</div>
  <div class="reason"><strong>السبب:</strong> {reason}</div>

  <div id="waitingCard" class="waiting">
    <h3 class="pulse">⏳ تم إرسال طلبك إلى والدك</h3>
    <p>سيُفتح الموقع تلقائياً بمجرد الموافقة — لا تغلق هذه الصفحة.</p>
  </div>

  <div id="formContainer">
    <label for="reqReason">اكتب لوالدك سبب حاجتك للموقع 👇</label>
    <textarea id="reqReason" rows="2" placeholder="مثال: هذا موقع واجب العلوم"></textarea>
    <div class="row">
      <button class="btn" id="btnSubmitReq" onclick="sendRequestAsync(event)">📨 اطلب إذن والدك</button>
    </div>

    <div class="divider"></div>
    <label for="codeInput">أو أدخل رمز الموافقة من والدك</label>
    <input type="text" id="codeInput" placeholder="6 أرقام" maxlength="8">
    <div class="row">
      <button class="btn green" onclick="verifyCode()">✅ تفعيل الرمز وفتح الموقع</button>
      <a class="btn ghost" href="http://127.0.0.1:8089/" style="text-decoration:none;text-align:center;line-height:1.4">🏠 الرئيسية</a>
    </div>
    <p class="hint">الرمز يصلك من والدك على هاتفه أو بريده فور موافقته.</p>
  </div>

  <p class="foot">حَصِين للأطفال • حماية ذكية بدون إزعاج 🛡️</p>
</div>

<script>
const DOMAIN = {domain_json};
const FULL_URL = {url_json};
const BASE = 'http://127.0.0.1:8089';

async function sendRequestAsync(e) {{
  if (e) e.preventDefault();
  const btn = document.getElementById('btnSubmitReq');
  const reason = (document.getElementById('reqReason').value || '').trim() || 'طلب فتح من الطفل';
  btn.disabled = true; btn.textContent = 'جاري الإرسال... ⏳';
  try {{
    const fd = new URLSearchParams({{ domain: DOMAIN, url: FULL_URL, reason: reason }});
    await fetch(BASE + '/request_exception', {{ method: 'POST', body: fd }});
    document.getElementById('formContainer').style.display = 'none';
    document.getElementById('waitingCard').style.display = 'block';
    const timer = setInterval(async () => {{
      try {{
        const r = await fetch(BASE + '/check_status?domain=' + encodeURIComponent(DOMAIN));
        const d = await r.json();
        if (d.allowed) {{
          clearInterval(timer);
          document.getElementById('waitingCard').innerHTML =
            '<h3 style="color:#0f766e">🎉 وافق والدك! جاري فتح الموقع...</h3>';
          setTimeout(() => {{ window.location.href = FULL_URL || ('https://' + DOMAIN); }}, 900);
        }}
      }} catch (e) {{}}
    }}, 3000);
  }} catch (err) {{
    btn.disabled = false; btn.textContent = '📨 اطلب إذن والدك';
  }}
}}

async function verifyCode() {{
  const code = (document.getElementById('codeInput').value || '').trim();
  if (!code) {{ alert('أدخل الرمز الذي أعطاه لك والدك'); return; }}
  try {{
    const fd = new URLSearchParams({{ code: code }});
    const r = await fetch(BASE + '/verify_code', {{ method: 'POST', body: fd }});
    const d = await r.json();
    if (d.success) {{
      window.location.href = d.url || ('https://' + DOMAIN);
    }} else {{
      alert(d.message || 'الرمز غير صحيح');
    }}
  }} catch (e) {{ alert('تعذر التحقق من الرمز'); }}
}}
</script>
</body>
</html>"""


class LocalProxyServer:
    def __init__(self, host="127.0.0.1", port=8089):
        self.host = host
        self.port = port
        self.db = DBManager()
        self.filter = SmartFilterEngine(self.db)
        self.youtube = YouTubeEngine()
        self.approvals = ApprovalManager(self.db)
        self.server = None

    async def start(self):
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"Haseen Local Proxy running on {self.host}:{self.port}")
        async with self.server:
            await self.server.serve_forever()

    # -- helpers ------------------------------------------------------------
    def _block_page(self, domain, url, reason):
        return BLOCKED_HTML_TEMPLATE.format(
            domain=domain,
            reason=reason,
            domain_json=json.dumps(domain, ensure_ascii=False),
            url_json=json.dumps(url, ensure_ascii=False),
        )

    @staticmethod
    def _http(status, body, ctype="text/html; charset=utf-8", extra=""):
        raw = body.encode("utf-8")
        head = (
            f"HTTP/1.1 {status}\r\n"
            f"Content-Type: {ctype}\r\n"
            f"Content-Length: {len(raw)}\r\n"
            f"Cache-Control: no-store\r\n"
            f"Connection: close\r\n{extra}\r\n"
        )
        return head.encode("utf-8") + raw

    async def handle_client(self, client_reader, client_writer):
        try:
            req_line = await client_reader.readline()
            if not req_line:
                client_writer.close()
                return

            parts = req_line.decode('utf-8', errors='ignore').strip().split()
            if len(parts) < 2:
                client_writer.close()
                return

            method, target = parts[0], parts[1]

            headers = {}
            while True:
                line = await client_reader.readline()
                if not line or line == b'\r\n':
                    break
                h_parts = line.decode('utf-8', errors='ignore').split(':', 1)
                if len(h_parts) == 2:
                    headers[h_parts[0].strip().lower()] = h_parts[1].strip()

            host_header = headers.get('host', '')
            if f"127.0.0.1:{self.port}" in host_header or f"localhost:{self.port}" in host_header:
                await self.handle_internal_route(method, target, client_reader, client_writer, headers)
                return

            if method.upper() == 'CONNECT':
                await self.handle_connect(target, client_reader, client_writer)
            else:
                await self.handle_http(method, target, headers, client_reader, client_writer)

        except Exception:
            try:
                client_writer.close()
            except Exception:
                pass

    async def handle_connect(self, target, client_reader, client_writer):
        """Handles HTTPS CONNECT tunnelling with safety inspection."""
        host = target.split(':')[0]
        port = int(target.split(':')[1]) if ':' in target else 443

        action, category, reason, src = self.filter.evaluate_url(f"https://{host}/")

        if action in ('BLOCK', 'BEDTIME', 'TIME_EXPIRED'):
            # Browsers cannot render a body for a rejected CONNECT, so we answer
            # with a redirect hint and let the browser extension (installed by
            # Haseen) show the friendly block page for this exact error.
            resp = (
                "HTTP/1.1 403 Forbidden\r\n"
                "X-Haseen-Blocked: 1\r\n"
                f"X-Haseen-Domain: {host}\r\n"
                f"X-Haseen-Reason: {urllib.parse.quote(reason)}\r\n"
                "Content-Length: 0\r\n"
                "Connection: close\r\n\r\n"
            )
            client_writer.write(resp.encode('utf-8'))
            await client_writer.drain()
            client_writer.close()
            self.db.log_activity(host, f"https://{target}", category, action, reason)
            return

        try:
            remote_reader, remote_writer = await asyncio.open_connection(host, port)
            client_writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            await client_writer.drain()

            self.db.log_activity(host, f"https://{target}", category, "ALLOW", reason)

            async def pipe(r, w):
                try:
                    while True:
                        buf = await r.read(16384)
                        if not buf:
                            break
                        w.write(buf)
                        await w.drain()
                except Exception:
                    pass
                finally:
                    try:
                        w.close()
                    except Exception:
                        pass

            await asyncio.gather(
                pipe(client_reader, remote_writer),
                pipe(remote_reader, client_writer)
            )
        except Exception:
            try:
                client_writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                await client_writer.drain()
                client_writer.close()
            except Exception:
                pass

    async def handle_http(self, method, target, headers, client_reader, client_writer):
        """Handles plain HTTP requests (and serves the friendly block page)."""
        url = target if target.startswith("http") else f"http://{headers.get('host', '')}{target}"
        host = headers.get('host', '').split(':')[0]

        action, category, reason, src = self.filter.evaluate_url(url)

        if action == "REDIRECT_YOUTUBE":
            self.youtube.play_video(url)
            html = (
                "<html dir='rtl'><body style='font-family:Tahoma;background:#241b52;color:#fff;"
                "text-align:center;padding:60px'>"
                "<h2>🎬 تم فتح الفيديو في مشغل حصين النظيف بدون إعلانات</h2>"
                "<p style='color:#c7bdf5'>يمكنك متابعة الدرس من نافذة المشغل.</p></body></html>"
            )
            client_writer.write(self._http("200 OK", html))
            await client_writer.drain()
            client_writer.close()
            return

        if action in ['BLOCK', 'BEDTIME', 'TIME_EXPIRED']:
            html = self._block_page(host, url, reason)
            client_writer.write(self._http("403 Forbidden", html))
            await client_writer.drain()
            client_writer.close()
            self.db.log_activity(host, url, category, action, reason)
            return

        try:
            remote_reader, remote_writer = await asyncio.open_connection(host, 80)
            req = f"{method} {target} HTTP/1.1\r\n"
            for k, v in headers.items():
                req += f"{k}: {v}\r\n"
            req += "\r\n"
            remote_writer.write(req.encode('utf-8'))
            await remote_writer.drain()

            while True:
                buf = await remote_reader.read(16384)
                if not buf:
                    break
                client_writer.write(buf)
                await client_writer.drain()
        except Exception:
            pass
        finally:
            client_writer.close()

    async def handle_internal_route(self, method, target, reader, writer, headers):
        """Internal API used by the block page, tray icon and browser extension."""
        content_len = int(headers.get('content-length', 0) or 0)
        body = b""
        if content_len > 0:
            body = await reader.read(content_len)
        raw_body = body.decode('utf-8', errors='ignore')
        form_data = urllib.parse.parse_qs(raw_body)
        # The browser extension (and any other client) may post JSON instead of
        # a form; accept both so a request never silently arrives with an empty
        # domain.
        if raw_body.lstrip().startswith('{'):
            try:
                for _k, _v in json.loads(raw_body).items():
                    form_data[_k] = [str(_v)]
            except Exception:
                pass
        parsed = urllib.parse.urlparse(target)
        qs = urllib.parse.parse_qs(parsed.query)

        def send(payload_bytes, ctype="application/json; charset=utf-8", status="200 OK"):
            head = (
                f"HTTP/1.1 {status}\r\n"
                f"Content-Type: {ctype}\r\n"
                f"Content-Length: {len(payload_bytes)}\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "Cache-Control: no-store\r\n"
                "Connection: close\r\n\r\n"
            ).encode("utf-8")
            writer.write(head + payload_bytes)
            return writer.drain()

        # 1. Block page rendering for a domain blocked at CONNECT level
        if parsed.path == "/blocked":
            dom = qs.get('domain', [''])[0]
            full = qs.get('url', [f"https://{dom}"])[0]
            writer.write(self._http("200 OK", self._block_page(dom, full, "موقع خارج قائمة المواقع المسموح بها")))
            await writer.drain()
            writer.close()
            return

        # 2. Child submits an exception request
        if "/request_exception" in target:
            domain = form_data.get('domain', [''])[0]
            url = form_data.get('url', [''])[0]
            reason = form_data.get('reason', [''])[0]
            if not (domain or url):
                await send(json.dumps({"success": False,
                                       "message": "لم يصل اسم الموقع. أعد المحاولة من صفحة الحجب."},
                                      ensure_ascii=False).encode())
                writer.close()
                return
            if not domain:
                domain = urllib.parse.urlparse(url if '//' in url else 'https://' + url).netloc
            try:
                ok, msg, perm_code, temp_code = self.approvals.create_and_send_request(domain, url, reason)
            except Exception as e:
                ok, msg = False, str(e)
            await send(json.dumps({"success": bool(ok), "message": msg}, ensure_ascii=False).encode())
            writer.close()
            return

        # 3. Child enters the approval code
        if "/verify_code" in target:
            code = form_data.get('code', qs.get('code', ['']))[0]
            success, msg, typ, domain = self.db.verify_and_apply_code(code)
            payload = json.dumps({
                "success": success, "message": msg, "type": typ,
                "url": (f"https://{domain}" if success and domain else "")
            }, ensure_ascii=False).encode()
            await send(payload)
            writer.close()
            return

        # 4. Block page polls this while waiting for the parent
        if "/check_status" in target:
            chk_domain = qs.get('domain', [''])[0]
            allowed = False
            if chk_domain:
                # A parent approval is honoured first: it must unlock the page
                # even for domains that sit on the blacklist.
                try:
                    if self.db.has_active_exception(chk_domain):
                        allowed = True
                except Exception:
                    pass
                if not allowed:
                    action, cat, reason, src = self.filter.evaluate_url(f"https://{chk_domain}/")
                    allowed = action in ('ALLOW', 'REDIRECT_YOUTUBE')
            await send(json.dumps({"allowed": allowed, "domain": chk_domain}, ensure_ascii=False).encode())
            writer.close()
            return

        # 5. Extension asks: should this navigation be redirected to the clean player?
        if "/should_redirect" in target:
            url = qs.get('u', [''])[0]
            action, cat, reason, src = self.filter.evaluate_url(url)
            await send(json.dumps({
                "action": action,
                "redirect": f"http://127.0.0.1:{self.port}/open_clean?u=" + urllib.parse.quote(url, safe='')
                if action == "REDIRECT_YOUTUBE" else "",
                "blocked": action in ("BLOCK", "BEDTIME", "TIME_EXPIRED"),
                "block_page": f"http://127.0.0.1:{self.port}/blocked?domain=" +
                              urllib.parse.quote(urllib.parse.urlparse(url).netloc or '', safe='')
                              + "&url=" + urllib.parse.quote(url, safe=''),
                "reason": reason
            }, ensure_ascii=False).encode())
            writer.close()
            return

        # 6. Clean player launcher
        if "/open_clean" in target:
            video_url = qs.get('u', [''])[0]
            ok, msg = self.youtube.play_video(video_url)
            html = (
                "<html dir='rtl'><body style='font-family:Tahoma;background:#241b52;color:#fff;"
                "text-align:center;padding:60px'>"
                f"<h2>{'🎬 تم فتح المشغل النظيف' if ok else '⚠️ تعذر تشغيل الفيديو'}</h2>"
                f"<p style='color:#c7bdf5'>{msg}</p></body></html>"
            )
            writer.write(self._http("200 OK", html))
            await writer.drain()
            writer.close()
            return

        # 7. Health probe (used by the app, setup wizard and tests)
        if parsed.path in ("/", "/status", "/health"):
            try:
                left = self.db.get_pause_remaining()
            except Exception:
                left = 0
            payload = json.dumps({
                "status": "online", "service": "Haseen Local Proxy",
                "port": self.port, "version": "1.3.3",
                "paused": bool(left), "pause_seconds_left": left
            }, ensure_ascii=False).encode()
            await send(payload)
            writer.close()
            return

        writer.write(self._http("404 Not Found", "Not Found", "text/plain; charset=utf-8"))
        await writer.drain()
        writer.close()


if __name__ == "__main__":
    proxy = LocalProxyServer()
    asyncio.run(proxy.start())
