# Video to MP3

## หน้าเว็บ (`index.html`)
ลากไฟล์วิดีโอมาวาง แปลงเป็น MP3 ในเบราว์เซอร์ ไม่อัปโหลดไฟล์ไปที่ไหน
เหมาะกับคลิปราว 1 ชั่วโมงหรือสั้นกว่า

เปิดใช้ที่ `https://tonpixs-dev.github.io/video-to-mp3/`

## ลิงก์ YouTube
GitHub Pages ดึงวิดีโอจาก YouTube เองไม่ได้ จึงมีโปรแกรมช่วย `youtube_to_mp3.py` รันบนเครื่องคุณ
(ใช้กับวิดีโอที่คุณมีสิทธิ์ใช้งานเท่านั้น)

ติดตั้งครั้งเดียว:
```
pip install -U yt-dlp
winget install Gyan.FFmpeg
```

ใช้ผ่านหน้าเว็บ: เปิดโปรแกรมช่วยค้างไว้ แล้ววางลิงก์ในช่อง "วางลิงก์ YouTube" บนหน้าเว็บ
```
python youtube_to_mp3.py --serve
```

ใช้ในบรรทัดคำสั่งโดยตรง:
```
python youtube_to_mp3.py "https://www.youtube.com/watch?v=XXXX" -o D:\mp3 -b 192
```
