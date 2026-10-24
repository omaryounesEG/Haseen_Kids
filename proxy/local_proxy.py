import asyncio
import re
import urllib.parse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager
from proxy.filter_engine import SmartFilterEngine
from youtube.engine import YouTubeEngine
from core.approvals import ApprovalManager

BLOCKED_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>حصين - الموقع محجوب</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; text-align: center; padding: 40px 20px; }
        .card { background: #1e293b; max-width: 600px; margin: 0 auto; border-radius: 16px; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; }
        .icon { font-size: 64px; margin-bottom: 16px; }
        h1 { color: #f43f5e; margin-bottom: 8px; font-size: 26px; }
        p { color: #94a3b8; font-size: 16px; line-height: 1.6; }
        .domain-box { background: #0f172a; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 16px; color: #38bdf8; margin: 16px 0; word-break: break-all; }
        .btn { background: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-size: 16px; cursor: pointer; text-decoration: none; display: inline-block; transition: background 0.2s; }
        .btn:hover { background: #2563eb; }
        .form-box { margin-top: 24px; text-align: right; }
        input[type="text"], textarea { width: 100%; box-sizing: border-box; background: #0f172a; border: 1px solid #475569; color: white; padding: 10px; border-radius: 8px; margin-top: 6px; font-family: inherit; }
        .code-sec { margin-top: 20px; border-top: 1px dashed #334155; padding-top: 16px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">🛡️</div>
        <h1>الموقع محجوب لحمايتك</h1>
        <p>تم تقييد الوصول إلى هذا المحتوى وفقاً لسياسات الأمان الأسري في برنامج <strong>حصين</strong>.</p>
        <div class="domain-box">{domain}</div>
        <p><strong>السبب:</strong> {reason}</p>

        <div class="form-box">
            <h3>طلب إذن من ولي الأمر</h3>
            <form action="http://127.0.0.1:8089/request_exception" method="POST">
                <input type="hidden" name="domain" value="{domain}">
                <input type="hidden" name="url" value="{url}">
                <label>لماذا تحتاج فتح هذا الموقع؟</label>
                <textarea name="reason" rows="2" placeholder="اكتب سبب حاجتك للموقع (مثلاً: للبحث المدرسي)" required></textarea>
                <div style="text-align: center; margin-top: 12px;">
                    <button type="submit" class="btn">إرسال طلب استثناء لوالدي 📧</button>
                </div>
            </form>

            <div class="code-sec">
                <h3>هل لديك رمز موافقة من والدك؟</h3>
                <form action="http://127.0.0.1:8089/verify_code" method="POST">
                    <input type="text" name="code" placeholder="أدخل رمز الموافقة (مثال: 102948)" required>
                    <div style="text-align: center; margin-top: 10px;">
                        <button type="submit" class="btn" style="background: #10b981;">تفعيل الرمز وفتح الموقع ✅</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
"""

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

            # Read all request headers
            headers = {}
            while True:
                line = await client_reader.readline()
                if not line or line == b'\r\n':
                    break
                h_parts = line.decode('utf-8', errors='ignore').split(':', 1)
                if len(h_parts) == 2:
                    headers[h_parts[0].strip().lower()] = h_parts[1].strip()

            # Handle internal requests to proxy interface (127.0.0.1:8089)
            host_header = headers.get('host', '')
            if f"127.0.0.1:{self.port}" in host_header or f"localhost:{self.port}" in host_header:
                await self.handle_internal_route(method, target, client_reader, client_writer, headers)
                return

            if method.upper() == 'CONNECT':
                await self.handle_connect(target, client_reader, client_writer)
            else:
                await self.handle_http(method, target, headers, client_reader, client_writer)

        except Exception as e:
            try:
                client_writer.close()
            except Exception:
                pass

    async def handle_connect(self, target, client_reader, client_writer):
        """Handles HTTPS CONNECT tunneling with safety inspection"""
        host = target.split(':')[0]
        port = int(target.split(':')[1]) if ':' in target else 443

        action, category, reason, src = self.filter.evaluate_url(f"https://{host}")

        if action in ['BLOCK', 'BEDTIME', 'TIME_EXPIRED']:
            # Intercept blocked HTTPS connection
            html = BLOCKED_HTML_TEMPLATE.format(domain=host, url=f"https://{target}", reason=reason)
            resp = (
                f"HTTP/1.1 403 Forbidden\r\n"
                f"Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(html.encode('utf-8'))}\r\n"
                f"Connection: close\r\n\r\n"
                f"{html}"
            )
            client_writer.write(resp.encode('utf-8'))
            await client_writer.drain()
            client_writer.close()
            self.db.log_activity(host, f"https://{target}", category, action, reason)
            return

        # Allowed: establish remote connection and pipe data bidirectionally
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
        """Handles plain HTTP requests"""
        url = target if target.startswith("http") else f"http://{headers.get('host', '')}{target}"
        host = headers.get('host', '').split(':')[0]

        action, category, reason, src = self.filter.evaluate_url(url)

        if action == "REDIRECT_YOUTUBE":
            # Launch clean player
            self.youtube.play_video(url)
            html = f"<html><body style='background:#0f172a;color:white;text-align:center;padding:50px;'><h2>تم تحويل الفيديو للمشغل الآمن النظيف بدون إعلانات ✅</h2></body></html>"
            resp = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {len(html.encode('utf-8'))}\r\n\r\n{html}"
            client_writer.write(resp.encode('utf-8'))
            await client_writer.drain()
            client_writer.close()
            return

        if action in ['BLOCK', 'BEDTIME', 'TIME_EXPIRED']:
            html = BLOCKED_HTML_TEMPLATE.format(domain=host, url=url, reason=reason)
            resp = f"HTTP/1.1 403 Forbidden\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {len(html.encode('utf-8'))}\r\n\r\n{html}"
            client_writer.write(resp.encode('utf-8'))
            await client_writer.drain()
            client_writer.close()
            self.db.log_activity(host, url, category, action, reason)
            return

        # Forward HTTP request
        try:
            port = 80
            remote_reader, remote_writer = await asyncio.open_connection(host, port)
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
        """Handles internal form actions for exception requests and code verification"""
        content_len = int(headers.get('content-length', 0))
        body = b""
        if content_len > 0:
            body = await reader.read(content_len)
        form_data = urllib.parse.parse_qs(body.decode('utf-8', errors='ignore'))

        if "/request_exception" in target:
            domain = form_data.get('domain', [''])[0]
            url = form_data.get('url', [''])[0]
            reason = form_data.get('reason', [''])[0]
            success, msg, perm_code, temp_code = self.approvals.create_and_send_request(domain, url, reason)
            
            html = f"""<!DOCTYPE html><html lang='ar' dir='rtl'><head><meta charset='UTF-8'><title>تم إرسال الطلب</title>
            <body style='background:#0f172a;color:white;font-family:sans-serif;text-align:center;padding:50px;'>
            <div style='background:#1e293b;max-width:500px;margin:0 auto;padding:30px;border-radius:12px;'>
            <h2>📨 تم إرسال طلبك لوالدك بنجاح</h2>
            <p>تم إرسال تفاصيل طلبك لبريد ولي الأمر. اطلب منه رمز الموافقة عند قبوله.</p>
            <a href='javascript:history.back()' style='color:#38bdf8;'>الرجوع</a>
            </div></body></html>"""
            resp = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {len(html.encode('utf-8'))}\r\n\r\n{html}"
            writer.write(resp.encode('utf-8'))
            await writer.drain()
            writer.close()
            return

        if "/verify_code" in target:
            code = form_data.get('code', [''])[0]
            success, msg, typ, domain = self.db.verify_and_apply_code(code)
            color = "#10b981" if success else "#f43f5e"
            html = f"""<!DOCTYPE html><html lang='ar' dir='rtl'><head><meta charset='UTF-8'><title>التحقق من الرمز</title>
            <body style='background:#0f172a;color:white;font-family:sans-serif;text-align:center;padding:50px;'>
            <div style='background:#1e293b;max-width:500px;margin:0 auto;padding:30px;border-radius:12px;'>
            <h2 style='color:{color};'>{msg}</h2>
            <p><a href='http://{domain or ""}' style='color:#38bdf8;'>الانتقال للموقع الآن</a> | <a href='javascript:history.back()' style='color:#94a3b8;'>الرجوع</a></p>
            </div></body></html>"""
            resp = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {len(html.encode('utf-8'))}\r\n\r\n{html}"
            writer.write(resp.encode('utf-8'))
            await writer.drain()
            writer.close()
            return

        # Default internal status
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHaseen Local Proxy Online")
        await writer.drain()
        writer.close()

if __name__ == "__main__":
    proxy = LocalProxyServer()
    asyncio.run(proxy.start())
