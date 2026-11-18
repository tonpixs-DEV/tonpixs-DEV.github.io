#!/usr/bin/env python3
"""แปลงลิงก์ YouTube เป็น MP3 (รันบนเครื่องของคุณ)

ใช้กับวิดีโอที่คุณเป็นเจ้าของหรือมีสิทธิ์ใช้งานเท่านั้น

ติดตั้งครั้งแรก (Windows):
    pip install -U yt-dlp
    ติดตั้ง ffmpeg แล้วเพิ่มเข้า PATH (เช่น winget install Gyan.FFmpeg)

โหมดที่ 1 - ใช้ผ่านหน้าเว็บ (ช่องวางลิงก์ในหน้า video-to-mp3):
    python youtube_to_mp3.py --serve
    แล้วเปิดหน้าเว็บ วางลิงก์ กด "แปลงลิงก์ YouTube" (ปล่อยหน้าต่างนี้เปิดไว้)

โหมดที่ 2 - ใช้ในบรรทัดคำสั่ง:
    python youtube_to_mp3.py "https://www.youtube.com/watch?v=XXXX"
    python youtube_to_mp3.py URL1 URL2 -o D:\\mp3 -b 192
    python youtube_to_mp3.py -f links.txt        (ไฟล์ละ 1 ลิงก์)
"""
import argparse
import glob
import os
import shutil
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

ALLOWED_ORIGINS = {"https://tonpixs-dev.github.io", "http://localhost", "http://127.0.0.1"}


def check_deps():
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        sys.exit("ยังไม่ได้ติดตั้ง yt-dlp: pip install -U yt-dlp")
    if not shutil.which("ffmpeg"):
        sys.exit("ไม่พบ ffmpeg ใน PATH: ติดตั้งแล้วลองใหม่ (winget install Gyan.FFmpeg)")


def make_opts(out_dir, bitrate, playlist=False):
    return {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
        "noplaylist": not playlist,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": str(bitrate),
        }],
    }


def is_youtube(url):
    host = (urlparse(url).hostname or "").lower()
    return host in {"youtu.be", "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS or origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:"):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Expose-Headers", "X-Title")

    def _text(self, code, msg):
        body = msg.encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/ping":
            return self._text(200, "ok")
        if u.path != "/convert":
            return self._text(404, "not found")
        q = parse_qs(u.query)
        url = (q.get("url") or [""])[0]
        bitrate = (q.get("bitrate") or ["192"])[0]
        if not is_youtube(url):
            return self._text(400, "ลิงก์ต้องเป็น YouTube")
        if bitrate not in {"96", "128", "192", "256", "320"}:
            bitrate = "192"
        from yt_dlp import YoutubeDL
        tmp = tempfile.mkdtemp(prefix="yt2mp3_")
        try:
            with YoutubeDL(make_opts(tmp, bitrate)) as ydl:
                ydl.download([url])
            files = glob.glob(os.path.join(tmp, "*.mp3"))
            if not files:
                return self._text(500, "แปลงไม่สำเร็จ (ไม่พบไฟล์ mp3)")
            path = files[0]
            title = os.path.splitext(os.path.basename(path))[0]
            size = os.path.getsize(path)
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(size))
            self.send_header("X-Title", quote(title))
            self.end_headers()
            with open(path, "rb") as fh:
                shutil.copyfileobj(fh, self.wfile)
        except Exception as e:  # noqa: BLE001
            try:
                self._text(500, "ผิดพลาด: " + str(e)[:300])
            except Exception:  # noqa: BLE001
                pass
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.address_string(), fmt % args))


def serve(port):
    check_deps()
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("พร้อมใช้งานที่ http://127.0.0.1:%d  (เปิดหน้าเว็บแล้ววางลิงก์ได้เลย, กด Ctrl+C เพื่อหยุด)" % port)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nหยุดแล้ว")


def main():
    p = argparse.ArgumentParser(description="YouTube -> MP3")
    p.add_argument("urls", nargs="*", help="ลิงก์ YouTube")
    p.add_argument("-f", "--file", help="ไฟล์ข้อความที่มีลิงก์บรรทัดละอัน")
    p.add_argument("-o", "--out", default="mp3_output", help="โฟลเดอร์ปลายทาง (ค่าเริ่มต้น mp3_output)")
    p.add_argument("-b", "--bitrate", default="192", help="kbps ของ mp3 (ค่าเริ่มต้น 192)")
    p.add_argument("--playlist", action="store_true", help="ดาวน์โหลดทั้ง playlist (ค่าเริ่มต้นเอาเฉพาะวิดีโอเดียว)")
    p.add_argument("--serve", action="store_true", help="เปิดเซิร์ฟเวอร์ในเครื่องให้หน้าเว็บเรียกใช้")
    p.add_argument("--port", type=int, default=8787, help="พอร์ตของ --serve (ค่าเริ่มต้น 8787)")
    a = p.parse_args()

    if a.serve:
        return serve(a.port)

    urls = list(a.urls)
    if a.file:
        with open(a.file, encoding="utf-8") as fh:
            urls += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    if not urls:
        p.error("ใส่ลิงก์อย่างน้อย 1 อัน, ใช้ -f links.txt หรือใช้ --serve")

    check_deps()
    from yt_dlp import YoutubeDL
    with YoutubeDL(make_opts(a.out, a.bitrate, a.playlist)) as ydl:
        code = ydl.download(urls)
    if code == 0:
        print("เสร็จแล้ว ไฟล์อยู่ที่โฟลเดอร์:", a.out)
    sys.exit(code)


if __name__ == "__main__":
    main()
