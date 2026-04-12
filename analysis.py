import os
import shutil
import yt_dlp
import whisper
import imageio_ffmpeg
from moviepy import VideoFileClip

# =====================================================================
# CHIÊU CUỐI: Tự động copy file FFmpeg ẩn ra thư mục hiện tại
# Windows sẽ luôn ưu tiên tìm file .exe ở ngay cạnh file code đang chạy.
# =====================================================================
ffmpeg_hidden_path = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_local_path = os.path.join(os.getcwd(), "ffmpeg.exe")

if not os.path.exists(ffmpeg_local_path):
    print("-> Đang tự động trích xuất FFmpeg ra thư mục làm việc...")
    shutil.copy(ffmpeg_hidden_path, ffmpeg_local_path)
# =====================================================================

VIDEO_URL = "https://www.tiktok.com/@subatriminh/video/7613700622910557460?_r=1&u_code=0&region=FR&mid=7613700681886616340&preview_pb=0&sharer_language=vi&_d=f2d65f91fl5e5g&share_item_id=7613700622910557460&source=h5_t"
VIDEO_FILE = "video.mp4"
AUDIO_FILE = "audio.mp3"

def download_tiktok_video(url):
    print("\n1. Downloading video with yt-dlp...")
    if os.path.exists(VIDEO_FILE):
        os.remove(VIDEO_FILE)
        
    ydl_opts = {
        'outtmpl': VIDEO_FILE,
        'format': 'best',
        'quiet': True,
        'no_warnings': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print("=> Video downloaded:", VIDEO_FILE)

def extract_audio():
    print("\n2. Extracting audio using moviepy...")
    if os.path.exists(AUDIO_FILE):
        os.remove(AUDIO_FILE)
        
    try:
        video_clip = VideoFileClip(VIDEO_FILE)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(AUDIO_FILE, logger=None)
        audio_clip.close()
        video_clip.close()
        print("=> Audio saved:", AUDIO_FILE)
    except Exception as e:
        print(f"Lỗi khi tách âm thanh: {e}")

def speech_to_text():
    print("\n3. Loading Whisper model & Transcribing...")
    model = whisper.load_model("base")
    
    # Whisper giờ đây sẽ thấy file ffmpeg.exe nằm ngay bên cạnh và không báo lỗi nữa!
    result = model.transcribe(AUDIO_FILE, language="vi")
    
    print("\n===== VIDEO TEXT =====")
    print(result["text"])
    
    return result["text"]

def main():
    download_tiktok_video(VIDEO_URL)
    extract_audio()
    text = speech_to_text()
    
    if text:
        with open("video_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("\n=> Text successfully saved to video_text.txt")
    else:
        print("\n=> Không trích xuất được văn bản nào từ video.")

if __name__ == "__main__":
    main()