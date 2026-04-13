import sys
import json
import os
import time
import webbrowser
import random 
import re 
import sqlite3
import shutil
import requests
import urllib.parse 
import subprocess 
import platform 

if platform.system() == "Windows":
    import winreg

# --- CÁC THƯ VIỆN XỬ LÝ MEDIA & API TIKTOK/GEMINI ---
from apify_client import ApifyClient
import yt_dlp
import imageio_ffmpeg
from moviepy import VideoFileClip
from google import genai
from google.genai import types 
from PIL import Image

from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox, 
                             QMessageBox, QTimeEdit, QListWidget, QAbstractItemView,
                             QListWidgetItem, QDialog, QSystemTrayIcon, QMenu, QStyle,
                             QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QTabWidget,
                             QInputDialog, QRadioButton, QButtonGroup, QFileDialog, QGraphicsDropShadowEffect,
                             QComboBox, QCheckBox, QSlider) 
from PyQt6.QtCore import QTime, Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt6.QtGui import QAction, QIcon, QFont, QColor, QPixmap 
from datetime import datetime

# =====================================================================
# TỰ ĐỘNG CẤU HÌNH FFMPEG CHO MOVIEPY KHỎI LỖI TRÊN WINDOWS
# =====================================================================
ffmpeg_hidden_path = imageio_ffmpeg.get_ffmpeg_exe()
ext = ".exe" if platform.system() == "Windows" else ""
ffmpeg_local_path = os.path.join(os.getcwd(), f"ffmpeg{ext}")

if not os.path.exists(ffmpeg_local_path):
    try:
        shutil.copy(ffmpeg_hidden_path, ffmpeg_local_path)
        if platform.system() != "Windows":
            os.chmod(ffmpeg_local_path, 0o755)
    except Exception:
        pass

DB_FILE = 'autopost_database.db' 
ADMIN_PASSWORD = "admin" 

# ==========================================
# 🎨 GLOBAL STYLESHEET (Giao diện Modern)
# ==========================================
MODERN_STYLE = (
    "QWidget { font-family: 'Segoe UI', -apple-system, sans-serif; font-size: 14px; color: #334155; }\n"
    "AutoPostApp { background-color: #f8fafc; }\n"
    "QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 8px; background: #ffffff; }\n"
    "QTabBar::tab { background: #f1f5f9; border: 1px solid #e2e8f0; border-bottom-color: #e2e8f0; border-top-left-radius: 8px; border-top-right-radius: 8px; padding: 12px 24px; margin-right: 4px; font-weight: 600; font-size: 14px; color: #64748b; }\n"
    "QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; color: #2563eb; }\n"
    "QTabBar::tab:hover:!selected { background: #e2e8f0; color: #0f172a; }\n"
    "QGroupBox { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 15px; padding-top: 20px; font-weight: bold; }\n"
    "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 15px; padding: 0 5px; color: #1e293b; font-size: 15px; background-color: transparent; }\n"
    "QLineEdit, QTextEdit, QTimeEdit, QSpinBox, QComboBox { border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; background-color: #ffffff; color: #0f172a; font-size: 14px; min-height: 24px; }\n"
    "QLineEdit:focus, QTextEdit:focus, QTimeEdit:focus, QSpinBox:focus, QComboBox:focus { border: 1px solid #3b82f6; }\n"
    "QPushButton { border-radius: 6px; padding: 10px 16px; font-weight: bold; border: none; font-size: 14px; }\n"
    "QPushButton:hover { opacity: 0.9; }\n"
    "QPushButton:disabled { background-color: #cbd5e1; color: #94a3b8; }\n"
    "QTableWidget { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; gridline-color: #f1f5f9; selection-background-color: #eff6ff; selection-color: #1e40af; }\n"
    "QHeaderView::section { background-color: #f8fafc; padding: 10px; border: none; border-bottom: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; font-weight: bold; color: #475569; }\n"
    "QRadioButton { font-weight: bold; color: #1e293b; padding: 12px 15px; border: 2px solid #e2e8f0; border-radius: 8px; background-color: #f8fafc; }\n"
    "QRadioButton:hover { border-color: #cbd5e1; background-color: #f1f5f9; }\n"
    "QRadioButton:checked { border-color: #3b82f6; background-color: #eff6ff; color: #1d4ed8; }\n"
    "QRadioButton::indicator { width: 18px; height: 18px; }\n"
    "QCheckBox { font-weight: bold; color: #1e293b; padding: 5px; }\n"
    "QFrame#MediaFrame { background-color: #0f172a; border-radius: 8px; } QFrame#MediaFrame QLabel { color: #f1f5f9; font-weight: bold; }\n"
)

# ==========================================
# 🌟 CUSTOM TOAST NOTIFICATION
# ==========================================
class CustomToast(QFrame):
    def __init__(self, parent, title, message, is_error=False):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        bg_color = "#fef2f2" if is_error else "#f0fdf4"
        border_color = "#ef4444" if is_error else "#22c55e"
        text_color = "#991b1b" if is_error else "#166534"
        title_color = "#7f1d1d" if is_error else "#14532d"
        icon_text = "❌" if is_error else "✅"

        self.setStyleSheet(f"""
            QFrame#ToastFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 10px;
            }}
        """)

        self.frame = QFrame(self)
        self.frame.setObjectName("ToastFrame")
        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(15, 15, 15, 15)

        title_lbl = QLabel(f"{icon_text}  {title}")
        title_lbl.setStyleSheet(f"font-weight: bold; font-size: 16px; color: {title_color};")
        layout.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(f"font-size: 14px; color: {text_color}; margin-top: 5px;")
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(self.frame)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.frame.setGraphicsEffect(shadow)

        self.adjustSize()
        
        if parent:
            parent_rect = parent.geometry()
            start_x = parent_rect.width() - self.width() - 20
            start_y = 40
            self.move(start_x, start_y - 50) 

            self.anim = QPropertyAnimation(self, b"pos")
            self.anim.setDuration(400)
            self.anim.setStartValue(QPoint(start_x, start_y - 30))
            self.anim.setEndValue(QPoint(start_x, start_y))
            self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
            self.anim.start()

        self.show()
        self.raise_()
        QTimer.singleShot(3500, self.close)


# ==========================================
# ⚙️ THREADS
# ==========================================
class AutoPostWorker(QThread):
    time_tick = pyqtSignal(str) 
    def __init__(self):
        super().__init__()
        self.is_running = True
    def run(self):
        while self.is_running:
            now_str = datetime.now().strftime("%H:%M")
            self.time_tick.emit(now_str)
            time.sleep(1) 
    def stop(self):
        self.is_running = False
        self.quit()
        self.wait()

class SilentLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

class ApiPipelineWorker(QThread):
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str, list) 

    # [MỚI] Nhận thêm các biến cấu hình Video (Veo 3.1)
    def __init__(self, apify_token, gemini_key, ai_model, count, custom_trend="", target_topics="", custom_prompt="", max_videos=1, doc_file_path="", ignore_keywords="", word_limit=0, gen_image=False, logo_path="", logo_pos="", logo_opacity=100, logo_scale=20, gen_video=False, veo_model="veo-3.1-generate-preview", veo_aspect="16:9", veo_res="720p", veo_duration="8", veo_negative=""):
        super().__init__()
        self.apify_token = apify_token 
        self.gemini_key = gemini_key
        self.ai_model = ai_model
        self.count = count
        self.custom_trend = custom_trend 
        self.target_topics = target_topics 
        self.custom_prompt = custom_prompt 
        self.max_videos = max_videos
        self.doc_file_path = doc_file_path
        self.ignore_keywords = ignore_keywords
        self.word_limit = word_limit
        
        self.gen_image = gen_image
        self.logo_path = logo_path
        self.logo_pos = logo_pos
        self.logo_opacity = logo_opacity
        self.logo_scale = logo_scale
        
        self.gen_video = gen_video
        self.veo_model = veo_model
        self.veo_aspect = veo_aspect
        self.veo_res = veo_res
        self.veo_duration = veo_duration
        self.veo_negative = veo_negative
        
        self.temp_video = "temp_video.mp4"
        self.temp_audio = "temp_audio.mp3"

    def run(self):
        try:
            genai_client = genai.Client(api_key=self.gemini_key)
            
            total_in_tokens = 0
            total_out_tokens = 0

            # 1. ĐỌC FILE TÀI LIỆU SẢN PHẨM
            doc_context = ""
            if self.doc_file_path and os.path.exists(self.doc_file_path):
                try:
                    ext = os.path.splitext(self.doc_file_path)[1].lower()
                    doc_content = ""
                    
                    if ext == '.docx':
                        try:
                            import docx
                            doc = docx.Document(self.doc_file_path)
                            doc_content = "\n".join([para.text for para in doc.paragraphs])
                        except ImportError:
                            self.status_signal.emit("❌ Lỗi: Bạn chưa cài thư viện đọc file Word. Hãy gõ lệnh: pip install python-docx")
                            raise Exception("Thiếu thư viện python-docx")
                    elif ext in ['.txt', '.md', '.csv']:
                        with open(self.doc_file_path, 'r', encoding='utf-8') as f:
                            doc_content = f.read()
                    else:
                        with open(self.doc_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            doc_content = f.read()

                    if doc_content.strip():
                        doc_context = f"\n--- THÔNG TIN TÀI LIỆU SẢN PHẨM BỔ SUNG (BẮT BUỘC SỬ DỤNG) ---\n{doc_content}\n------------------------------------------\n\n"
                        self.status_signal.emit(f"-> Đã nạp thành công file tài liệu: {os.path.basename(self.doc_file_path)}")
                except Exception as e:
                    self.status_signal.emit(f"⚠️ Không thể đọc file tài liệu: {e}")

            # 2. CÀO VIDEO TIKTOK
            buffer_limit = self.max_videos 
            self.status_signal.emit(f"B1: [Apify] Đang tìm kiếm {buffer_limit} video TikTok...")
            client = ApifyClient(self.apify_token)
            search_keyword = self.custom_trend if self.custom_trend else "viral"
                    
            run_input = {
                "trendType": "videos",
                "maxItems": buffer_limit, 
                "maxResults": buffer_limit,       
                "resultsPerPage": buffer_limit,   
                "limit": buffer_limit,            
                "countryCode": "VN",
                "hashtagPeriod": "7",
                "industryId": "",
                "showOnlyNew": False,
                "videoCountryCode": "VN",
                "videoPeriod": "7",
                "videoSortBy": "vv",
                "creatorCountryCode": "VN",
                "creatorAudienceCountry": "",
                "creatorSortBy": "follower",
                "proxyConfiguration": { "useApifyProxy": True },
            }

            run = client.actor("GULLsEZsAD69QFACQ").call(run_input=run_input)
            videos_data = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                v_link = item.get("TikTok URL_video", "")
                if v_link:
                    author_info = item.get("author", {})
                    creator = author_info.get("nickname", "Không xác định") if isinstance(author_info, dict) else "Không xác định"
                    videos_data.append({
                        "link": v_link,
                        "desc": item.get("Title_video", "Không có mô tả"),
                        "creator": creator
                    })
                if len(videos_data) >= buffer_limit:
                    break
                
            if not videos_data:
                raise Exception("Không tìm thấy video TikTok nào cho từ khóa này!")
                
            self.status_signal.emit(f"B1 Xong: Đã cào được {len(videos_data)} link. Bắt đầu lọc và tải...")
            
            # 3. TẢI VÀ DÙNG GEMINI ĐỂ NGHE TỪNG VIDEO
            combined_script = ""
            successful_count = 0 
            
            for idx, video in enumerate(videos_data, 1):
                if successful_count >= self.max_videos:
                    break
                    
                self.status_signal.emit(f"B2: [yt-dlp] Đang tải video {idx}/{len(videos_data)}...")
                if os.path.exists(self.temp_video): os.remove(self.temp_video)
                
                ydl_opts = {
                    'outtmpl': self.temp_video, 
                    'format': 'best', 
                    'quiet': True, 
                    'no_warnings': True,
                    'logger': SilentLogger(),
                    'nopart': True,
                    'cookiefile': 'cookies.txt'
                }
                
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl: 
                        ydl.download([video["link"]])
                except Exception as e:
                    self.status_signal.emit(f"⚠️ Bỏ qua video {idx} due to error: {str(e)}")
                    continue

                if not os.path.exists(self.temp_video) or os.path.getsize(self.temp_video) == 0:
                    self.status_signal.emit(f"⚠️ Bỏ qua video {idx} (File video bị rỗng)")
                    continue

                self.status_signal.emit(f"B3: [MoviePy] Tách âm thanh video {successful_count + 1}/{self.max_videos}...")
                if os.path.exists(self.temp_audio): os.remove(self.temp_audio)
                
                try:
                    video_clip = VideoFileClip(self.temp_video)
                    audio_clip = video_clip.audio
                    audio_clip.write_audiofile(self.temp_audio, logger=None)
                    audio_clip.close()
                    video_clip.close()
                except Exception as e:
                    self.status_signal.emit(f"⚠️ Bỏ qua video {idx} do lỗi trích xuất âm thanh: {e}")
                    continue

                self.status_signal.emit(f"B4: [{self.ai_model}] AI đang nghe bóc băng video {successful_count + 1}/{self.max_videos}...")
                try:
                    audio_file = genai_client.files.upload(file=self.temp_audio)
                    transcribe_response = genai_client.models.generate_content(
                        model=self.ai_model, 
                        contents=[audio_file, "Hãy nghe và gõ lại chính xác lời thoại trong đoạn âm thanh này thành văn bản. Chỉ trả về lời thoại, không giải thích gì thêm. Nếu không có tiếng người, hãy nói 'Không có lời thoại'."],
                    )
                    transcribed_text = transcribe_response.text.strip()
                    
                    if getattr(transcribe_response, 'usage_metadata', None):
                        total_in_tokens += getattr(transcribe_response.usage_metadata, 'prompt_token_count', 0)
                        total_out_tokens += getattr(transcribe_response.usage_metadata, 'candidates_token_count', 0)

                except Exception as e:
                    transcribed_text = f"(Không thể nhận diện giọng nói: {str(e)})"
                
                combined_script += f"--- VIDEO SỐ {successful_count + 1} ---\n"
                combined_script += f"- Tác giả: {video['creator']}\n"
                combined_script += f"- Mô tả gốc: {video['desc']}\n"
                combined_script += f"- Lời thoại/Kịch bản: {transcribed_text}\n\n"
                
                successful_count += 1

            if os.path.exists(self.temp_video): os.remove(self.temp_video)
            if os.path.exists(self.temp_audio): os.remove(self.temp_audio)

            if successful_count == 0:
                raise Exception("Trích xuất thất bại, tất cả video tìm được đều bị TikTok chặn!")

            self.status_signal.emit(f"B5: [{self.ai_model}] Phân tích ngữ cảnh & Viết bài Facebook...")
            
            prompt = (
                "Bạn là một chuyên gia Marketing và sáng tạo nội dung Facebook chuyên nghiệp.\n"
                f"Tôi vừa cào và phân tích {successful_count} video TikTok. Dưới đây là dữ liệu gốc từ các video:\n\n"
                f"{combined_script}"
                f"{doc_context}" 
                f"Dựa vào toàn bộ thông tin tổng hợp trên, hãy chắt lọc các ý hay nhất để sáng tạo ra {self.count} bài đăng Facebook khác nhau (các biến thể).\n\n"
            )

            if self.target_topics:
                prompt += f"**🎯 CHỦ ĐỀ / NGÁNH HÀNG MỤC TIÊU CỦA PAGE:** Kênh của tôi tập trung vào chủ đề: [{self.target_topics}]. Hãy chắc chắn rằng nội dung bạn viết ra được tinh chỉnh, bẻ lái và liên hệ khéo léo để phù hợp với ngành hàng/chủ đề này (ngay cả khi video gốc không hoàn toàn liên quan).\n\n"

            if self.ignore_keywords:
                prompt += f"**⚠️ YÊU CẦU LOẠI TRỪ CẤM KỴ:** Dưới đây là nội dung/từ khóa BỊ CẤM. Bạn phải đối chiếu với kịch bản video và TUYỆT ĐỐI KHÔNG SỬ DỤNG, KHÔNG NHẮC ĐẾN, LOẠI BỎ HOÀN TOÀN các ý tưởng, câu văn, hay từ khóa nào có trong đoạn này khỏi bài viết của bạn:\n[{self.ignore_keywords}]\n\n"

            if self.custom_prompt:
                prompt += f"**💡 YÊU CẦU SÁNG TẠO TỪ NGƯỜI DÙNG:** {self.custom_prompt}\n\n"

            word_limit_text = f"Mỗi bài viết giới hạn TỐI ĐA {self.word_limit} từ. " if self.word_limit > 0 else ""

            prompt += (
                "Yêu cầu Định dạng Đầu ra:\n"
                f"- {word_limit_text}Văn phong cuốn hút, bắt trend, chuẩn để đăng Facebook Fanpage.\n"
                "- Bắt buộc dùng Emoji và gắn Hashtag liên quan ở cuối bài.\n"
                "- KHÔNG kèm theo tiêu đề như 'Biến thể 1', 'Bài 1'. CHỈ TRẢ VỀ nội dung bài viết.\n"
                f"- PHÂN TÁCH các bài viết bằng đúng chuỗi ký tự này: |||\n"
                "Ví dụ:\nNội dung bài viết 1\n|||\nNội dung bài viết 2\n|||\nNội dung bài viết 3\n"
            )

            response = genai_client.models.generate_content(
                model=self.ai_model, 
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.8
                ),
            )

            if getattr(response, 'usage_metadata', None):
                total_in_tokens += getattr(response.usage_metadata, 'prompt_token_count', 0)
                total_out_tokens += getattr(response.usage_metadata, 'candidates_token_count', 0)

            raw_text = response.text.strip()
            generated_contents = [text.strip() for text in raw_text.split("|||") if text.strip()]
            
            if len(generated_contents) > self.count:
                generated_contents = generated_contents[:self.count]
                
            self.status_signal.emit(f"B5 Xong: [{self.ai_model}] Đã chắp bút thành công!")
            
            final_posts = []
            
            for idx, text_content in enumerate(generated_contents):
                image_save_path = ""
                video_save_path = ""
                
                # --- [MỚI] TẠO VIDEO BẰNG VEO 3.1 ---
                if self.gen_video:
                    self.status_signal.emit(f"🎬 B6: [Veo 3.1] Đang render Video cho bài số {idx + 1} (Mất khoảng 2-5 phút)...")
                    try:
                        # Dùng Gemini tóm tắt bài viết thành kịch bản Video (prompt tiếng Anh)
                        summary_prompt = f"Write a highly detailed, cinematic video generation prompt in English for a Facebook post about: {search_keyword}. Context: {text_content[:200]}. Do not include text, typography or dialogue in the video prompt. Focus purely on visual descriptions."
                        veo_prompt_resp = genai_client.models.generate_content(model="gemini-2.5-flash", contents=summary_prompt)
                        veo_prompt = veo_prompt_resp.text.strip()
                        
                        # Chèn nội dung cấm (Negative Prompt) vào thẳng Text Prompt
                        if self.veo_negative:
                            veo_prompt += f"\n\nNegative prompt: {self.veo_negative}"
                            
                        # Cấu hình video linh hoạt qua Dictionary để tương thích với SDK
                        veo_config = {
                            "aspect_ratio": self.veo_aspect,
                            "resolution": self.veo_res,
                            "durationSeconds": self.veo_duration
                        }
                        
                        operation = genai_client.models.generate_videos(
                            model=self.veo_model,
                            prompt=veo_prompt,
                            config=veo_config
                        )
                        
                        # Polling chờ Video (Không làm đơ ứng dụng vì đang chạy ở Thread phụ)
                        while not operation.done:
                            self.status_signal.emit(f"-> [Veo 3.1] Đang render Video bài {idx + 1}... Vui lòng đợi...")
                            time.sleep(10)
                            operation = genai_client.operations.get(operation)
                            
                        generated_video = operation.response.generated_videos[0]
                        os.makedirs("video", exist_ok=True)
                        video_save_path = f"video/ai_video_{int(time.time())}_{idx}.mp4"
                        
                        # Tải và lưu Video
                        genai_client.files.download(file=generated_video.video)
                        generated_video.video.save(video_save_path)
                        self.status_signal.emit(f"✅ Đã render xong Video: {video_save_path}")
                        
                    except Exception as vid_err:
                        self.status_signal.emit(f"⚠️ Lỗi tạo Video Veo 3.1: {str(vid_err)}")
                
                # --- TẠO ẢNH BẰNG GEMINI FLASH IMAGE (Nếu không chọn tạo Video) ---
                elif self.gen_image:
                    self.status_signal.emit(f"B6: [Gemini Image] Đang vẽ ảnh minh họa cho bài số {idx + 1}...")
                    try:
                        summary_prompt = f"Write a short, highly descriptive image generation prompt in English for a Facebook post about: {search_keyword}. Context: {text_content[:200]}. Do not include any text in the image itself. High quality, professional photography style."
                        img_prompt_resp = genai_client.models.generate_content(model="gemini-2.5-flash", contents=summary_prompt)
                        english_img_prompt = img_prompt_resp.text.strip()
                        
                        img_response = genai_client.models.generate_content(
                            model="gemini-2.5-flash-image",
                            contents=english_img_prompt
                        )
                        
                        image_saved = False
                        if getattr(img_response, "candidates", None):
                            for part in img_response.candidates[0].content.parts:
                                if hasattr(part, "inline_data") and part.inline_data:
                                    img_bytes = part.inline_data.data
                                    os.makedirs("image", exist_ok=True)
                                    image_save_path = f"image/ai_image_{int(time.time())}_{idx}.png"
                                    with open(image_save_path, "wb") as f:
                                         f.write(img_bytes)
                                    self.status_signal.emit(f"-> Đã vẽ xong ảnh: {image_save_path}")
                                    image_saved = True
                                    
                                    # XỬ LÝ ĐÓNG DẤU LOGO LÊN ẢNH
                                    if self.logo_path and os.path.exists(self.logo_path):
                                        self.status_signal.emit("-> Đang đóng dấu Logo (Watermark) lên ảnh...")
                                        try:
                                            base_img = Image.open(image_save_path).convert("RGBA")
                                            watermark = Image.open(self.logo_path).convert("RGBA")
                                            base_w, base_h = base_img.size
                                            wm_w, wm_h = watermark.size
                                            
                                            scale_factor = self.logo_scale / 100.0
                                            new_wm_w = int(base_w * scale_factor)
                                            new_wm_h = int(wm_h * (new_wm_w / wm_w))
                                            watermark = watermark.resize((new_wm_w, new_wm_h), Image.Resampling.LANCZOS)
                                            
                                            if self.logo_opacity < 100:
                                                alpha = watermark.split()[3]
                                                alpha = alpha.point(lambda p: p * (self.logo_opacity / 100.0))
                                                watermark.putalpha(alpha)
                                                
                                            padding = 20 
                                            pos_x, pos_y = 0, 0
                                            
                                            if self.logo_pos == "Góc trên Trái": pos_x, pos_y = padding, padding
                                            elif self.logo_pos == "Góc trên Phải": pos_x, pos_y = base_w - new_wm_w - padding, padding
                                            elif self.logo_pos == "Góc dưới Trái": pos_x, pos_y = padding, base_h - new_wm_h - padding
                                            elif self.logo_pos == "Góc dưới Phải": pos_x, pos_y = base_w - new_wm_w - padding, base_h - new_wm_h - padding
                                            elif self.logo_pos == "Chính giữa": pos_x, pos_y = (base_w - new_wm_w) // 2, (base_h - new_wm_h) // 2
                                                
                                            base_img.paste(watermark, (pos_x, pos_y), watermark)
                                            base_img.convert("RGB").save(image_save_path)
                                            self.status_signal.emit("-> Đóng dấu Logo thành công! ✅")
                                        except Exception as wm_err:
                                            self.status_signal.emit(f"⚠️ Lỗi đóng dấu Logo: {str(wm_err)}")
                                    break
                        if not image_saved:
                            raise Exception("Không tìm thấy dữ liệu ảnh (inline_data) trong phản hồi của API.")

                    except Exception as img_err:
                        self.status_signal.emit(f"⚠️ Không thể vẽ ảnh cho bài {idx + 1}: {str(img_err)}")
                        
                final_posts.append({
                    "content": text_content,
                    "image_path": image_save_path,
                    "video_path": video_save_path # [MỚI] Thêm video_path vào dữ liệu bài viết
                })
            
            total_tokens = total_in_tokens + total_out_tokens
            self.status_signal.emit(f"🪙 [Chi phí Token] Tổng sử dụng Text: {total_tokens:,} (Input: {total_in_tokens:,} | Output: {total_out_tokens:,})")
            
            display_title = f"Tổng hợp {successful_count} video từ '{search_keyword}'"
            self.finished_signal.emit(display_title, final_posts)

        except Exception as e:
            self.status_signal.emit(f"❌ Pipeline Lỗi: {str(e)}")
            self.finished_signal.emit("Lỗi Pipeline", [{"content": f"Lỗi: {str(e)}", "image_path": "", "video_path": ""}])


# ==========================================
# CÁC CLASS CỬA SỔ PHỤ
# ==========================================

# --- [MỚI] CỬA SỔ CÀI ĐẶT VIDEO (VEO 3.1) ---
class VideoSettingsDialog(QDialog):
    def __init__(self, model, aspect, res, duration, negative, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎥 Cài đặt Video AI (Veo 3.1)")
        self.resize(600, 350)
        self.setStyleSheet(MODERN_STYLE)

        layout = QVBoxLayout(self)

        row_model = QHBoxLayout()
        self.combo_model = QComboBox()
        self.combo_model.addItems(["veo-3.1-generate-preview", "veo-3.1-lite-preview"])
        self.combo_model.setCurrentText(model)
        row_model.addWidget(QLabel("Mô hình Video:"))
        row_model.addWidget(self.combo_model, stretch=1)
        layout.addLayout(row_model)

        row_format = QHBoxLayout()
        self.combo_aspect = QComboBox()
        self.combo_aspect.addItems(["16:9", "9:16"])
        self.combo_aspect.setCurrentText(aspect)
        row_format.addWidget(QLabel("Tỷ lệ khung hình:"))
        row_format.addWidget(self.combo_aspect, stretch=1)
        
        self.combo_res = QComboBox()
        self.combo_res.addItems(["720p", "1080p", "4k"])
        self.combo_res.setCurrentText(res)
        row_format.addWidget(QLabel("Độ phân giải:"))
        row_format.addWidget(self.combo_res, stretch=1)
        layout.addLayout(row_format)

        row_duration = QHBoxLayout()
        self.combo_duration = QComboBox()
        self.combo_duration.addItems(["4", "6", "8"])
        self.combo_duration.setCurrentText(duration)
        row_duration.addWidget(QLabel("Thời lượng (giây):"))
        row_duration.addWidget(self.combo_duration, stretch=1)
        lbl_hint = QLabel("<i>*Lưu ý: 1080p & 4k bắt buộc là 8s</i>")
        lbl_hint.setStyleSheet("color: #64748b;")
        row_duration.addWidget(lbl_hint)
        layout.addLayout(row_duration)

        layout.addWidget(QLabel("🚫 Nội dung cần tránh trong Video (Negative Prompt):"))
        self.input_negative = QTextEdit()
        self.input_negative.setPlainText(negative)
        self.input_negative.setPlaceholderText("Ghi bằng tiếng Anh. VD: text, urban background, man-made structures, dark...")
        layout.addWidget(self.input_negative)

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾 Lưu Cài Đặt Video")
        btn_save.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)

    def get_settings(self):
        return self.combo_model.currentText(), self.combo_aspect.currentText(), self.combo_res.currentText(), self.combo_duration.currentText(), self.input_negative.toPlainText().strip()


class LogoSettingsDialog(QDialog):
    def __init__(self, path, pos, opacity, scale, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🖼️ Cài đặt Logo / Watermark")
        self.resize(550, 300)
        self.setStyleSheet(MODERN_STYLE)

        layout = QVBoxLayout(self)

        row_file = QHBoxLayout()
        self.input_file = QLineEdit(path)
        self.input_file.setPlaceholderText("Đường dẫn file Logo (.png nền trong suốt)")
        btn_browse = QPushButton("📁 Chọn Logo")
        btn_browse.clicked.connect(self.browse_logo)
        btn_clear = QPushButton("❌")
        btn_clear.clicked.connect(self.input_file.clear)
        row_file.addWidget(QLabel("File Logo:"))
        row_file.addWidget(self.input_file, stretch=1)
        row_file.addWidget(btn_browse)
        row_file.addWidget(btn_clear)
        layout.addLayout(row_file)

        row_pos = QHBoxLayout()
        self.combo_pos = QComboBox()
        self.combo_pos.addItems(["Góc dưới Phải", "Góc dưới Trái", "Góc trên Phải", "Góc trên Trái", "Chính giữa"])
        self.combo_pos.setCurrentText(pos)
        row_pos.addWidget(QLabel("Vị trí đóng dấu:"))
        row_pos.addWidget(self.combo_pos, stretch=1)
        layout.addLayout(row_pos)

        row_scale = QHBoxLayout()
        self.spin_scale = QSpinBox()
        self.spin_scale.setRange(5, 100)
        self.spin_scale.setValue(int(scale))
        self.spin_scale.setSuffix(" % (so với ảnh gốc)")
        row_scale.addWidget(QLabel("Kích thước Logo:"))
        row_scale.addWidget(self.spin_scale, stretch=1)
        layout.addLayout(row_scale)

        row_opacity = QHBoxLayout()
        self.spin_opacity = QSpinBox()
        self.spin_opacity.setRange(10, 100)
        self.spin_opacity.setValue(int(opacity))
        self.spin_opacity.setSuffix(" % (Độ rõ nét)")
        row_opacity.addWidget(QLabel("Độ mờ (Opacity):"))
        row_opacity.addWidget(self.spin_opacity, stretch=1)
        layout.addLayout(row_opacity)

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾 Lưu Cài Đặt Logo")
        btn_save.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addStretch()
        layout.addLayout(btn_layout)

    def browse_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file Logo", "", "Images (*.png *.jpg *.jpeg);;All Files (*)")
        if file_path:
            self.input_file.setText(file_path)

    def get_settings(self):
        return self.input_file.text(), self.combo_pos.currentText(), self.spin_opacity.value(), self.spin_scale.value()


class DraftDetailDialog(QDialog):
    def __init__(self, draft_data, parent=None):
        super().__init__(parent)
        self.draft_data = draft_data
        self.setWindowTitle("🔍 Xem và Chỉnh sửa Content")
        self.resize(1000, 600) 
        self.setStyleSheet(MODERN_STYLE)
        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # --- [MỚI] Hiển thị UI cho Video hoặc Ảnh ---
        vid_path = self.draft_data.get("video_path", "")
        img_path = self.draft_data.get("image_path", "")
        
        if vid_path and os.path.exists(vid_path):
            media_frame = QFrame()
            media_frame.setObjectName("MediaFrame") 
            media_layout = QVBoxLayout(media_frame)
            media_layout.setContentsMargins(20, 20, 20, 20)
            media_layout.addWidget(QLabel('<b>🎬 Video minh họa (Veo 3.1):</b>'))
            
            lbl_vid = QLabel("Phát hiện Video đính kèm.\n(Không thể xem trước trực tiếp trong app)")
            lbl_vid.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_vid.setStyleSheet("color: #94a3b8; font-size: 16px; font-style: italic;")
            media_layout.addWidget(lbl_vid, stretch=1)
            
            btn_play = QPushButton("▶️ MỞ VIDEO BẰNG PHẦN MỀM MÁY TÍNH")
            btn_play.setStyleSheet("background-color: #ef4444; color: white; padding: 15px; font-weight: bold;")
            btn_play.clicked.connect(lambda: os.startfile(vid_path) if sys.platform == "win32" else subprocess.call(["open" if sys.platform == "darwin" else "xdg-open", vid_path]))
            media_layout.addWidget(btn_play)
            
            main_layout.addWidget(media_frame, stretch=4)
            
        elif img_path and os.path.exists(img_path):
            media_frame = QFrame()
            media_frame.setObjectName("MediaFrame") 
            media_layout = QVBoxLayout(media_frame)
            media_layout.setContentsMargins(10, 10, 10, 10)
            
            media_layout.addWidget(QLabel('<b>🖼️ Hình ảnh minh họa (Gemini Image):</b>'))
            self.image_label = QLabel()
            self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.image_label.setMinimumSize(450, 450)
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(450, 450, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.image_label.setText("⚠️ Không thể tải hình ảnh.")
            media_layout.addWidget(self.image_label, stretch=1)
            main_layout.addWidget(media_frame, stretch=4) 

        editor_layout = QVBoxLayout()
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel('<b>🕒 Thời gian:</b>'))
        time_edit = QLineEdit(self.draft_data.get("timestamp", "Không xác định"))
        time_edit.setReadOnly(True)
        time_edit.setStyleSheet("background-color: #f1f5f9; color: #64748b;")
        info_layout.addWidget(time_edit)

        info_layout.addWidget(QLabel('<b>📌 Nguồn/Trend:</b>'))
        self.kw_edit = QLineEdit(self.draft_data.get("keyword", ""))
        info_layout.addWidget(self.kw_edit)
        editor_layout.addLayout(info_layout)

        editor_layout.addWidget(QLabel('<b>📝 Nội dung bài viết (Có thể chỉnh sửa trực tiếp):</b>'))
        self.content_edit = QTextEdit()
        self.content_edit.setPlainText(self.draft_data.get("content", ""))
        self.content_edit.setStyleSheet("font-size: 15px; line-height: 1.6;")
        editor_layout.addWidget(self.content_edit)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton('💾 Lưu lại thay đổi')
        self.btn_save.setStyleSheet("background-color: #22c55e; color: white; min-height: 40px;")
        self.btn_save.clicked.connect(self.save_changes) 
        
        self.btn_cancel = QPushButton('Đóng (Không lưu)')
        self.btn_cancel.setStyleSheet("background-color: #e2e8f0; color: #334155; min-height: 40px;")
        self.btn_cancel.clicked.connect(self.reject) 
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save, stretch=1)
        editor_layout.addLayout(btn_layout)
        
        main_layout.addLayout(editor_layout, stretch=6)

    def save_changes(self):
        self.draft_data["keyword"] = self.kw_edit.text().strip()
        self.draft_data["content"] = self.content_edit.toPlainText().strip()
        self.accept()

class DraftsDialog(QDialog):
    draft_selected = pyqtSignal(dict) 
    post_now_requested = pyqtSignal(dict) 
    queue_requested = pyqtSignal(dict, str) 

    def __init__(self, drafts_list, parent=None):
        super().__init__(parent)
        self.drafts_list = drafts_list 
        self.setWindowTitle("📁 Kho Content đã tạo (Chờ xếp lịch)")
        self.resize(1100, 700) 
        self.setStyleSheet(MODERN_STYLE)
        self.is_all_checked = False
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm Content theo từ khóa, nội dung...")
        self.search_input.textChanged.connect(self.filter_drafts)
        
        self.btn_select_all = QPushButton("☑️ Chọn / Bỏ chọn tất cả")
        self.btn_select_all.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1;")
        self.btn_select_all.clicked.connect(self.toggle_select_all)

        top_layout.addWidget(self.search_input, stretch=1)
        top_layout.addWidget(self.btn_select_all)
        layout.addLayout(top_layout)

        self.table_widget = QTableWidget(len(self.drafts_list), 5) 
        self.table_widget.setHorizontalHeaderLabels(["Chọn", "Media (Ảnh/Video)", "Thời gian tạo", "Từ khóa / Nguồn", "Nội dung"])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) 
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.table_widget.verticalHeader().setDefaultSectionSize(80) 
        
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) 

        self.load_table_data()

        layout.addWidget(self.table_widget, stretch=1)
        
        hint_label = QLabel("💡 <b>Mẹo:</b> Tích vào ô vuông để chọn bài. Click đúp vào một dòng để <b>XEM CHI TIẾT/SỬA</b> bài viết.")
        hint_label.setStyleSheet("color: #64748b; margin-bottom: 5px;")
        layout.addWidget(hint_label)

        schedule_group = QGroupBox("⏳ Thiết lập lịch cho các bài ĐÃ TÍCH CHỌN (☑️)")
        schedule_layout = QHBoxLayout()

        self.draft_time_picker = QTimeEdit()
        self.draft_time_picker.setDisplayFormat("HH:mm")
        self.draft_time_picker.setTime(QTime.currentTime())
        self.draft_time_picker.setMinimumWidth(100)

        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(0, 1440) 
        self.spin_interval.setSuffix(" phút")
        self.spin_interval.setValue(15) 
        self.spin_interval.setMinimumWidth(100)

        self.btn_queue_selected = QPushButton("🚀 Chuyển vào Hàng đợi")
        self.btn_queue_selected.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold; padding: 10px 20px;")
        self.btn_queue_selected.clicked.connect(self.queue_selected_posts)

        schedule_layout.addWidget(QLabel("🕒 Bắt đầu đăng lúc:"))
        schedule_layout.addWidget(self.draft_time_picker)
        schedule_layout.addSpacing(20)
        schedule_layout.addWidget(QLabel("⏳ Giãn cách giữa các bài:"))
        schedule_layout.addWidget(self.spin_interval)
        schedule_layout.addStretch()
        schedule_layout.addWidget(self.btn_queue_selected)

        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)

        action_layout = QHBoxLayout()
        self.btn_post_now = QPushButton('⚡ Đăng Ngay bài ĐẦU TIÊN được tích chọn')
        self.btn_post_now.setStyleSheet("background-color: #3b82f6; color: white;")
        self.btn_post_now.clicked.connect(self.request_post_now)
        
        self.btn_delete = QPushButton('🗑️ Xóa các bài đã chọn')
        self.btn_delete.setStyleSheet("background-color: #ef4444; color: white;")
        self.btn_delete.clicked.connect(self.delete_draft)
        
        action_layout.addWidget(self.btn_post_now)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_delete)
        layout.addLayout(action_layout)
        
        self.setLayout(layout)

    def load_table_data(self):
            self.table_widget.setRowCount(0)
            for row, d in enumerate(self.drafts_list):
                self.table_widget.insertRow(row)
                
                chk_item = QTableWidgetItem()
                chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                chk_item.setCheckState(Qt.CheckState.Unchecked)
                chk_item.setData(Qt.ItemDataRole.UserRole, d) 
                
                vid_path = d.get('video_path', '')
                img_path = d.get('image_path', '')
                
                if vid_path and os.path.exists(vid_path):
                    lbl = QLabel("🎬 CÓ VIDEO")
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl.setStyleSheet("font-weight: bold; color: #ef4444;")
                    lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                    self.table_widget.setCellWidget(row, 1, lbl)
                elif img_path and os.path.exists(img_path):
                    img_label = QLabel()
                    pixmap = QPixmap(img_path).scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    img_label.setPixmap(pixmap)
                    img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    img_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                    self.table_widget.setCellWidget(row, 1, img_label)
                else:
                    no_img_item = QTableWidgetItem("Không có")
                    no_img_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    no_img_item.setForeground(QColor("#94a3b8"))
                    self.table_widget.setItem(row, 1, no_img_item)
                
                self.table_widget.setItem(row, 0, chk_item)
                self.table_widget.setItem(row, 2, QTableWidgetItem(d.get("timestamp", "Bản cũ")))
                self.table_widget.setItem(row, 3, QTableWidgetItem(d.get("keyword", "")))
                self.table_widget.setItem(row, 4, QTableWidgetItem(d.get("content", "").replace('\n', ' ')))

    def toggle_select_all(self):
        self.is_all_checked = not self.is_all_checked
        new_state = Qt.CheckState.Checked if self.is_all_checked else Qt.CheckState.Unchecked
        for row in range(self.table_widget.rowCount()):
            if not self.table_widget.isRowHidden(row): 
                self.table_widget.item(row, 0).setCheckState(new_state)

    def get_checked_rows(self):
        rows = []
        for row in range(self.table_widget.rowCount()):
            if self.table_widget.item(row, 0).checkState() == Qt.CheckState.Checked:
                rows.append(row)
        return rows

    def filter_drafts(self, text):
        search_term = text.lower()
        for row in range(self.table_widget.rowCount()):
            d_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if search_term in d_data.get("keyword", "").lower() or search_term in d_data.get("content", "").lower():
                self.table_widget.setRowHidden(row, False)
            else: 
                self.table_widget.setRowHidden(row, True)

    def on_item_double_clicked(self, item):
        row = item.row()
        draft_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = DraftDetailDialog(draft_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.table_widget.setItem(row, 3, QTableWidgetItem(draft_data.get("keyword", "")))
            self.table_widget.setItem(row, 4, QTableWidgetItem(draft_data.get("content", "").replace('\n', ' ')))
            if self.parent():
                self.parent().save_config()
                if hasattr(self.parent(), 'show_notification'):
                    self.parent().show_notification("Thành công! ✏️", "Đã cập nhật nội dung bài viết.")

    def queue_selected_posts(self):
        selected_rows = self.get_checked_rows()
        if not selected_rows:
            QMessageBox.warning(self, "Lỗi", "Vui lòng tích chọn (☑️) ít nhất 1 bài viết!")
            return

        start_time = self.draft_time_picker.time()
        interval_mins = self.spin_interval.value()
        queued_count = 0

        for i, row in enumerate(selected_rows):
            draft_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            post_time = start_time.addSecs(i * interval_mins * 60)
            self.queue_requested.emit(draft_data, post_time.toString("HH:mm"))
            queued_count += 1
            
        for row in reversed(selected_rows):
            draft_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if draft_data in self.drafts_list:
                self.drafts_list.remove(draft_data)
            self.table_widget.removeRow(row)

        if self.parent(): self.parent().save_config()
        self.is_all_checked = False
        
        if hasattr(self.parent(), 'show_notification'):
            self.parent().show_notification("Chuyển Hàng Đợi! 🚀", f"Đã đẩy {queued_count} bài vào Hàng đợi chờ đăng!")

    def request_post_now(self):
        selected_rows = self.get_checked_rows()
        if not selected_rows: return QMessageBox.warning(self, "Lỗi", "Vui lòng tích chọn bài cần đăng!")
        
        row = selected_rows[0] 
        draft_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if QMessageBox.question(self, 'Xác nhận', 'Đăng ngay bài viết này lên Facebook?') == QMessageBox.StandardButton.Yes:
            self.post_now_requested.emit(draft_data) 
            if draft_data in self.drafts_list: self.drafts_list.remove(draft_data)
            if self.parent(): self.parent().save_config()
            self.accept() 

    def delete_draft(self):
        selected_rows = self.get_checked_rows()
        if not selected_rows: return
        
        if QMessageBox.question(self, 'Xác nhận', f'Bạn có chắc muốn xóa vĩnh viễn {len(selected_rows)} bài này?') == QMessageBox.StandardButton.Yes:
            for row in reversed(selected_rows):
                draft_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
                if draft_data in self.drafts_list: self.drafts_list.remove(draft_data) 
                self.table_widget.removeRow(row)
            if self.parent(): self.parent().save_config()
            self.is_all_checked = False
            if hasattr(self.parent(), 'show_notification'):
                self.parent().show_notification("Đã xóa! 🗑️", f"Đã xóa {len(selected_rows)} bài viết khỏi Kho Content.")

class EditTimeDialog(QDialog):
    def __init__(self, current_time_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✏️ Sửa giờ đăng")
        self.resize(300, 150)
        self.setStyleSheet(MODERN_STYLE)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Nhập giờ mới cho bài viết này:</b>"))
        self.time_picker = QTimeEdit()
        self.time_picker.setDisplayFormat("HH:mm")
        parsed_time = QTime.fromString(current_time_str, "HH:mm")
        if parsed_time.isValid(): self.time_picker.setTime(parsed_time)
        layout.addWidget(self.time_picker)
        
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Hủy"); self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok = QPushButton("Lưu"); self.btn_ok.setStyleSheet("background-color: #22c55e; color: white;")
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_cancel); btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)

    def get_new_time(self): return self.time_picker.time().toString("HH:mm")

class QueueDialog(QDialog):
    def __init__(self, queue_list, parent=None):
        super().__init__(parent)
        self.queue_list = queue_list 
        self.setWindowTitle("📋 Quản lý Hàng Đợi")
        self.resize(900, 600)
        self.setStyleSheet(MODERN_STYLE)
        
        layout = QVBoxLayout(self)
        self.table_widget = QTableWidget(0, 3)
        self.table_widget.setHorizontalHeaderLabels(["Giờ sẽ đăng", "Từ khóa / Nguồn", "Nội dung"])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) 
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) 
        self.table_widget.itemDoubleClicked.connect(self.edit_queue_time)
        self.table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) 
        layout.addWidget(self.table_widget)

        action_layout = QHBoxLayout()
        self.btn_edit = QPushButton('✏️ Sửa giờ đăng')
        self.btn_edit.setStyleSheet("background-color: #eab308; color: white;")
        self.btn_edit.clicked.connect(self.edit_queue_time)
        self.btn_delete = QPushButton('❌ Xóa khỏi Hàng đợi')
        self.btn_delete.setStyleSheet("background-color: #ef4444; color: white;")
        self.btn_delete.clicked.connect(self.delete_queue_item)
        
        action_layout.addStretch()
        action_layout.addWidget(self.btn_edit)
        action_layout.addWidget(self.btn_delete)
        layout.addLayout(action_layout)
        self.refresh_table()

    def refresh_table(self):
        self.table_widget.setRowCount(0)
        self.queue_list.sort(key=lambda x: x['time'])
        for row, q in enumerate(self.queue_list):
            self.table_widget.insertRow(row)
            time_item = QTableWidgetItem(f" 🕒 {q.get('time', '00:00')} ")
            time_item.setData(Qt.ItemDataRole.UserRole, q)
            time_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.table_widget.setItem(row, 0, time_item)
            
            kw_display = f"🖼️ {q.get('keyword', '')}" if q.get('image_path') else q.get("keyword", "")
            self.table_widget.setItem(row, 1, QTableWidgetItem(kw_display))
            self.table_widget.setItem(row, 2, QTableWidgetItem(q.get("content", "").replace('\n', ' ')))

    def edit_queue_time(self):
        selected_items = self.table_widget.selectedItems()
        if not selected_items: return
        queue_data = self.table_widget.item(selected_items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        
        dialog = EditTimeDialog(queue_data.get("time", "00:00"), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            queue_data["time"] = dialog.get_new_time() 
            if self.parent(): 
                self.parent().queue_list.sort(key=lambda x: x['time'])
                self.parent().save_config()
                if hasattr(self.parent(), 'show_notification'):
                    self.parent().show_notification("Thành công! ⏰", "Đã thay đổi giờ đăng của bài viết.")
            self.refresh_table()

    def delete_queue_item(self):
        selected_rows = set(item.row() for item in self.table_widget.selectedItems())
        for row in sorted(selected_rows, reverse=True):
            queue_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if queue_data in self.queue_list: self.queue_list.remove(queue_data) 
            self.table_widget.removeRow(row)
        if self.parent(): 
            self.parent().save_config()
            if hasattr(self.parent(), 'show_notification'):
                self.parent().show_notification("Đã xóa! 🗑️", "Đã xóa bài viết khỏi hàng đợi.")

class ScheduleDialog(QDialog):
    def __init__(self, schedule_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📅 Cài đặt Khung giờ Bot Auto A-Z")
        self.resize(500, 450)
        self.setStyleSheet(MODERN_STYLE)
        self.initUI()
        self.load_schedule(schedule_str)

    def initUI(self):
        layout = QVBoxLayout(self)
        
        input_layout = QHBoxLayout()
        self.time_picker = QTimeEdit()
        self.time_picker.setDisplayFormat("HH:mm")
        self.time_picker.setTime(QTime.currentTime())
        self.time_picker.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.time_picker.setMinimumHeight(40)
        
        self.spin_time_count = QSpinBox()
        self.spin_time_count.setRange(1, 50)
        self.spin_time_count.setPrefix("Số bài: ")
        self.spin_time_count.setFont(QFont("Segoe UI", 13))
        self.spin_time_count.setMinimumHeight(40)
        
        self.btn_add = QPushButton('➕ Thêm Lịch')
        self.btn_add.setStyleSheet("background-color: #0ea5e9; color: white; font-weight: bold; min-height: 40px;")
        self.btn_add.clicked.connect(self.add_time)
        
        input_layout.addWidget(self.time_picker)
        input_layout.addWidget(self.spin_time_count)
        input_layout.addWidget(self.btn_add)
        layout.addLayout(input_layout)

        self.table_times = QTableWidget(0, 3)
        self.table_times.setHorizontalHeaderLabels(["⏰ Khung Giờ", "📝 Số bài", "Thao tác"])
        self.table_times.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_times.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_times.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_times.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table_times.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_times.setAlternatingRowColors(True)
        self.table_times.verticalHeader().setVisible(False)
        self.table_times.verticalHeader().setDefaultSectionSize(50) 
        self.table_times.setStyleSheet("QTableWidget { border: 1px solid #cbd5e1; border-radius: 8px; background-color: #ffffff; alternate-background-color: #f8fafc; font-size: 15px; } QHeaderView::section { background-color: #f1f5f9; border: none; border-bottom: 2px solid #cbd5e1; font-weight: bold; color: #334155; padding: 10px; }")
        layout.addWidget(self.table_times)

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Hủy bỏ")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save = QPushButton("💾 Lưu Cài Đặt")
        self.btn_save.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold;")
        self.btn_save.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def load_schedule(self, schedule_str):
        if not schedule_str: return
        for p in schedule_str.split(','):
            match = re.search(r"(\d{2}:\d{2})(?:\s*\(x(\d+)\))?", p.strip())
            if match:
                time_val = match.group(1)
                count_val = match.group(2) if match.group(2) else "1"
                self._insert_row(time_val, count_val)

    def add_time(self):
        time_str = self.time_picker.time().toString("HH:mm")
        count_str = str(self.spin_time_count.value())
        for i in range(self.table_times.rowCount()):
            if self.table_times.item(i, 0).data(Qt.ItemDataRole.UserRole) == time_str:
                QMessageBox.warning(self, "Lỗi trùng lặp", f"Khung giờ {time_str} đã có trong danh sách rồi!")
                return
        self._insert_row(time_str, count_str)

    def _insert_row(self, time_val, count_val):
        row = self.table_times.rowCount()
        self.table_times.insertRow(row)
        
        it_t = QTableWidgetItem(f"{time_val}")
        it_t.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        it_t.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        it_t.setForeground(QColor("#2563eb"))
        it_t.setData(Qt.ItemDataRole.UserRole, time_val)
        
        it_c = QTableWidgetItem(f"{count_val} bài")
        it_c.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        it_c.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        it_c.setForeground(QColor("#475569"))
        it_c.setData(Qt.ItemDataRole.UserRole, count_val)

        btn_del = QPushButton("❌ Xóa")
        btn_del.setStyleSheet("QPushButton { background-color: #fee2e2; color: #ef4444; border: none; padding: 6px 10px; border-radius: 6px; font-weight: bold; margin: 4px; } QPushButton:hover { background-color: #fca5a5; }")
        btn_del.clicked.connect(self.delete_row)
        
        self.table_times.setItem(row, 0, it_t)
        self.table_times.setItem(row, 1, it_c)
        self.table_times.setCellWidget(row, 2, btn_del)

    def delete_row(self):
        button = self.sender()
        if button:
            for row in range(self.table_times.rowCount()):
                if self.table_times.cellWidget(row, 2) == button:
                    self.table_times.removeRow(row)
                    break

    def get_schedule_string(self):
        times = []
        for i in range(self.table_times.rowCount()):
            t = self.table_times.item(i, 0).data(Qt.ItemDataRole.UserRole)
            c = self.table_times.item(i, 1).data(Qt.ItemDataRole.UserRole)
            times.append(f"{t} (x{c})" if int(c) > 1 else t)
        return ", ".join(times)


# ==========================================
# 🖥️ CLASS GIAO DIỆN CHÍNH
# ==========================================
class AutoPostApp(QWidget):
    def __init__(self):
        super().__init__()
        self.worker_thread = None 
        self.api_pipeline_thread = None 
        self.silent_pipeline_thread = None 
        self.last_posted_minute = None 
        self.drafts_list, self.queue_list, self.history_list = [], [], []
        self.bot_mode = 1 
        self.auto_az_schedule = [] 
        self.is_settings_unlocked = False 
        self.schedule_string = "" 
        
        self.logo_path = ""
        self.logo_pos = "Góc dưới Phải"
        self.logo_opacity = 100
        self.logo_scale = 20
        
        # [MỚI] Cấu hình Video
        self.veo_model = "veo-3.1-generate-preview"
        self.veo_aspect = "16:9"
        self.veo_res = "720p"
        self.veo_duration = "8"
        self.veo_negative = ""
        
        self.check_and_create_cookie_file()
        
        self.setStyleSheet(MODERN_STYLE)
        self.init_db() 
        self.initUI()
        self.setup_tray_icon()
        self.load_config() 

    def set_run_on_startup(self, enable):
        if platform.system() == "Windows":
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "KomeifyAutoPostBot"
            executable_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
                if enable:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{executable_path}"')
                else:
                    try:
                        winreg.DeleteValue(key, app_name)
                    except FileNotFoundError:
                        pass
                winreg.CloseKey(key)
            except Exception:
                pass

    def check_and_create_cookie_file(self):
        cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
        if not os.path.exists(cookie_path) or os.path.getsize(cookie_path) == 0:
            with open(cookie_path, 'w', encoding='utf-8') as f:
                f.write("# Netscape HTTP Cookie File\n# HDSD: Xóa nội dung trong file này, copy toàn bộ nội dung từ tiện ích 'Get cookies.txt LOCALLY' trên Chrome và dán vào đây, sau đó bấm Save (Ctrl+S).\n")

    def open_cookie_file(self):
        cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
        self.check_and_create_cookie_file() 
        try:
            if sys.platform == "win32":
                os.startfile(cookie_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", cookie_path])
            else:
                subprocess.call(["xdg-open", cookie_path])
            self.show_notification("Đã mở file Cookie 🍪", "Hãy dán dữ liệu cookie vào file vừa hiện lên và lưu lại (Ctrl+S) nhé.")
        except Exception as e:
            self.show_notification("Lỗi", f"Không thể tự động mở file: {e}", True)

    def open_logo_dialog(self):
        dialog = LogoSettingsDialog(self.logo_path, self.logo_pos, self.logo_opacity, self.logo_scale, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.logo_path, self.logo_pos, self.logo_opacity, self.logo_scale = dialog.get_settings()
            self.save_config()
            if self.logo_path:
                self.show_notification("Logo đã lưu 🖼️", "Đã cập nhật cấu hình đóng dấu bản quyền.")

    # --- [MỚI] Hàm mở cửa sổ cài đặt Video ---
    def open_video_dialog(self):
        dialog = VideoSettingsDialog(self.veo_model, self.veo_aspect, self.veo_res, self.veo_duration, self.veo_negative, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.veo_model, self.veo_aspect, self.veo_res, self.veo_duration, self.veo_negative = dialog.get_settings()
            self.save_config()
            self.show_notification("Đã lưu Cài đặt Video 🎬", "Video tạo ra sẽ tuân theo chuẩn bạn vừa lưu.")

    def init_db(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS drafts (keyword TEXT, content TEXT, timestamp TEXT, image_path TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS queue_posts (time TEXT, keyword TEXT, content TEXT, image_path TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS history_posts (post_time TEXT, keyword TEXT, content TEXT, mode TEXT, image_path TEXT)''')
        
        try: c.execute('ALTER TABLE drafts ADD COLUMN image_path TEXT')
        except: pass
        try: c.execute('ALTER TABLE queue_posts ADD COLUMN image_path TEXT')
        except: pass
        try: c.execute('ALTER TABLE history_posts ADD COLUMN image_path TEXT')
        except: pass
        
        # [MỚI] Bảng CSDL thêm cột cho video_path
        try: c.execute('ALTER TABLE drafts ADD COLUMN video_path TEXT')
        except: pass
        try: c.execute('ALTER TABLE queue_posts ADD COLUMN video_path TEXT')
        except: pass
        try: c.execute('ALTER TABLE history_posts ADD COLUMN video_path TEXT')
        except: pass

        conn.commit()
        conn.close()

    def save_config(self):
        self.init_db() 
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        settings = {
            "gemini_key": self.input_gemini.text(),
            "gemini_model": self.combo_gemini_model.currentData(), 
            "tiktok_api": self.input_tiktok_api.text(),
            "fb_id": self.input_fb_id.text(),
            "fb_token": self.input_fb_token.text(),
            "target_topics": self.input_target_topics.text(), 
            "auto_az_times": self.schedule_string,
            "logo_path": self.logo_path, 
            "logo_pos": self.logo_pos,
            "logo_opacity": str(self.logo_opacity),
            "logo_scale": str(self.logo_scale),
            "run_on_startup": "1" if self.check_startup.isChecked() else "0",
            "veo_model": self.veo_model,
            "veo_aspect": self.veo_aspect,
            "veo_res": self.veo_res,
            "veo_duration": self.veo_duration,
            "veo_negative": self.veo_negative
        }
        for k, v in settings.items(): c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, v))

        c.execute("DELETE FROM drafts")
        for d in self.drafts_list: c.execute("INSERT INTO drafts VALUES (?, ?, ?, ?, ?)", (d.get("keyword",""), d.get("content",""), d.get("timestamp",""), d.get("image_path", ""), d.get("video_path", "")))

        c.execute("DELETE FROM queue_posts")
        for q in self.queue_list: c.execute("INSERT INTO queue_posts VALUES (?, ?, ?, ?, ?)", (q.get("time",""), q.get("keyword",""), q.get("content",""), q.get("image_path", ""), q.get("video_path", "")))

        c.execute("DELETE FROM history_posts")
        for h in self.history_list: c.execute("INSERT INTO history_posts VALUES (?, ?, ?, ?, ?, ?)", (h.get("post_time",""), h.get("keyword",""), h.get("content",""), h.get("mode",""), h.get("image_path", ""), h.get("video_path", "")))

        conn.commit(); conn.close()
        
        self.set_run_on_startup(self.check_startup.isChecked())

    def action_save_config(self):
        self.save_config()
        self.set_status("✅ Đã lưu cấu hình hệ thống.")
        self.show_notification("Lưu thành công! 💾", "Toàn bộ cấu hình hệ thống đã được lưu lại an toàn.")

    def load_config(self):
        if not os.path.exists(DB_FILE): return
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        c.execute("SELECT key, value FROM settings")
        settings = dict(c.fetchall())
        self.input_gemini.setText(settings.get("gemini_key", ""))
        self.input_tiktok_api.setText(settings.get("tiktok_api", ""))
        self.input_fb_id.setText(settings.get("fb_id", ""))
        self.input_fb_token.setText(settings.get("fb_token", ""))
        self.input_target_topics.setText(settings.get("target_topics", "")) 
        
        self.logo_path = settings.get("logo_path", "")
        self.logo_pos = settings.get("logo_pos", "Góc dưới Phải")
        self.logo_opacity = int(settings.get("logo_opacity", "100"))
        self.logo_scale = int(settings.get("logo_scale", "20"))
        
        self.veo_model = settings.get("veo_model", "veo-3.1-generate-preview")
        self.veo_aspect = settings.get("veo_aspect", "16:9")
        self.veo_res = settings.get("veo_res", "720p")
        self.veo_duration = settings.get("veo_duration", "8")
        self.veo_negative = settings.get("veo_negative", "")
        
        self.check_startup.setChecked(settings.get("run_on_startup", "0") == "1")
        
        saved_model = settings.get("gemini_model", "gemini-2.5-flash")
        idx = self.combo_gemini_model.findData(saved_model)
        if idx >= 0:
            self.combo_gemini_model.setCurrentIndex(idx)
        
        self.schedule_string = settings.get("auto_az_times", "") 

        self.drafts_list.clear()
        try:
            for row in c.execute("SELECT keyword, content, timestamp, image_path, video_path FROM drafts"):
                self.drafts_list.append({"keyword": row[0], "content": row[1], "timestamp": row[2], "image_path": row[3], "video_path": row[4]})
        except sqlite3.OperationalError:
            pass

        self.queue_list.clear()
        try:
            for row in c.execute("SELECT time, keyword, content, image_path, video_path FROM queue_posts ORDER BY time ASC"):
                self.queue_list.append({"time": row[0], "keyword": row[1], "content": row[2], "image_path": row[3], "video_path": row[4]})
        except sqlite3.OperationalError:
            pass

        self.history_list.clear()
        try:
            for row in c.execute("SELECT post_time, keyword, content, mode, image_path, video_path FROM history_posts"):
                self.history_list.append({"post_time": row[0], "keyword": row[1], "content": row[2], "mode": row[3], "image_path": row[4], "video_path": row[5]})
        except sqlite3.OperationalError:
            pass

        conn.close()
        self.refresh_history_table()

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file tài liệu sản phẩm", "", "Documents (*.txt *.md *.csv *.docx);;All Files (*)")
        if file_path:
            self.input_doc_file.setText(file_path)
            self.show_notification("Đã tải file! 📂", f"Đã đính kèm file: {os.path.basename(file_path)}")

    def initUI(self):
        self.setWindowTitle('Facebook Auto-Post Manager PRO (Pipeline AI)')
        self.resize(1400, 850) 
        self.root_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # --- TAB 1: BẢNG ĐIỀU KHIỂN ---
        self.tab_dashboard = QWidget()
        dashboard_main_layout = QHBoxLayout(self.tab_dashboard)
        
        log_group = QGroupBox("Terminal: System Logs")
        log_layout = QVBoxLayout()
        self.list_history = QListWidget() 
        self.list_history.setStyleSheet("background-color: #0f172a; color: #38bdf8; font-family: Consolas, monospace;")
        log_layout.addWidget(self.list_history)
        log_group.setLayout(log_layout)
        
        right_layout = QVBoxLayout()

        # 1. KHU VỰC AI
        ai_group = QGroupBox("✨ Trợ lý AI Sinh Content")
        ai_layout = QVBoxLayout()
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel('📌 Nguồn/Trend:'))
        self.console_keyword = QLineEdit() 
        self.console_keyword.setPlaceholderText("VD: Thời trang, Review...")
        row1.addWidget(self.console_keyword, stretch=1)
        
        row1.addWidget(QLabel('🎥 Số video tham khảo:'))
        self.spin_max_videos = QSpinBox()
        self.spin_max_videos.setRange(1, 50)
        self.spin_max_videos.setValue(1)
        row1.addWidget(self.spin_max_videos)
        
        row1.addWidget(QLabel('📝 Số bài tạo ra:'))
        self.spin_ai_count = QSpinBox()
        self.spin_ai_count.setRange(1, 20)
        self.spin_ai_count.setValue(1)
        row1.addWidget(self.spin_ai_count)
        ai_layout.addLayout(row1)

        row1_5 = QHBoxLayout()
        row1_5.addWidget(QLabel('🎯 Chủ đề / Ngách quan tâm:'))
        self.input_target_topics = QLineEdit()
        self.input_target_topics.setPlaceholderText("VD: Sức khỏe, Ăn uống, Mẹ bé (AI sẽ hướng nội dung về ngách này)")
        row1_5.addWidget(self.input_target_topics, stretch=1)
        ai_layout.addLayout(row1_5)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel('📂 Tài liệu SP (TXT, DOCX):'))
        self.input_doc_file = QLineEdit()
        self.input_doc_file.setReadOnly(True)
        self.input_doc_file.setPlaceholderText("Gắn file thông tin sản phẩm (nếu có)")
        self.btn_browse_file = QPushButton('Chọn File')
        self.btn_browse_file.clicked.connect(self.browse_file)
        self.btn_clear_file = QPushButton('❌')
        self.btn_clear_file.clicked.connect(self.input_doc_file.clear)
        
        row2.addWidget(self.input_doc_file, stretch=1)
        row2.addWidget(self.btn_browse_file)
        row2.addWidget(self.btn_clear_file)
        ai_layout.addLayout(row2)

        row3 = QVBoxLayout()
        row3.addWidget(QLabel('💡 Yêu cầu thêm (Prompt):'))
        self.input_custom_prompt = QTextEdit()
        self.input_custom_prompt.setPlaceholderText("Ra lệnh thêm cho AI (VD: Viết theo phong cách GenZ, chèn ưu đãi 50%...)")
        self.input_custom_prompt.setMaximumHeight(60)
        row3.addWidget(self.input_custom_prompt)
        ai_layout.addLayout(row3)

        row4 = QVBoxLayout()
        row4.addWidget(QLabel('🚫 Nội dung / Từ khóa cần loại bỏ:'))
        self.input_ignore_keywords = QTextEdit()
        self.input_ignore_keywords.setPlaceholderText("Dán nội dung 1 bài viết hoặc các từ khóa mà bạn tuyệt đối KHÔNG MUỐN AI đưa vào bài viết mới...")
        self.input_ignore_keywords.setMaximumHeight(60)
        row4.addWidget(self.input_ignore_keywords)
        ai_layout.addLayout(row4)
        
        row_limit = QHBoxLayout()
        row_limit.addWidget(QLabel('📏 Giới hạn số từ tối đa:'))
        self.spin_word_limit = QSpinBox()
        self.spin_word_limit.setRange(0, 5000)
        self.spin_word_limit.setValue(0)
        self.spin_word_limit.setSpecialValueText("Không giới hạn")
        row_limit.addWidget(self.spin_word_limit)
        row_limit.addStretch()
        ai_layout.addLayout(row_limit)
        
        row_logo = QHBoxLayout()
        self.check_gen_image = QCheckBox("🎨 Tự động vẽ ảnh minh họa (Image)")
        self.check_gen_image.setStyleSheet("color: #2563eb; font-weight: bold;")
        self.btn_logo_settings = QPushButton('🖼️ Cài đặt Logo')
        self.btn_logo_settings.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; padding: 6px 15px;")
        self.btn_logo_settings.clicked.connect(self.open_logo_dialog)
        
        # --- [MỚI] TÍCH HỢP TÍNH NĂNG TẠO VIDEO ---
        self.check_gen_video = QCheckBox("🎬 Tự động tạo Video (Veo 3.1)")
        self.check_gen_video.setStyleSheet("color: #ef4444; font-weight: bold; margin-left: 20px;")
        self.btn_video_settings = QPushButton('🎥 Cài đặt Video')
        self.btn_video_settings.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; padding: 6px 15px;")
        self.btn_video_settings.clicked.connect(self.open_video_dialog)
        
        row_logo.addWidget(self.check_gen_image)
        row_logo.addWidget(self.btn_logo_settings)
        row_logo.addWidget(self.check_gen_video)
        row_logo.addWidget(self.btn_video_settings)
        row_logo.addStretch()
        ai_layout.addLayout(row_logo)
        
        self.btn_auto_pipeline = QPushButton('⚡ BẮT ĐẦU CÀO & PHÂN TÍCH')
        self.btn_auto_pipeline.setStyleSheet("background-color: #8b5cf6; color: white; padding: 15px; font-size: 15px; margin-top: 10px;")
        self.btn_auto_pipeline.clicked.connect(self.run_api_pipeline)
        ai_layout.addWidget(self.btn_auto_pipeline)
        
        ai_group.setLayout(ai_layout)
        right_layout.addWidget(ai_group)

        # 2. KHU VỰC NÚT MỞ KHO CONTENT VÀ HÀNG ĐỢI
        storage_group = QGroupBox("📁 Quản lý Kho Bài & Lên Lịch")
        storage_layout = QHBoxLayout()
        
        self.btn_open_drafts = QPushButton('📂 MỞ KHO CONTENT ĐÃ TẠO')
        self.btn_open_drafts.setStyleSheet("background-color: #3b82f6; color: white; font-size: 16px; padding: 20px;")
        self.btn_open_drafts.clicked.connect(self.open_drafts_dialog)
        
        self.btn_open_queue = QPushButton('📋 XEM HÀNG ĐỢI ĐANG CHỜ')
        self.btn_open_queue.setStyleSheet("background-color: #06b6d4; color: white; font-size: 16px; padding: 20px;")
        self.btn_open_queue.clicked.connect(self.open_queue_dialog)
        
        storage_layout.addWidget(self.btn_open_drafts)
        storage_layout.addWidget(self.btn_open_queue)
        storage_group.setLayout(storage_layout)
        right_layout.addWidget(storage_group)

        # 3. THIẾT LẬP CHẾ ĐỘ BOT CHẠY NGẦM
        schedule_group = QGroupBox("🤖 Thiết lập Chế độ Bot")
        schedule_layout = QVBoxLayout()
        
        mode_layout = QHBoxLayout()
        self.mode_group = QButtonGroup(self)
        
        self.radio_mode_queue = QRadioButton("🟢 CHẾ ĐỘ 1: Bốc bài từ Hàng Đợi")
        self.radio_mode_queue.setChecked(True)
        self.radio_mode_queue.clicked.connect(self.on_mode_clicked)
        
        self.radio_mode_az = QRadioButton("🚀 CHẾ ĐỘ 2: Auto A-Z (Cào -> Dịch -> Post)")
        self.radio_mode_az.clicked.connect(self.on_mode_clicked)
        
        self.mode_group.addButton(self.radio_mode_queue, 1)
        self.mode_group.addButton(self.radio_mode_az, 2)
        mode_layout.addWidget(self.radio_mode_queue); mode_layout.addWidget(self.radio_mode_az)
        schedule_layout.addLayout(mode_layout)

        time_container = QFrame()
        time_container.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;")
        time_layout = QHBoxLayout(time_container)

        time_input_col = QVBoxLayout()
        
        self.btn_open_schedule = QPushButton('📅 CÀI ĐẶT KHUNG GIỜ (CHẾ ĐỘ 2)')
        self.btn_open_schedule.setStyleSheet("background-color: #3b82f6; color: white; font-size: 15px; font-weight: bold; padding: 15px;")
        self.btn_open_schedule.clicked.connect(self.open_schedule_dialog)
        
        lbl_info_schedule = QLabel("💡 Bot sẽ tự động chạy ngầm theo các khung giờ được cài đặt trong này.")
        lbl_info_schedule.setStyleSheet("color: #64748b; font-style: italic; margin-top: 5px;")
        
        time_input_col.addWidget(self.btn_open_schedule)
        time_input_col.addWidget(lbl_info_schedule)
        time_input_col.addStretch()
        
        action_col = QVBoxLayout()
        
        self.lbl_bot_status = QLabel("Trạng thái Bot: 🔴 ĐANG TẮT")
        self.lbl_bot_status.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        self.lbl_bot_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action_col.addWidget(self.lbl_bot_status)
        
        self.btn_start_bot = QPushButton('🤖 BẬT BOT TỰ ĐỘNG NGAY')
        self.btn_start_bot.setStyleSheet("background-color: #16a34a; color: white; font-size: 18px; font-weight: bold; min-height: 80px;")
        self.btn_start_bot.clicked.connect(self.toggle_background_task)
        action_col.addWidget(self.btn_start_bot)
        
        time_layout.addLayout(time_input_col, stretch=2)
        time_layout.addSpacing(20)
        time_layout.addLayout(action_col, stretch=1)
        
        schedule_layout.addWidget(time_container)
        schedule_group.setLayout(schedule_layout)
        right_layout.addWidget(schedule_group)

        right_layout.addStretch()

        dashboard_main_layout.addWidget(log_group, stretch=3)
        dashboard_main_layout.addLayout(right_layout, stretch=7)
        self.tab_widget.addTab(self.tab_dashboard, "🚀 Bảng Điều Khiển")

        # --- TAB 2, 3, 4 ---
        self.tab_guide = QWidget()
        guide_layout = QVBoxLayout(self.tab_guide)
        guide_content = QTextEdit()
        guide_content.setReadOnly(True)
        guide_content.setStyleSheet("background-color: #ffffff; padding: 25px; font-size: 15px; line-height: 1.8;")
        guide_content.setHtml("""
        <h2 style='color: #2563eb;'>🚀 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG AUTO-POST PRO</h2>
        <p>Phần mềm giúp bạn tự động hóa quy trình tìm kiếm nội dung TikTok, dùng AI (Gemini) để viết lại thành bài đăng Facebook và tự động lên lịch đăng tải.</p>
        
        <h3 style='color: #f59e0b;'>🟢 CHẾ ĐỘ 1: BỐC BÀI TỪ HÀNG ĐỢI (BÁN TỰ ĐỘNG)</h3>
        <p><i>Phù hợp khi bạn muốn tự tay duyệt từng bài viết trước khi đăng.</i></p>
        <ol>
            <li><b>Bước 1 (Tìm & Viết bài):</b> Nhập từ khóa Trend và Ngữ cảnh -> Bấm <b>BẮT ĐẦU CÀO & PHÂN TÍCH</b>. Tất cả bài AI tạo ra sẽ tự động được lưu vào Kho Content.</li>
            <li><b>Bước 2 (Kiểm duyệt):</b> Bấm <b>MỞ KHO CONTENT ĐÃ TẠO</b> để xem lại, sửa bài.</li>
            <li><b>Bước 3 (Xếp lịch):</b> Tích chọn các bài muốn đăng -> Cài đặt giờ -> Bấm <b>Chuyển vào Hàng đợi</b>.</li>
            <li><b>Bước 4 (Chạy Bot):</b> Quay lại Bảng điều khiển -> Chọn Chế độ 1 -> Bấm <b>BẬT BOT TỰ ĐỘNG</b>.</li>
        </ol>

        <h3 style='color: #16a34a;'>🚀 CHẾ ĐỘ 2: AUTO A-Z (TỰ ĐỘNG HOÀN TOÀN)</h3>
        <p><i>Phù hợp khi bạn muốn bot tự động làm mọi thứ theo giờ đã định.</i></p>
        <ol>
            <li><b>Bước 1 (Chuẩn bị):</b> Nhập từ khóa Trend và Ngữ cảnh bổ sung.</li>
            <li><b>Bước 2 (Lên lịch):</b> Bấm <b>CÀI ĐẶT KHUNG GIỜ</b> để thêm các giờ bạn muốn Bot chạy.</li>
            <li><b>Bước 3 (Chạy Bot):</b> Chọn Chế độ 2 -> Bấm <b>BẬT BOT TỰ ĐỘNG</b>. Cứ đến giờ, Bot sẽ tự động đi tìm video mới, tự dịch, tự viết bài và đăng thẳng lên Facebook!</li>
        </ol>
        """)
        guide_layout.addWidget(guide_content)
        self.tab_widget.addTab(self.tab_guide, "📖 Hướng Dẫn")

        self.tab_posted_history = QWidget()
        history_layout = QVBoxLayout(self.tab_posted_history)
        self.table_posted_history = QTableWidget(0, 4)
        self.table_posted_history.setHorizontalHeaderLabels(["Thời gian Đăng", "Nguồn", "Nội dung", "Loại đăng"])
        self.table_posted_history.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.table_posted_history)
        self.tab_widget.addTab(self.tab_posted_history, "🕒 Lịch sử Post")

        # --- TAB THIẾT LẬP ---
        self.tab_settings = QWidget()
        set_layout = QVBoxLayout(self.tab_settings)
        
        # Nhóm API & Facebook
        api_group = QGroupBox("🔑 Cấu hình API & Facebook")
        api_layout = QVBoxLayout()
        self.input_gemini = QLineEdit()
        self.input_gemini.setEchoMode(QLineEdit.EchoMode.Password) 
        self.combo_gemini_model = QComboBox() 
        self.combo_gemini_model.addItem("gemini-2.5-flash (Khuyên dùng - Rẻ & Nhanh)", "gemini-2.5-flash")
        self.combo_gemini_model.addItem("gemini-2.5-pro (Thông minh - Đắt hơn)", "gemini-2.5-pro")
        self.combo_gemini_model.addItem("gemini-3.1-pro-preview (Siêu cấp - Rất đắt)", "gemini-3.1-pro-preview")
        self.combo_gemini_model.addItem("gemini-2.5-flash-lite (Siêu rẻ - Tốc độ cao)", "gemini-2.5-flash-lite")
        self.combo_gemini_model.setCurrentIndex(0) 
        self.input_tiktok_api = QLineEdit()
        self.input_tiktok_api.setEchoMode(QLineEdit.EchoMode.Password) 
        self.input_fb_id = QLineEdit()
        self.input_fb_token = QLineEdit()
        self.input_fb_token.setEchoMode(QLineEdit.EchoMode.Password) 
        
        api_layout.addWidget(QLabel("Gemini API Key:")); api_layout.addWidget(self.input_gemini)
        api_layout.addWidget(QLabel("Chọn Model AI (Gemini):")); api_layout.addWidget(self.combo_gemini_model)
        api_layout.addWidget(QLabel("Apify Token:")); api_layout.addWidget(self.input_tiktok_api)
        api_layout.addWidget(QLabel("ID Facebook Page/User:")); api_layout.addWidget(self.input_fb_id)
        api_layout.addWidget(QLabel("FB Access Token:")); api_layout.addWidget(self.input_fb_token)
        
        self.btn_open_cookie = QPushButton('🍪 CẬP NHẬT COOKIES TIKTOK (Chống chặn)')
        self.btn_open_cookie.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold; padding: 10px; margin-top: 10px;")
        self.btn_open_cookie.clicked.connect(self.open_cookie_file)
        api_layout.addWidget(QLabel("<b>Bảo mật TikTok (Bắt buộc):</b>"))
        api_layout.addWidget(self.btn_open_cookie)
        api_group.setLayout(api_layout)
        set_layout.addWidget(api_group)
        
        self.check_startup = QCheckBox("🚀 Khởi động phần mềm ngầm cùng Windows")
        self.check_startup.setStyleSheet("font-weight: bold; color: #16a34a; font-size: 15px; margin-top: 10px;")
        set_layout.addWidget(self.check_startup)

        self.btn_save_config = QPushButton('💾 LƯU CẤU HÌNH')
        self.btn_save_config.setStyleSheet("background-color: #2563eb; color: white; min-height: 40px; margin-top: 10px;")
        self.btn_save_config.clicked.connect(self.action_save_config)
        set_layout.addWidget(self.btn_save_config)
        
        set_layout.addStretch()
        self.tab_widget.addTab(self.tab_settings, "⚙️ Thiết Lập")

        self.root_layout.addWidget(self.tab_widget)
        self.status_label = QLabel(" Trạng thái: 🟢 Ready.")
        self.root_layout.addWidget(self.status_label)

    def on_tab_changed(self, index):
        if index == 3 and not self.is_settings_unlocked:
            self.tab_widget.blockSignals(True)
            self.tab_widget.setCurrentIndex(0) 
            self.tab_widget.blockSignals(False)
            password, ok = QInputDialog.getText(self, "Quản trị", "Mật khẩu: (admin)", QLineEdit.EchoMode.Password)
            if ok and password == ADMIN_PASSWORD:
                self.is_settings_unlocked = True
                self.tab_widget.setCurrentIndex(3)

    def refresh_history_table(self):
        self.table_posted_history.setRowCount(0) 
        for i, record in enumerate(reversed(self.history_list)):
            self.table_posted_history.insertRow(i)
            self.table_posted_history.setItem(i, 0, QTableWidgetItem(record.get('post_time', '')))
            
            kw_display = f"🖼️ {record.get('keyword', '')}" if record.get('image_path') else record.get("keyword", "")
            self.table_posted_history.setItem(i, 1, QTableWidgetItem(kw_display))
            
            self.table_posted_history.setItem(i, 2, QTableWidgetItem(record.get("content", "").replace('\n', ' ')))
            self.table_posted_history.setItem(i, 3, QTableWidgetItem(record.get("mode", "")))

    def set_status(self, text): self.status_label.setText(f" Trạng thái: {text}")
    
    def add_log(self, msg):
        self.list_history.addItem(QListWidgetItem(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"))
        self.list_history.scrollToBottom()

    def show_notification(self, title, message, is_error=False):
        if self.tray_icon.isVisible() and self.isHidden():
            icon = QSystemTrayIcon.MessageIcon.Critical if is_error else QSystemTrayIcon.MessageIcon.Information
            self.tray_icon.showMessage(title, message, icon, 3500)
        else:
            CustomToast(self, title, message, is_error)

    def on_mode_clicked(self):
        if self.worker_thread and self.worker_thread.is_running:
            self.show_notification("Bot đang chạy ⚠️", "Vui lòng TẮT BOT trước khi chuyển chế độ!", True)
            
            if self.bot_mode == 1:
                self.radio_mode_queue.setChecked(True)
            elif self.bot_mode == 2:
                self.radio_mode_az.setChecked(True)

    def open_schedule_dialog(self):
        if self.worker_thread and self.worker_thread.is_running:
            self.show_notification("Bot đang chạy ⚠️", "Vui lòng TẮT BOT trước khi thay đổi khung giờ!", True)
            return

        dialog = ScheduleDialog(self.schedule_string, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.schedule_string = dialog.get_schedule_string()
            self.save_config()
            self.add_log("-> Đã cập nhật lại Khung giờ chạy Bot Auto A-Z.")
            self.show_notification("Cập nhật Lịch! 📅", "Đã lưu danh sách khung giờ chạy Bot tự động.")

    def run_api_pipeline(self):
        if self.worker_thread and self.worker_thread.is_running:
            self.show_notification("Bot đang chạy ⚠️", "Vui lòng TẮT BOT trước khi cào và phân tích thủ công!", True)
            return

        if not self.input_tiktok_api.text() or not self.input_gemini.text(): 
            self.show_notification("Thiếu API Key ❌", "Vui lòng nhập đầy đủ API Key trong phần Thiết Lập!", True)
            return
            
        self.btn_auto_pipeline.setEnabled(False)
        self.api_pipeline_thread = ApiPipelineWorker(
            self.input_tiktok_api.text(), 
            self.input_gemini.text(), 
            self.combo_gemini_model.currentData(), 
            self.spin_ai_count.value(), 
            self.console_keyword.text().strip(),
            self.input_target_topics.text().strip(), 
            self.input_custom_prompt.toPlainText().strip(),
            self.spin_max_videos.value(),
            self.input_doc_file.text().strip(),
            self.input_ignore_keywords.toPlainText().strip(), 
            self.spin_word_limit.value(),
            self.check_gen_image.isChecked(),
            self.logo_path,
            self.logo_pos,
            self.logo_opacity,
            self.logo_scale,
            self.check_gen_video.isChecked(), 
            self.veo_model,
            self.veo_aspect,
            self.veo_res,
            self.veo_duration,
            self.veo_negative
        )
        self.api_pipeline_thread.status_signal.connect(self.add_log) 
        self.api_pipeline_thread.finished_signal.connect(self.on_pipeline_finished)
        self.api_pipeline_thread.start()

    def on_pipeline_finished(self, trend, content_list):
        self.btn_auto_pipeline.setEnabled(True)
        if content_list and not content_list[0].get("content", "").startswith("Lỗi"):
            current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S") 
            for item in content_list: 
                self.drafts_list.append({
                    "keyword": trend, 
                    "content": item["content"], 
                    "timestamp": current_time, 
                    "image_path": item.get("image_path", ""),
                    "video_path": item.get("video_path", "")
                })
            self.save_config()
            self.add_log(f"-> Đã chuyển thành công {len(content_list)} bài vào Kho Content.")
            self.show_notification("Phân tích hoàn tất! 🎉", f"AI đã tạo xong {len(content_list)} bài viết. Mở Kho Content để xem.")
        else:
            self.show_notification("Lỗi AI ❌", "Quá trình phân tích thất bại.", True)

    def open_drafts_dialog(self):
        dialog = DraftsDialog(self.drafts_list, self)
        dialog.post_now_requested.connect(lambda d: self.execute_post(d, datetime.now().strftime("%H:%M"), False))
        dialog.queue_requested.connect(lambda d, t: self.queue_list.append({"time": t, "keyword": d.get("keyword", ""), "content": d.get("content", ""), "image_path": d.get("image_path", ""), "video_path": d.get("video_path", "")}))
        dialog.exec()

    def open_queue_dialog(self): QueueDialog(self.queue_list, self).exec()

    def toggle_background_task(self):
        if self.worker_thread is None or not self.worker_thread.is_running:
            self.bot_mode = self.mode_group.checkedId() 
            
            if self.bot_mode == 2:
                self.auto_az_schedule = []
                if not self.schedule_string:
                    self.show_notification("Chưa cài giờ ❌", "Hãy bấm 'CÀI ĐẶT KHUNG GIỜ' trước khi bật Bot A-Z", True)
                    return
                
                for p in self.schedule_string.split(','):
                    match = re.search(r"(\d{2}:\d{2})(?:\s*\(x(\d+)\))?", p.strip())
                    if match:
                        self.auto_az_schedule.append({
                            "time": match.group(1), 
                            "count": int(match.group(2)) if match.group(2) else 1
                        })
                if not self.auto_az_schedule:
                    self.show_notification("Lỗi", "Cần có ít nhất 1 khung giờ hợp lệ!", True)
                    return
                
            self.worker_thread = AutoPostWorker()
            self.worker_thread.time_tick.connect(self.process_bot_tick)
            self.worker_thread.start()
            
            self.btn_start_bot.setText('🔴 TẮT BOT')
            self.btn_start_bot.setStyleSheet("background-color: #ef4444; color: white; min-height: 80px; font-size: 18px;")
            
            mode_name = "1 (Hàng đợi)" if self.bot_mode == 1 else "2 (Auto A-Z)"
            self.lbl_bot_status.setText(f"Trạng thái Bot: 🟢 ĐANG CHẠY (Chế độ {mode_name})")
            self.lbl_bot_status.setStyleSheet("color: #16a34a; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
            
            self.show_notification("Bot đang chạy 🤖", f"Hệ thống tự động hóa đã được bật (Chế độ {self.bot_mode}).")
        else:
            self.worker_thread.stop()
            
            self.btn_start_bot.setText('🤖 BẬT BOT TỰ ĐỘNG NGAY')
            self.btn_start_bot.setStyleSheet("background-color: #16a34a; color: white; min-height: 80px; font-size: 18px;")
            
            self.lbl_bot_status.setText("Trạng thái Bot: 🔴 ĐANG TẮT")
            self.lbl_bot_status.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
            
            self.show_notification("Đã tắt Bot 🔴", "Hệ thống tự động hóa đã dừng.")

    def on_silent_pipeline_finished(self, trend, content_list, target_time):
        if content_list and not content_list[0].get("content", "").startswith("Lỗi"):
            self.add_log(f"✅ [BOT A-Z] AI đã tạo xong {len(content_list)} bài. Đang tiến hành đăng lên Facebook...")
            for item in content_list:
                post_data = {"keyword": trend, "content": item["content"], "image_path": item.get("image_path", ""), "video_path": item.get("video_path", "")}
                self.execute_post(post_data, target_time, True, "Auto A-Z")
        else:
            err_msg = content_list[0].get("content", "Không rõ") if content_list else "Không rõ"
            self.add_log(f"❌ [BOT A-Z] Lỗi không thể tạo bài: {err_msg}")
            self.show_notification("Bot A-Z thất bại", "Vui lòng kiểm tra System Log", True)

    def process_bot_tick(self, now_str):
        if now_str == self.last_posted_minute: return 
        if self.bot_mode == 1:
            for i in range(len(self.queue_list) - 1, -1, -1):
                if self.queue_list[i]["time"] == now_str:
                    self.add_log(f"⏰ [BOT] Đến giờ {now_str}! Đang lấy bài từ Hàng đợi để đăng...")
                    self.execute_post(self.queue_list[i], now_str, True, "Auto Queue")
                    self.queue_list.pop(i) 
        elif self.bot_mode == 2:
            for sched in self.auto_az_schedule:
                if sched["time"] == now_str:
                    self.add_log(f"⏰ [BOT A-Z] Đến giờ {now_str}! Bắt đầu tự động Cào & Đăng ({sched['count']} bài)...")
                    self.silent_pipeline_thread = ApiPipelineWorker(
                        self.input_tiktok_api.text(), 
                        self.input_gemini.text(), 
                        self.combo_gemini_model.currentData(), 
                        sched["count"], 
                        self.console_keyword.text().strip(),
                        self.input_target_topics.text().strip(),
                        self.input_custom_prompt.toPlainText().strip(),
                        self.spin_max_videos.value(),
                        self.input_doc_file.text().strip(),
                        self.input_ignore_keywords.toPlainText().strip(), 
                        self.spin_word_limit.value(),
                        self.check_gen_image.isChecked(),
                        self.logo_path,
                        self.logo_pos,
                        self.logo_opacity,
                        self.logo_scale,
                        self.check_gen_video.isChecked(), 
                        self.veo_model,
                        self.veo_aspect,
                        self.veo_res,
                        self.veo_duration,
                        self.veo_negative
                    )
                    self.silent_pipeline_thread.status_signal.connect(self.add_log)
                    self.silent_pipeline_thread.finished_signal.connect(lambda t, c: self.on_silent_pipeline_finished(t, c, now_str))
                    self.silent_pipeline_thread.start()
        self.last_posted_minute = now_str; self.save_config()

    def execute_post(self, post_data, time_str, is_auto=True, mode_name="Auto Bot"):
        content = post_data.get("content", "")
        keyword = post_data.get("keyword", "")
        image_path = post_data.get("image_path", "")
        video_path = post_data.get("video_path", "")
        prefix = f"[{mode_name.upper()}]" if is_auto else "[THỦ CÔNG]"
        
        self.add_log(f"B7: {prefix} Đang chuẩn bị đăng lên Facebook Graph API...")
        QApplication.processEvents() 
        
        fb_id = self.input_fb_id.text().strip()
        fb_token = self.input_fb_token.text().strip()
        
        if not fb_id or not fb_token:
            err = "Chưa cấu hình ID Facebook hoặc Token trong tab Thiết Lập!"
            self.add_log(f"❌ {prefix} Lỗi: {err}")
            self.show_notification("Lỗi Facebook API ❌", err, True)
            return
            
        try:
            # Ưu tiên Đăng Video trước nếu có
            if video_path and os.path.exists(video_path):
                self.add_log(f"-> Phát hiện có Video đính kèm, đang upload lên Facebook...")
                url = f"https://graph.facebook.com/v24.0/{fb_id}/videos"
                payload = {"description": content, "access_token": fb_token}
                with open(video_path, 'rb') as f:
                    files = {'source': f}
                    response = requests.post(url, data=payload, files=files)
            elif image_path and os.path.exists(image_path):
                self.add_log(f"-> Phát hiện có Ảnh đính kèm, đang upload lên Facebook...")
                url = f"https://graph.facebook.com/v24.0/{fb_id}/photos"
                payload = {"caption": content, "access_token": fb_token}
                with open(image_path, 'rb') as f:
                    files = {'source': f}
                    response = requests.post(url, data=payload, files=files)
            else:
                url = f"https://graph.facebook.com/v24.0/{fb_id}/feed"
                payload = {"message": content, "access_token": fb_token}
                response = requests.post(url, data=payload)
                
            resp_json = response.json()
            
            if response.status_code == 200 and ("id" in resp_json or "post_id" in resp_json):
                post_id = resp_json.get("post_id", resp_json.get("id"))
                self.add_log(f"B8: [Facebook API] Đăng bài thành công! Post ID: {post_id}")
                self.set_status(f"✅ {mode_name} đăng FB thành công lúc {time_str}")
                
                self.show_notification("Đăng FB thành công! 🚀", f"Bài viết đã được đẩy lên lúc {time_str}.")
                
                real_post_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S") 
                self.history_list.append({"post_time": real_post_time, "keyword": keyword, "content": content, "mode": mode_name, "image_path": image_path, "video_path": video_path})
                if len(self.history_list) > 1000: self.history_list.pop(0)
                    
                self.refresh_history_table() 
                self.save_config()
            else:
                err_msg = resp_json.get("error", {}).get("message", "Lỗi không xác định")
                self.add_log(f"❌ B8: [Facebook API] Thất bại: {err_msg}")
                self.show_notification("Lỗi đăng FB ❌", f"Facebook API: {err_msg}", True)
        except Exception as e:
            self.add_log(f"❌ B8: [Facebook API] Lỗi kết nối mạng: {str(e)}")
            self.show_notification("Lỗi mạng ❌", f"Không thể kết nối Facebook: {str(e)}", True)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)); self.tray_icon.show() 
        self.tray_icon.activated.connect(lambda r: self.showNormal() if r == QSystemTrayIcon.ActivationReason.DoubleClick else None)

    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.is_running: 
            event.ignore()
            self.hide()
            self.tray_icon.showMessage("Bot đang chạy ngầm", "Phần mềm đã ẩn xuống khay hệ thống.", QSystemTrayIcon.MessageIcon.Information, 3000)
        else: 
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv); app.setStyle("Fusion") 
    window = AutoPostApp(); window.show()
    sys.exit(app.exec())