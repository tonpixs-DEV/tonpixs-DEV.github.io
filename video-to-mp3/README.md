# Video to MP3

## หน้าเว็บ (`index.html`)
ลากไฟล์วิดีโอมาวาง แปลงเป็น MP3 ในเบราว์เซอร์ ไม่อัปโหลดไฟล์ไปที่ไหน
เหมาะกับคลิปราว 1 ชั่วโมงหรือสั้นกว่า

เปิดใช้ที่ `https://tonpixs-dev.github.io/video-to-mp3/`

## ลิงก์ YouTube (`youtube_to_mp3.py`)
GitHub Pages ดึงวิดีโอจาก YouTube ไม่ได้ จึงใช้สคริปต์ Python รันบนเครื่องแทน
(ใช้กับวิดีโอที่คุณมีสิทธิ์ใช้งานเท่านั้น)

```
pip install -U yt-dlp
winget install Gyan.FFmpeg
python youtube_to_mp3.py "https://www.youtube.com/watch?v=XXXX" -o D:\mp3 -b 192
```
