import os
import sys
import time
import re
import concurrent.futures
from PIL import Image, ImageDraw
from moviepy import VideoFileClip
import yt_dlp
from google import genai
from google.genai import types
from docx import Document
from pypdf import PdfReader
from .token_tracker import TokenTracker

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
        # Gắn chặt file temp vào đúng thư mục data an toàn
        self.temp_video = os.path.join(data_dir, "temp_video.mp4")
        self.temp_audio = os.path.join(data_dir, "temp_audio.mp3")
        # Khởi tạo Token Tracker
        self.token_tracker = TokenTracker()

    class SilentLogger:
        def debug(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass

    # =========================
    # HÀM XÓA FILE CHỐNG CRASH (FIX WINERROR 32)
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
    # TOKEN TRACKING
    # =========================
    def _track_tokens(self, response, operation):
        """Theo dõi token sử dụng từ response của Gemini API"""
        try:
            if hasattr(response, 'usage_metadata'):
                meta = response.usage_metadata
                # Thử nhiều kiểu đặt tên thuộc tính khác nhau của các phiên bản SDK
                input_tokens = getattr(meta, 'prompt_token_count', 
                               getattr(meta, 'input_token_count', 
                               getattr(meta, 'input_tokens', 0)))
                
                output_tokens = getattr(meta, 'candidates_token_count', 
                                getattr(meta, 'output_token_count', 
                                getattr(meta, 'output_tokens', 0)))
                
                self.token_tracker.add_tokens(operation, input_tokens, output_tokens)
        except Exception:
            pass


    def get_token_stats(self):
        """Lấy thống kê token đã sử dụng"""
        return self.token_tracker.get_all_stats()
    
    def get_token_stats_text(self):
        """Lấy văn bản thống kê token"""
        return self.token_tracker.get_stats_text()
    
    def reset_token_tracker(self):
        """Xóa tất cả thống kê token (dùng khi bắt đầu pipeline mới)"""
        self.token_tracker.reset()

    # =========================
    # MAIN PIPELINE
    # =========================
    def process_content_pipeline(self, videos_data, config, log_cb=None, stop_cb=None):
        """Hàm chính điều phối toàn bộ quá trình"""
        if stop_cb and stop_cb(): return

        # Reset token tracker khi bắt đầu pipeline mới
        self.reset_token_tracker()

        if not self.client:
            yield {"type": "error", "message": "Thiếu Gemini API Key"}
            return

        # Chế độ Gemini Only (không có TikTok): bỏ qua B1 và B2
        gemini_only_mode = not videos_data
        
        combined_script = ""
        successful_count = 0

        if gemini_only_mode:
            yield {"type": "log", "message": "🤖 Chế độ Gemini Only: Bỏ qua B1 (video) và B2 (trend). Dùng tài liệu sản phẩm trực tiếp."}
            successful_count = 1
        else:
            yield {"type": "log", "message": "B1: Tải & bóc băng video..."}
            combined_script, successful_count = yield from self._process_videos(videos_data, config, log_cb, stop_cb)
            
            if successful_count == 0:
                yield {"type": "error", "message": "Không xử lý được video"}
                return

        trend_data = ""
        if not gemini_only_mode:
            if stop_cb and stop_cb(): return
            yield {"type": "log", "message": "B2: Phân tích thông điệp cốt lõi..."}
            
            trend_data = self._analyze_trend(combined_script)
            if trend_data is None:
                yield {"type": "error", "message": "❌ Nội dung video trending chứa từ khóa nhạy cảm bị AI chặn. Bỏ qua bước này!"}
                return
                
            trend_html = trend_data.replace('\n', '<br>')
            yield {"type": "log", "message": f"📊 Kết quả phân tích Trend từ AI:<br><div style='color: #475569; font-size: 13px;'>{trend_html}</div>"}

        if stop_cb and stop_cb(): return
        yield {"type": "log", "message": "B3: Nạp tài liệu & Viết bài Facebook..."}

        product_info = yield from self._load_documents(config)
        
        system_prompt = config.get("system_prompt", "Bạn là copywriter chuyên nghiệp")
        posts = self._generate_posts(system_prompt, combined_script, trend_data, product_info, config)
        
        if posts is None:
            yield {"type": "error", "message": "❌ AI từ chối viết bài do đầu vào vi phạm chính sách an toàn của Google. Vui lòng thử đổi video khác!"}
            return
            
        if not posts:
            yield {"type": "error", "message": "AI không tạo được nội dung"}
            return

        requested_count = config.get('count', 1)
        if len(posts) > requested_count:
            yield {"type": "log", "message": f"⚠️ AI sinh {len(posts)} bài (yêu cầu {requested_count}), tự động cắt bớt."}
            posts = posts[:requested_count]

        yield {"type": "log", "message": f"✅ Đã viết xong {len(posts)} bài content! Bắt đầu tạo Media..."}
        for p_idx, p_content in enumerate(posts, 1):
            preview = p_content[:150].replace('\n', ' ') + "..." if len(p_content) > 150 else p_content.replace('\n', ' ')
            yield {"type": "log", "message": f"📝 Bài {p_idx}: <div style='color: #cbd5e1;'>{preview}</div>"}

        final_posts, media_fail_count = yield from self._process_media_for_posts(posts, product_info, config, log_cb, stop_cb)

        needs_image = bool(config.get("gen_image"))
        needs_video = bool(config.get("gen_video"))
        total_media_tasks = len(posts) * (int(needs_image) + int(needs_video))
        
        if total_media_tasks > 0 and media_fail_count >= total_media_tasks:
            yield {"type": "error", "message": f"❌ Toàn bộ {total_media_tasks} tiến trình tạo Media đều thất bại. Đã dừng pipeline!"}
            return

        # Hiển thị thống kê token trước khi hoàn thành
        token_stats_text = self.get_token_stats_text()
        if token_stats_text:
            yield {"type": "log", "message": f"<br><br><b>{token_stats_text.replace(chr(10), '<br>')}</b>"}

        yield {"type": "success", "data": final_posts, "token_stats": self.get_token_stats()}

    # =========================================================================
    # CÁC HÀM XỬ LÝ CON (THEO CHUẨN SOLID & DRY)
    # =========================================================================
    def _process_videos(self, videos_data, config, log_cb, stop_cb):
        """Bước 1: Tải, tách âm thanh và nhận dạng giọng nói từ danh sách video"""
        combined_script = ""
        successful_count = 0
        
        for idx, video in enumerate(videos_data, 1):
            if stop_cb and stop_cb(): break

            if successful_count >= config.get("max_videos", 3):
                break

            self.safe_remove(self.temp_video)
            self.safe_remove(self.temp_audio)
            self.safe_remove(self.temp_video + ".part")
            self.safe_remove(self.temp_video + ".ytdl")

            yield from self._download_video(video["link"], idx, log_cb)

            audio_extracted = yield from self._extract_audio(idx, log_cb)
            if not audio_extracted:
                combined_script += f"\nVIDEO {idx}\nTác giả: {video['creator']}\nMô tả: {video['desc']}\nLời thoại: (Không có âm thanh)\n--------------------\n"
                successful_count += 1
                continue

            text = self._transcribe_audio(idx, log_cb)
            combined_script += f"\nVIDEO {idx}\nTác giả: {video['creator']}\nMô tả: {video['desc']}\nLời thoại: {text}\n--------------------\n"
            successful_count += 1
            
        return combined_script, successful_count

    def _download_video(self, link, idx, log_cb):
        """Tải video qua yt-dlp"""
        try:
            last_log_time = [0]
            def ytdl_hook(d):
                if d['status'] == 'downloading':
                    current_time = time.time()
                    if current_time - last_log_time[0] > 1.0:
                        percent_str = d.get('_percent_str', '0%')
                        clean_percent = re.sub(r'\x1b[^m]*m', '', percent_str).strip()
                        if log_cb:
                            log_cb(f"⏳ Đang tải video {idx}: {clean_percent}")
                        last_log_time[0] = current_time
                elif d['status'] == 'finished':
                    if log_cb:
                        log_cb(f"✅ Tải xong video {idx}, chuẩn bị tách âm thanh...")

            ydl_opts = {
                "outtmpl": self.temp_video,
                "format": "best",
                "quiet": True,
                "noresume": True,
                "overwrites": True,
                "logger": self.SilentLogger(),
                "progress_hooks": [ytdl_hook],
                "cookiefile": os.path.join(base_dir, "cookies.txt") if os.path.exists(os.path.join(base_dir, "cookies.txt")) else None,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Sec-Fetch-Mode": "navigate",
                },
                "sleep_interval": 2,
                "max_sleep_interval": 5,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
                
        except Exception as e:
            yield {"type": "log", "message": f"Lỗi tải video: {e}"}

    def _extract_audio(self, idx, log_cb):
        """Tách âm thanh từ video đã tải"""
        try:
            if log_cb: log_cb(f"⏳ Đang tách âm thanh video {idx}...")
            video_clip = VideoFileClip(self.temp_video)
            audio = video_clip.audio
            if audio is None:
                raise Exception("Video không có âm thanh")
            audio.write_audiofile(self.temp_audio, logger=None)
            audio.close()
            video_clip.close()
            del audio
            del video_clip
            if log_cb: log_cb(f"✅ Tách âm thanh video {idx} xong.")
            return True
        except Exception as e:
            yield {"type": "log", "message": f"⚠️ Lỗi tách âm thanh video {idx}: {e}. Bỏ qua, dùng mô tả thay thế."}
            return False

    def _transcribe_audio(self, idx, log_cb):
        """Nhận dạng giọng nói (Audio to Text) bằng Gemini"""
        text = "Không có lời thoại"
        try:
            if log_cb: log_cb(f"⏳ Đang nhận dạng giọng nói video {idx}...")
            def _transcribe():
                audio_file = self.client.files.upload(file=self.temp_audio)
                resp = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[audio_file, "Chuyển toàn bộ lời nói thành văn bản."],
                )
                self._track_tokens(resp, "transcribe")
                return resp.text.strip()

            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            future = executor.submit(_transcribe)
            try:
                text = future.result(timeout=120)
                if log_cb: log_cb(f"✅ Nhận dạng xong video {idx}.")
            except concurrent.futures.TimeoutError:
                if log_cb: log_cb(f"⚠️ Nhận dạng video {idx} quá 2 phút, bỏ qua.")
                text = "Không có lời thoại (timeout)"
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            text = "Không có lời thoại"
        return text

    def _analyze_trend(self, combined_script):
        """Bước 2: Phân tích thông điệp cốt lõi từ các video trending"""
        trend_prompt = f"Phân tích dữ liệu sau và tìm:\n1. Chủ đề chính (xuất hiện nhiều nhất)\n2. Thông điệp lặp lại\n3. Hành vi / insight người dùng\n\nDữ liệu:\n{combined_script}\n\nTrả về dạng:\n- Chủ đề:\n- Insight:\n- Keywords:\n"
        trend_resp = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=trend_prompt
        )
        self._track_tokens(trend_resp, "trend_analysis")
        
        try:
            return trend_resp.text.strip()
        except ValueError:
            return None

    def _load_documents(self, config):
        """Bước 3.1: Đọc và xử lý nội dung các file tài liệu"""
        raw_paths = config.get("doc_file_paths", [])
        if not raw_paths:
            raw_paths = config.get("doc_file_path", "")
            
        doc_paths = []
        if isinstance(raw_paths, str):
            if ',' in raw_paths and not raw_paths.startswith('['):
                doc_paths = [p.strip() for p in raw_paths.split(',')]
            else:
                import ast
                try:
                    doc_paths = ast.literal_eval(raw_paths)
                except:
                    doc_paths = [raw_paths.strip()]
        elif isinstance(raw_paths, list):
            doc_paths = raw_paths

        doc_paths = [p.strip() for p in doc_paths if p and p.strip()]
        doc_paths = list(set(doc_paths))

        yield {"type": "log", "message": f"📄 Khởi động nạp {len(doc_paths)} tài liệu sản phẩm..."}

        all_extracted = []
        for doc_path in doc_paths:
            if not os.path.exists(doc_path):
                yield {"type": "log", "message": f"⚠️ Bỏ qua: Không tìm thấy file '{doc_path}' (Kiểm tra lại đường dẫn có bị sai/xóa không)."}
                continue
                
            try:
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
                    yield {"type": "log", "message": f"⚠️ '{os.path.basename(doc_path)}': File .doc quá cũ, vui lòng Save As thành .docx. Bỏ qua!"}
                    continue
                else:
                    yield {"type": "log", "message": f"⚠️ Định dạng .{ext} chưa được hỗ trợ!"}
                    continue

                if extracted_text.strip():
                    all_extracted.append(f"=== {os.path.basename(doc_path)} ===\n{extracted_text.strip()}")
                    yield {"type": "log", "message": f"✅ Nạp thành công: {os.path.basename(doc_path)}"}
                else:
                    yield {"type": "log", "message": f"⚠️ '{os.path.basename(doc_path)}': File trống hoặc là ảnh (không trích được chữ)!"}

            except Exception as e:
                yield {"type": "log", "message": f"⚠️ Lỗi đọc '{os.path.basename(doc_path)}': {e}"}

        if all_extracted:
            return "\n\n".join(all_extracted)
        return "Không có thông tin sản phẩm cụ thể."

    def _generate_posts(self, system_prompt, combined_script, trend_data, product_info, config):
        """Bước 3.2: Sinh nội dung các bài đăng dựa trên thông tin đã xử lý"""
        custom_prompt = (config.get('custom_prompt') or '').strip()
        ignore_keywords = (config.get('ignore_keywords') or '').strip()
        try:
            word_limit = int(config.get('word_limit') or 0)
        except (TypeError, ValueError):
            word_limit = 0

        extra_requirements = []
        if custom_prompt:
            extra_requirements.append(f"- YÊU CẦU THÊM: {custom_prompt}")
        if ignore_keywords:
            extra_requirements.append(f"- NỘI DUNG CẤM: Tránh dùng hoặc đề cập đến: {ignore_keywords}")
        if word_limit > 0:
            extra_requirements.append(f"- Mỗi bài đăng không quá {word_limit} từ. Nếu cần, rút gọn nội dung nhưng vẫn giữ đủ ý.")

        extra_requirements_text = ""
        if extra_requirements:
            extra_requirements_text = "\n\nYÊU CẦU NGƯỜI DÙNG:\n" + "\n".join(extra_requirements)

        write_prompt = f"{system_prompt}\n\nDỮ LIỆU TỪ VIDEO TRENDING:\n{combined_script}\n\nPHÂN TÍCH INSIGHT:\n{trend_data}\n\nTHÔNG TIN SẢN PHẨM CẦN BÁN (BẮT BUỘC PHẢI LỒNG GHÉP):\n{product_info}\n\nQUY TẮC BẮT BUỘC:\n1. Dẫn dắt mượt mà từ câu chuyện trending sang giới thiệu \"Thông tin sản phẩm\".\n2. Phải có lời kêu gọi hành động (Call to Action) mua hàng ở cuối bài.\n3. VIẾT thành câu chuyện liền mạch, KHÔNG liệt kê máy móc.{extra_requirements_text}\n\nYÊU CẦU ĐỊNH DẠNG ĐẦU RA (TUYỆT ĐỐI PHẢI TUÂN THỦ):\n- Viết ĐÚNG {config.get('count', 1)} bài đăng Facebook.\n- Phân tách mỗi bài bằng dấu ||| (ba gạch đứng) trên một dòng riêng.\n- TUYỆT ĐỐI KHÔNG viết phần mở đầu, lời chào, giải thích hay bình luận trước/sau các bài.\n- TUYỆT ĐỐI KHÔNG thêm tiêu đề \"Bài 1:\", \"**Bài 1**\", \"---\" hay bất kỳ nhãn đánh số nào.\n- Chỉ trả về NỘI DUNG THUẦN TÚY của từng bài, phân tách bằng |||."

        print("data gửi đi " , write_prompt)
        write_resp = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=write_prompt,
            config=types.GenerateContentConfig(temperature=0.8)
        )
        self._track_tokens(write_resp, "content_writing")

        try:
            raw_text = write_resp.text.strip()
        except ValueError:
            return None

        if "|||" in raw_text:
            first_sep = raw_text.find("|||")
            before_first = raw_text[:first_sep].strip()
            if len(before_first) < 100:
                raw_text = raw_text[first_sep + 3:].strip()

        posts_raw = [x.strip() for x in raw_text.split("|||") if len(x.strip()) > 30]

        def clean_post(text):
            text = re.sub(r'^[\*#_\-\s]*(Bài|Post|BÀI)\s*\d+[\:\.\)]?\s*[^\n]*\n?', '', text, flags=re.IGNORECASE | re.MULTILINE).strip()
            text = re.sub(r'^[\-=]{3,}\s*$', '', text, flags=re.MULTILINE).strip()
            return text

        return [clean_post(p) for p in posts_raw if len(clean_post(p)) > 30]

    def _process_media_for_posts(self, posts, product_info, config, log_cb, stop_cb):
        """Bước 4 & 5: Gọi API tạo hình ảnh và video cho từng bài đăng"""
        if config.get("gen_image") or config.get("gen_video"):
            yield {"type": "log", "message": "B4: Xử lý Hình ảnh & Video..."}
        else:
            yield {"type": "log", "message": "✅ Đang viết content hoàn tất (Không tạo media)."}

        final_posts = []
        media_fail_count = 0  

        for idx, content in enumerate(posts):
            if stop_cb and stop_cb(): break
            image_path = ""
            video_path = ""
            media_prompt = "" 
            
            if config.get("gen_image"):
                img_result = yield from self._generate_image_for_post(content, idx, config)
                image_path = img_result.get("path", "")
                media_prompt = img_result.get("prompt", "")
                if not image_path:
                    media_fail_count += 1
            
            if config.get("gen_video"):
                vid_path = yield from self._generate_video_for_post(content, product_info, idx, config)
                video_path = vid_path
                if not video_path:
                    media_fail_count += 1
                    
            final_posts.append({
                "content": content,
                "image_prompt": media_prompt if config.get("gen_image") else "",
                "image_path": image_path,
                "video_path": video_path
            })
            
        return final_posts, media_fail_count

    def _generate_image_for_post(self, content, idx, config):
        """Tạo ảnh minh họa cho bài đăng"""
        yield {"type": "log", "message": f"🎨 Đang nghĩ ý tưởng ảnh cho bài {idx+1}..."}
        
        man_subject = config.get('dash_imagen_subject', '')
        man_action = config.get('dash_imagen_action', '')
        man_lighting = config.get('dash_imagen_lighting', '')
        man_camera = config.get('dash_imagen_camera', '')
        man_context = config.get('dash_imagen_context', '')

        constraints = []
        if man_subject: constraints.append(f"- Subject must be: {man_subject}")
        if man_action: constraints.append(f"- Action/Emotion must be: {man_action}")
        if man_lighting: constraints.append(f"- Lighting/Color must be: {man_lighting}")
        if man_camera: constraints.append(f"- Camera Angle must be: {man_camera}")
        if man_context: constraints.append(f"- Setting/Context must be: {man_context}")
        
        constraint_text = "\n".join(constraints) if constraints else "AI tự do sáng tạo dựa trên bài viết."

        keyword_prompt = f"Dựa trên bài viết Facebook sau: \"{content}\"\n\nHãy tạo một Prompt tiếng Anh chuyên nghiệp để vẽ ảnh minh họa, tập trung vào 5 yếu tố:\n1. Subject: Mô tả chi tiết ngoại hình, trang phục, tuổi tác của \"ngôi sao\" trong ảnh.\n2. Action/Emotion: Hành động hoặc cảm xúc sống động của chủ thể.\n3. Setting: Bối cảnh, môi trường xung quanh chi tiết.\n4. Lighting/Color: Ánh sáng (Cinematic, Golden hour, Soft light...) và màu sắc (Vibrant, Pastel...).\n5. Camera Angle: Góc máy và bố cục (Close-up, Wide shot, Top-down...).\n\nYÊU CẦU ĐẶC BIỆT TỪ NGƯỜI DÙNG (ƯU TIÊN CAO NHẤT):\n{constraint_text}\n\nYÊU CẦU: Chỉ mô tả hình ảnh, TUYỆT ĐỐI KHÔNG có chữ trong ảnh. Trả về duy nhất 1 câu prompt tiếng Anh."

        try:
            keyword_resp = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=keyword_prompt
            )
            self._track_tokens(keyword_resp, "image_prompt")
            
            media_prompt = keyword_resp.text.strip()
            
            style = config.get("dash_imagen_style", "Mặc định")
            aspect = config.get("dash_imagen_aspect", "1:1")
            
            final_media_prompt = media_prompt
            if style != "Mặc định":
                final_media_prompt += f", in {style} style"
            if aspect and aspect != "1:1":
                final_media_prompt += f", {aspect} aspect ratio"

            yield {"type": "log", "message": f"⏳ Đang vẽ ảnh ({aspect} - {style})..."}
            img_resp = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=final_media_prompt,
                config=types.GenerateContentConfig()
            )
            self._track_tokens(img_resp, "image_generation")

            img_data = None
            try:
                parts = img_resp.candidates[0].content.parts
                for part in parts:
                    if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                        img_data = part.inline_data.data
                        break
            except (IndexError, AttributeError):
                pass

            if img_data:
                img_dir = os.path.join(data_dir, "image")
                os.makedirs(img_dir, exist_ok=True)
                image_path = os.path.join(img_dir, f"img_{int(time.time())}_{idx}.png")
                with open(image_path, "wb") as f:
                    f.write(img_data)
                
                if self._apply_image_overlays(image_path, config):
                    yield {"type": "log", "message": f"✅ Vẽ ảnh & đóng dấu bài {idx+1} thành công!"}
                else:
                    yield {"type": "log", "message": f"✅ Vẽ ảnh bài {idx+1} thành công (Lỗi khi chèn logo)."}
                return {"path": image_path, "prompt": media_prompt}
            else:
                yield {"type": "log", "message": f"⚠️ Bài {idx+1}: AI không trả về ảnh (có thể vi phạm policy), bỏ qua."}
                return {"path": "", "prompt": media_prompt}
        except Exception as e:
            yield {"type": "log", "message": f"⚠️ Lỗi vẽ ảnh bài {idx+1}: {e}"}
            return {"path": "", "prompt": ""}

    def _generate_video_for_post(self, content, product_info, idx, config):
        """Tạo video qua mô hình Veo"""
        yield {"type": "log", "message": f"🎬 Đang tư duy kịch bản video cho bài {idx+1}..."}

        video_prompt_req = f"Dựa vào bài viết: \"{content}\"\nThông tin sản phẩm: \"{product_info}\"\n\nHÃY ĐÓNG VAI ĐẠO DIỄN VIẾT 1 PROMPT TIẾNG ANH TẠO VIDEO (Dài tối đa 3 câu).\nCẤU TRÚC: [Cú máy] + [Chủ thể] + [Hành động đang diễn ra] + [Ánh sáng/Màu sắc].\nYÊU CẦU: Phải có yếu tố chuyển động rõ ràng. KHÔNG chữ, KHÔNG âm thanh."
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

            vid_data = None
            try:
                v_parts = video_resp.candidates[0].content.parts
                for vpart in v_parts:
                    if hasattr(vpart, "inline_data") and vpart.inline_data and vpart.inline_data.data:
                        vid_data = vpart.inline_data.data
                        break
            except (IndexError, AttributeError):
                pass

            if vid_data:
                vid_dir = os.path.join(data_dir, "video")
                os.makedirs(vid_dir, exist_ok=True)
                video_path = os.path.join(vid_dir, f"vid_{int(time.time())}_{idx}.mp4")
                with open(video_path, "wb") as f:
                    f.write(vid_data)
                yield {"type": "log", "message": f"✅ Render Video thành công!"}
                return video_path
            else:
                yield {"type": "log", "message": "⚠️ AI không trả về Video (có thể vi phạm policy), bỏ qua."}
                return ""
        except Exception as e:
            yield {"type": "log", "message": f"❌ Lỗi render video bài {idx+1}: {e}"}
            return ""

    def _apply_image_overlays(self, base_path, config):
        """Chèn Logo và Ảnh người dùng vào ảnh gốc"""
        try:
            # Mở ảnh gốc
            base_img = Image.open(base_path).convert("RGBA")
            width, height = base_img.size
            
            # 1. XỬ LÝ LOGO
            logo_path = config.get("logo_path", "")
            if logo_path and os.path.exists(logo_path):
                try:
                    logo = Image.open(logo_path).convert("RGBA")
                    
                    # Tính toán kích thước Logo (theo % so với chiều rộng ảnh gốc)
                    l_scale_percent = config.get("logo_scale", 20)
                    l_width = int(width * (l_scale_percent / 100.0))
                    l_height = int(logo.height * (l_width / logo.width))
                    logo = logo.resize((l_width, l_height), Image.Resampling.LANCZOS)
                    
                    # --- BỔ SUNG: XÓA NỀN LOGO ---
                    # Lấy màu pixel ở góc để làm màu nền cần xóa
                    datas = logo.getdata()
                    bg_color = datas[0]
                    new_data = []
                    tolerance = 30 # Độ lệch màu cho phép
                    for item in datas:
                        if abs(item[0] - bg_color[0]) < tolerance and \
                           abs(item[1] - bg_color[1]) < tolerance and \
                           abs(item[2] - bg_color[2]) < tolerance:
                            new_data.append((255, 255, 255, 0))
                        else:
                            new_data.append(item)
                    logo.putdata(new_data)
                    
                    # Xử lý Độ mờ (Opacity)
                    l_opacity = config.get("logo_opacity", 100) / 100.0
                    if l_opacity < 1.0:
                        alpha = logo.split()[3]
                        alpha = alpha.point(lambda p: int(p * l_opacity))
                        logo.putalpha(alpha)
                    
                    # Tính toán vị trí (Padding mặc định 20px)
                    pos_str = config.get("logo_pos", "Góc dưới Phải")
                    lx, ly = 20, 20 # Mặc định trên trái
                    
                    if pos_str == "Góc dưới Phải":
                        lx, ly = width - l_width - 20, height - l_height - 20
                    elif pos_str == "Góc dưới Trái":
                        lx, ly = 20, height - l_height - 20
                    elif pos_str == "Góc trên Phải":
                        lx, ly = width - l_width - 20, 20
                    elif pos_str == "Góc trên Trái":
                        lx, ly = 20, 20
                    elif pos_str == "Chính giữa":
                        lx, ly = (width - l_width) // 2, (height - l_height) // 2
                    
                    # Dán Logo lên
                    base_img.paste(logo, (lx, ly), logo)
                except Exception as e:
                    print(f"Lỗi xử lý logo: {e}")



            # Lưu lại file cuối cùng (convert về RGB để tối ưu dung lượng và tương thích FB)
            base_img.convert("RGB").save(base_path, "JPEG", quality=95)
            return True
            
        except Exception as e:
            print(f"Lỗi tổng quát _apply_image_overlays: {e}")
            return False