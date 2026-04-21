import os
import sys
import time
import re
from PIL import Image
from moviepy import VideoFileClip
import yt_dlp
from google import genai
from google.genai import types
from docx import Document
from pypdf import PdfReader

# ==========================================
# 1. ĐỊNH TUYẾN ĐƯỜNG DẪN PORTABLE CHUẨN
# ==========================================
if getattr(sys, 'frozen', False) or '__compiled__' in globals():
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
else:
    # Lùi 1 cấp vì file này đang nằm trong thư mục 'services'
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

data_dir = os.path.join(base_dir, 'data')
os.makedirs(data_dir, exist_ok=True)
# ==========================================

class AIService:
    def __init__(self, gemini_key):
        self.client = genai.Client(api_key=gemini_key) if gemini_key else None
        # 2. Gắn chặt file temp vào đúng thư mục data an toàn
        self.temp_video = os.path.join(data_dir, "temp_video.mp4")
        self.temp_audio = os.path.join(data_dir, "temp_audio.mp3")

    class SilentLogger:
        def debug(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass

    # =========================
    # 3. HÀM XÓA FILE CHỐNG CRASH (FIX WINERROR 32)
    # =========================
    def safe_remove(self, filepath):
        """Cố gắng xóa file, nếu bị kẹt thì đợi 1s rồi xóa lại. Vẫn kẹt thì bỏ qua để app chạy tiếp."""
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except PermissionError:
                time.sleep(1) # Chờ Windows nhả file
                try:
                    os.remove(filepath)
                except:
                    pass

    # =========================
    # MAIN PIPELINE
    # =========================
    def process_content_pipeline(self, videos_data, config):

        if not self.client:
            yield {"type": "error", "message": "Thiếu Gemini API Key"}
            return

        combined_script = ""
        successful_count = 0

        # =========================
        # BƯỚC 1: LOAD + TRANSCRIBE
        # =========================
        yield {"type": "log", "message": "B1: Tải & bóc băng video..."}

        for idx, video in enumerate(videos_data, 1):

            if successful_count >= config.get("max_videos", 3):
                break

            # Gọi hàm xóa an toàn thay vì os.remove() thông thường
            self.safe_remove(self.temp_video)
            self.safe_remove(self.temp_audio)

            try:
                ydl_opts = {
                    "outtmpl": self.temp_video,
                    "format": "best",
                    "quiet": True,
                    "logger": self.SilentLogger(),
                    # Tìm cookies.txt ở đúng thư mục gốc
                    "cookiefile": os.path.join(base_dir, "cookies.txt") if os.path.exists(os.path.join(base_dir, "cookies.txt")) else None
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video["link"]])

            except Exception as e:
                yield {"type": "log", "message": f"Lỗi tải video: {e}"}
                continue

            # extract audio
            try:
                video_clip = VideoFileClip(self.temp_video)
                audio = video_clip.audio
                audio.write_audiofile(self.temp_audio, logger=None)
                
                # Đóng file để nhả tài nguyên
                audio.close()
                video_clip.close()
                
                # Ép Python dọn dẹp bộ nhớ ngay lập tức để ngắt hẳn liên kết với file
                del audio
                del video_clip
            except Exception as e:
                yield {"type": "log", "message": f"Lỗi tách âm thanh: {e}"}
                continue

            # TRANSCRIBE
            try:
                audio_file = self.client.files.upload(file=self.temp_audio)

                resp = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        audio_file,
                        "Chuyển toàn bộ lời nói thành văn bản."
                    ],
                )

                text = resp.text.strip()

            except:
                text = "Không có lời thoại"

            combined_script += f"""
VIDEO {idx}
Tác giả: {video['creator']}
Mô tả: {video['desc']}
Lời thoại: {text}
--------------------
"""
            successful_count += 1

        if successful_count == 0:
            yield {"type": "error", "message": "Không xử lý được video"}
            return

        # =========================
        # BƯỚC 2: PHÂN TÍCH TREND
        # =========================
        yield {"type": "log", "message": "B2: Phân tích thông điệp cốt lõi..."}

        trend_prompt = f"""
Phân tích dữ liệu sau và tìm:

1. Chủ đề chính (xuất hiện nhiều nhất)
2. Thông điệp lặp lại
3. Hành vi / insight người dùng

Dữ liệu:
{combined_script}

Trả về dạng:
- Chủ đề:
- Insight:
- Keywords:
"""

        trend_resp = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=trend_prompt
        )

        trend_data = trend_resp.text.strip()

# =========================
        # BƯỚC 3: VIẾT CONTENT 
        # =========================
        yield {"type": "log", "message": "B3: Nạp tài liệu & Viết bài Facebook..."}

        system_prompt = config.get("system_prompt", "Bạn là copywriter chuyên nghiệp")
        
        # --- LOGIC MỚI: ĐỌC FILE TÀI LIỆU SẢN PHẨM ---
        # --- LOGIC MỚI: ĐỌC ĐA ĐỊNH DẠNG (TXT, DOCX, PDF) ---
        product_info = "Không có thông tin sản phẩm cụ thể."
        doc_path = config.get("doc_file_path", "")
        
        if doc_path and os.path.exists(doc_path):
            try:
                # Lấy đuôi file (chuyển về chữ thường để so sánh)
                ext = doc_path.split('.')[-1].lower()
                extracted_text = ""

                if ext == 'txt':
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        extracted_text = f.read()
                        
                elif ext == 'docx':
                    doc = Document(doc_path)
                    extracted_text = "\n".join([para.text for para in doc.paragraphs])
                    
                elif ext == 'pdf':
                    reader = PdfReader(doc_path)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            extracted_text += page_text + "\n"
                            
                elif ext == 'doc':
                    yield {"type": "log", "message": "⚠️ File .doc quá cũ, vui lòng Save As thành .docx. Tạm bỏ qua tài liệu!"}
                
                else:
                    yield {"type": "log", "message": f"⚠️ Định dạng .{ext} chưa được hỗ trợ!"}

                # Kiểm tra xem file có chữ không (chống file rỗng hoặc file PDF chỉ toàn ảnh)
                if extracted_text.strip():
                    product_info = extracted_text.strip()
                    yield {"type": "log", "message": f"✅ Đã nạp thành công tài liệu từ file .{ext}!"}
                elif ext in ['txt', 'docx', 'pdf']:
                    yield {"type": "log", "message": "⚠️ File tài liệu trống hoặc không thể trích xuất chữ!"}

            except Exception as e:
                yield {"type": "log", "message": f"⚠️ Lỗi đọc file tài liệu: {e}"}
        # ---------------------------------------------

        write_prompt = f"""
{system_prompt}

DỮ LIỆU TỪ VIDEO TRENDING:
{combined_script}

PHÂN TÍCH INSIGHT:
{trend_data}

THÔNG TIN SẢN PHẨM CẦN BÁN (BẮT BUỘC PHẢI LỒNG GHÉP):
{product_info}

QUY TẮC BẮT BUỘC:
1. Dùng nội dung từ "Video Trending" làm "mồi câu" (Hook) để thu hút sự chú ý.
2. Dẫn dắt mượt mà từ câu chuyện trending sang giới thiệu "Thông tin sản phẩm".
3. Phải có lời kêu gọi hành động (Call to Action) mua hàng ở cuối bài.
4. VIẾT thành câu chuyện liền mạch, KHÔNG liệt kê máy móc.

YÊU CẦU:
- Viết {config.get('count', 1)} bài đăng Facebook hoàn chỉnh.
- Phân tách các bài bằng dấu |||
"""

        write_resp = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=write_prompt,
            config=types.GenerateContentConfig(temperature=0.8)
        )

        raw_text = write_resp.text.strip()
        posts = [x.strip() for x in raw_text.split("|||") if len(x.strip()) > 30]

        if not posts:
            yield {"type": "error", "message": "AI không tạo được nội dung"}
            return

# =========================
        # BƯỚC 4 & 5: XỬ LÝ MEDIA (CHỈ CHẠY KHI ĐƯỢC TICK CHỌN)
        # =========================
        yield {"type": "log", "message": "B4: Xử lý Hình ảnh & Video (Nếu có)..."}

        final_posts = []

        for idx, content in enumerate(posts):
            image_path = ""
            video_path = ""
            media_prompt = "" 
            
            # -----------------------------------
            # 1. TẠO ẢNH (CHỈ KHI TICK CHỌN)
            # -----------------------------------
            if config.get("gen_image"):
                yield {"type": "log", "message": f"🎨 Đang nghĩ ý tưởng ảnh cho bài {idx+1}..."}
                
                keyword_prompt = f"""
                Bài viết: "{content}"
                YÊU CẦU: Chỉ mô tả thứ nhìn thấy, Chủ thể + hành động + bối cảnh + ánh sáng/màu sắc. KHÔNG chữ.
                Trả về 1 câu prompt tiếng Anh
                """
                try:
                    keyword_resp = self.client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=keyword_prompt
                    )
                    media_prompt = keyword_resp.text.strip()
                    
                    yield {"type": "log", "message": f"⏳ Đang vẽ ảnh..."}
                    
                    img_resp = self.client.models.generate_content(
                        model="gemini-2.5-flash-image",
                        contents=media_prompt
                    )

                    if hasattr(img_resp.candidates[0].content.parts[0], "inline_data"):
                        img_bytes = img_resp.candidates[0].content.parts[0].inline_data.data
                        
                        img_dir = os.path.join(data_dir, "image")
                        os.makedirs(img_dir, exist_ok=True)
                        image_path = os.path.join(img_dir, f"img_{int(time.time())}_{idx}.png")

                        with open(image_path, "wb") as f:
                            f.write(img_bytes)
                except Exception as e:
                    yield {"type": "log", "message": f"⚠️ Lỗi vẽ ảnh bài {idx+1}: {e}"}

            # -----------------------------------
            # 2. TẠO VIDEO (CHỈ KHI TICK CHỌN)
            # -----------------------------------
            if config.get("gen_video"):
                yield {"type": "log", "message": f"🎬 Đang tư duy kịch bản video cho bài {idx+1}..."}

                video_prompt_req = f"""
                Dựa vào bài viết: "{content}"
                Thông tin sản phẩm: "{product_info}"

                HÃY ĐÓNG VAI ĐẠO DIỄN VIẾT 1 PROMPT TIẾNG ANH TẠO VIDEO (Dài tối đa 3 câu).
                CẤU TRÚC: [Cú máy] + [Chủ thể] + [Hành động đang diễn ra] + [Ánh sáng/Màu sắc].
                YÊU CẦU: Phải có yếu tố chuyển động rõ ràng. KHÔNG chữ, KHÔNG âm thanh.
                """
                try:
                    vp_resp = self.client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=video_prompt_req
                    )
                    veo_prompt = vp_resp.text.strip()
                    
                    veo_negative = config.get("veo_negative", "").strip()
                    if veo_negative:
                        veo_prompt += f" --negative {veo_negative}"

                    yield {"type": "log", "message": f"⏳ Đang gọi Veo render video (Sẽ mất 1-3 phút)..."}

                    video_resp = self.client.models.generate_content(
                        model=config.get("veo_model", "veo-3.1-generate-preview"),
                        contents=veo_prompt,
                        config=types.GenerateContentConfig(temperature=0.7)
                    )

                    if hasattr(video_resp.candidates[0].content.parts[0], "inline_data"):
                        vid_bytes = video_resp.candidates[0].content.parts[0].inline_data.data
                        
                        vid_dir = os.path.join(data_dir, "video")
                        os.makedirs(vid_dir, exist_ok=True)
                        video_path = os.path.join(vid_dir, f"vid_{int(time.time())}_{idx}.mp4")

                        with open(video_path, "wb") as f:
                            f.write(vid_bytes)
                            
                        yield {"type": "log", "message": f"✅ Render Video thành công!"}
                    else:
                        yield {"type": "log", "message": "⚠️ AI không trả về Video."}
                except Exception as e:
                    yield {"type": "log", "message": f"❌ Lỗi render video bài {idx+1}: {e}"}

            # -----------------------------------
            # LƯU VÀO KẾT QUẢ
            # -----------------------------------
            final_posts.append({
                "content": content,
                "image_prompt": media_prompt if config.get("gen_image") else "",
                "image_path": image_path,
                "video_path": video_path
            })