#!/usr/bin/env python3
"""แปลงลิงก์ YouTube เป็น MP3 (รันบนเครื่องของคุณ)

ใช้กับวิดีโอที่คุณเป็นเจ้าของหรือมีสิทธิ์ใช้งานเท่านั้น

ติดตั้งครั้งแรก (Windows):
    pip install -U yt-dlp
    ติดตั้ง ffmpeg แล้วเพิ่มเข้า PATH (เช่น winget install Gyan.FFmpeg)

วิธีใช้:
    python youtube_to_mp3.py "https://www.youtube.com/watch?v=XXXX"
    python youtube_to_mp3.py URL1 URL2 -o D:\\mp3 -b 192
    python youtube_to_mp3.py -f links.txt        (ไฟล์ละ 1 ลิงก์)
"""
import argparse
import shutil
import sys


def main():
    p = argparse.ArgumentParser(description="YouTube -> MP3")
    p.add_argument("urls", nargs="*", help="ลิงก์ YouTube")
    p.add_argument("-f", "--file", help="ไฟล์ข้อความที่มีลิงก์บรรทัดละอัน")
    p.add_argument("-o", "--out", default="mp3_output", help="โฟลเดอร์ปลายทาง (ค่าเริ่มต้น mp3_output)")
    p.add_argument("-b", "--bitrate", default="192", help="kbps ของ mp3 (ค่าเริ่มต้น 192)")
    p.add_argument("--playlist", action="store_true", help="ดาวน์โหลดทั้ง playlist (ค่าเริ่มต้นเอาเฉพาะวิดีโอเดียว)")
    a = p.parse_args()

    urls = list(a.urls)
    if a.file:
        with open(a.file, encoding="utf-8") as fh:
            urls += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    if not urls:
        p.error("ใส่ลิงก์อย่างน้อย 1 อัน หรือใช้ -f links.txt")

    try:
        from yt_dlp import YoutubeDL
    except ImportError:
        sys.exit("ยังไม่ได้ติดตั้ง yt-dlp: pip install -U yt-dlp")
    if not shutil.which("ffmpeg"):
        sys.exit("ไม่พบ ffmpeg ใน PATH: ติดตั้งแล้วลองใหม่ (winget install Gyan.FFmpeg)")

    opts = {
        "format": "bestaudio/best",
        "outtmpl": a.out + "/%(title)s.%(ext)s",
        "noplaylist": not a.playlist,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": a.bitrate,
        }],
    }
    with YoutubeDL(opts) as ydl:
        code = ydl.download(urls)
    if code == 0:
        print("เสร็จแล้ว ไฟล์อยู่ที่โฟลเดอร์:", a.out)
    sys.exit(code)


if __name__ == "__main__":
    main()
