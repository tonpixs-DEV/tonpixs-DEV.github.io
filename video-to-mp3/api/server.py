#!/usr/bin/env python3
"""API แปลงลิงก์ YouTube เป็น MP3 สำหรับ deploy บนเซิร์ฟเวอร์ (ใช้แค่ stdlib + yt-dlp + ffmpeg)

GET /health
GET /convert?url=<ลิงก์ YouTube>&bitrate=128   -> audio/mpeg

ตั้งค่าด้วย environment variable:
  PORT              พอร์ต (ค่าเริ่มต้น 8000)
  ALLOWED_ORIGINS   โดเมนเว็บที่อนุญาต คั่นด้วยจุลภาค (ค่าเริ่มต้น https://tonpixs-dev.github.io)
  MAX_SECONDS       ความยาววิดีโอสูงสุดที่รับ (ค่าเริ่มต้น 900 = 15 นาที)
  MAX_JOBS          จำนวนงานที่ทำพร้อมกันได้ (ค่าเริ่มต้น 2)
  RATE_PER_HOUR     จำนวนครั้งต่อชั่วโมงต่อ IP (ค่าเริ่มต้น 6)
  TRUST_PROXY       ตั้งเป็น 1 ถ้าอยู่หลัง proxy/โหลดบาลานเซอร์ (อ่าน IP จาก X-Forwarded-For)
  YT_COOKIES        path ไฟล์ cookies.txt (ถ้า YouTube บล็อกเซิร์ฟเวอร์)
"""
import os
import shutil
import tempfile
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

PORT = int(os.environ.get("PORT", "8000"))
ORIGINS = {o.strip().rstrip("/") for o in os.environ.get("ALLOWED_ORIGINS", "https://tonpixs-dev.github.io").split(",") if o.strip()}
MAX_SECONDS = int(os.environ.get("MAX_SECONDS", "900"))
MAX_JOBS = int(os.environ.get("MAX_JOBS", "2"))
RATE_PER_HOUR = int(os.environ.get("RATE_PER_HOUR", "6"))
TRUST_PROXY = os.environ.get("TRUST_PROXY") == "1"
COOKIES = os.environ.get("YT_COOKIES")
BITRATES = {"96", "128", "192", "256", "320"}
YT_HOSTS = {"youtu.be", "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}

_slots = threading.BoundedSemaphore(MAX_JOBS)
_hits = defaultdict(deque)
_hits_lock = threading.Lock()


class ApiError(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code, self.msg = code, msg


def is_youtube(url):
    p = urlparse(url)
    return p.scheme in ("http", "https") and (p.hostname or "").lower() in YT_HOSTS


def rate_ok(ip, now=None):
    now = time.time() if now is None else now
    with _hits_lock:
        q = _hits[ip]
        while q and now - q[0] > 3600:
            q.popleft()
        if len(q) >= RATE_PER_HOUR:
            return False
        q.append(now)
        return True


def _base_opts():
    o = {"noplaylist": True, "quiet": True, "no_warnings": True}
    if COOKIES and os.path.exists(COOKIES):
        o["cookiefile"] = COOKIES
    return o


def probe(url):
    """คืนความยาว (วินาที) และชื่อ ก่อนโหลดจริง"""
    from yt_dlp import YoutubeDL
    with YoutubeDL(_base_opts()) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("is_live"):
        raise ApiError(400, "ไม่รองรับไลฟ์สด")
    return info.get("duration") or 0, info.get("title") or "audio"


def download_mp3(url, bitrate, out_dir):
    from yt_dlp import YoutubeDL
    o = _base_opts()
    o.update({
        "format": "bestaudio/best",
        "outtmpl": os.path.join(out_dir, "audio.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": bitrate}],
    })
    with YoutubeDL(o) as ydl:
        ydl.download([url])
    path = os.path.join(out_dir, "audio.mp3")
    if not os.path.exists(path):
        raise ApiError(500, "แปลงไม่สำเร็จ")
    return path


class Handler(BaseHTTPRequestHandler):
    server_version = "mp3api"

    def _origin_ok(self):
        o = (self.headers.get("Origin") or "").rstrip("/")
        return o if o in ORIGINS else None

    def _cors(self):
        o = self._origin_ok()
        if o:
            self.send_header("Access-Control-Allow-Origin", o)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Expose-Headers", "X-Title")

    def _text(self, code, msg):
        body = msg.encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _ip(self):
        if TRUST_PROXY:
            xff = self.headers.get("X-Forwarded-For", "")
            if xff:
                return xff.split(",")[0].strip()
        return self.client_address[0]

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/health", "/ping"):
            return self._text(200, "ok")
        if u.path != "/convert":
            return self._text(404, "not found")
        if not self._origin_ok():
            return self._text(403, "โดเมนนี้ไม่ได้รับอนุญาต")
        q = parse_qs(u.query)
        url = (q.get("url") or [""])[0].strip()
        bitrate = (q.get("bitrate") or ["128"])[0]
        if bitrate not in BITRATES:
            bitrate = "128"
        if not is_youtube(url):
            return self._text(400, "ลิงก์ต้องเป็น YouTube")
        if not rate_ok(self._ip()):
            return self._text(429, "ใช้งานบ่อยเกินไป ลองใหม่ภายหลัง")
        if not _slots.acquire(blocking=False):
            return self._text(503, "เซิร์ฟเวอร์กำลังทำงานเต็ม ลองใหม่อีกครั้งในอีกสักครู่")
        tmp = tempfile.mkdtemp(prefix="yt2mp3_")
        try:
            duration, title = probe(url)
            if duration > MAX_SECONDS:
                raise ApiError(413, "วิดีโอยาวเกินไป (รับไม่เกิน %d นาที)" % (MAX_SECONDS // 60))
            path = download_mp3(url, bitrate, tmp)
            size = os.path.getsize(path)
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(size))
            self.send_header("X-Title", quote(title))
            self.end_headers()
            with open(path, "rb") as fh:
                shutil.copyfileobj(fh, self.wfile)
        except ApiError as e:
            self._text(e.code, e.msg)
        except Exception as e:  # noqa: BLE001
            print("error:", repr(e)[:300], flush=True)
            try:
                self._text(502, "ดาวน์โหลดจาก YouTube ไม่สำเร็จ (ลิงก์ไม่ถูกต้อง ถูกจำกัด หรือ YouTube บล็อก)")
            except Exception:  # noqa: BLE001
                pass
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            _slots.release()

    def log_message(self, fmt, *args):
        print("%s %s" % (self._ip(), fmt % args), flush=True)


def main():
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("listening on :%d origins=%s max=%ds jobs=%d" % (PORT, sorted(ORIGINS), MAX_SECONDS, MAX_JOBS), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
