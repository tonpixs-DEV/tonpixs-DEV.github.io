# API แปลงลิงก์ YouTube เป็น MP3 (สำหรับเปิดให้ลูกค้าใช้ผ่านหน้าเว็บ)

## Deploy (ตัวอย่าง Render / Railway / Fly.io / VPS ที่รัน Docker ได้)
1. สร้าง Web Service จาก repo นี้ เลือก root directory `video-to-mp3/api` และให้ใช้ `Dockerfile`
2. ตั้ง environment variable อย่างน้อย:
   - `ALLOWED_ORIGINS=https://tonpixs-dev.github.io`
   - (ไม่บังคับ) `MAX_SECONDS=900`, `MAX_JOBS=2`, `RATE_PER_HOUR=6`
3. Deploy เสร็จจะได้ URL เช่น `https://mp3-api.onrender.com` เช็กที่ `<URL>/health` ต้องตอบ `ok`
4. แก้ `video-to-mp3/config.js` ให้เป็น `window.MP3_API = "<URL>";` แล้ว push
   หน้าเว็บจะแสดงช่องวางลิงก์ YouTube ให้ทุกคนและเรียกเซิร์ฟเวอร์นี้

## ข้อควรรู้
- มีตัวจำกัด: ความยาวคลิป, งานพร้อมกัน, จำนวนครั้งต่อ IP ต่อชั่วโมง, อนุญาตเฉพาะโดเมนใน `ALLOWED_ORIGINS`
- YouTube อาจบล็อกเซิร์ฟเวอร์ใน data center ถ้าโหลดไม่ได้ ให้อัปเดต `yt-dlp` (rebuild image) หรือใส่ไฟล์ cookies ผ่าน `YT_COOKIES`
- แพ็กเกจฟรีของบางเจ้าจำกัดเวลาตอบ (timeout) และ RAM ถ้าคลิปยาวอาจไม่ผ่าน
- ผู้เปิดบริการรับผิดชอบเรื่องลิขสิทธิ์และข้อกำหนดของ YouTube เอง ควรให้ใช้กับวิดีโอที่ลูกค้ามีสิทธิ์เท่านั้น
