@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Video to MP3 helper
echo ===== Video to MP3 helper =====

set PY=
where py >nul 2>nul && set PY=py
if "%PY%"=="" where python >nul 2>nul && set PY=python
if "%PY%"=="" (
  echo [!] Python not found. Install from https://www.python.org/downloads/ ^(tick "Add Python to PATH"^) then run this file again.
  pause
  exit /b 1
)

if not exist youtube_to_mp3.py (
  echo Downloading youtube_to_mp3.py ...
  curl -L -o youtube_to_mp3.py https://raw.githubusercontent.com/tonpixs-DEV/tonpixs-DEV.github.io/main/video-to-mp3/youtube_to_mp3.py
  if errorlevel 1 (
    echo [!] Download failed. Put youtube_to_mp3.py in this folder and run again.
    pause
    exit /b 1
  )
)

echo Installing / updating yt-dlp ...
%PY% -m pip install -U yt-dlp
if errorlevel 1 (
  echo [!] pip install failed.
  pause
  exit /b 1
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo Installing ffmpeg ...
  winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
  echo.
  echo ffmpeg installed. CLOSE this window and double-click this file again.
  pause
  exit /b 0
)

echo.
echo Ready. Keep this window open, then paste the YouTube link on the web page.
%PY% youtube_to_mp3.py --serve
pause
