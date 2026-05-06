import os
import sys
import time
import re
import concurrent.futures
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
        # Gắn chặt file temp vào đúng thư mục data an toàn
        self.temp_video = os.path.join(data_dir, "temp_video.mp4")
        self.temp_audio = os.path.join(data_dir, "temp_audio.mp3")

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
    # MAIN PIPELINE
    # =========================
    def process_content_pipeline(self, videos_data, config, log_cb=None, stop_cb=None):
        if stop_cb and stop_cb(): return

        if not self.client:
            yield {"type": "error", "message": "Thiếu Gemini API Key"}
            return

        combined_script = ""
        successful_count = 0

        # Chế độ Gemini Only (không có TikTok): bỏ qua B1 và B2
        gemini_only_mode = not videos_data

        if gemini_only_mode:
            yield {"type": "log", "message": "🤖 Chế độ Gemini Only: Bỏ qua B1 (video) và B2 (trend). Dùng tài liệu sản phẩm trực tiếp."}
            combined_script = ""
            successful_count = 1  # Giả lập để pipeline không báo lỗi
        else:
            # =========================
            # BƯỚC 1: LOAD + TRANSCRIBE
            # =========================
            yield {"type": "log", "message": "B1: Tải & bóc băng video..."}

            for idx, video in enumerate(videos_data, 1):
                if stop_cb and stop_cb(): return

                if successful_count >= config.get("max_videos", 3):
                    break

                # Gọi hàm xóa an toàn thay vì os.remove() thông thường
                self.safe_remove(self.temp_video)
                self.safe_remove(self.temp_audio)
                
                # Dọn rác (các file part tải dở dang từ lần trước)
                self.safe_remove(self.temp_video + ".part")
                self.safe_remove(self.temp_video + ".ytdl")

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
                        ydl.download([video["link"]])

                except Exception as e:
                    yield {"type": "log", "message": f"Lỗi tải video: {e}"}
                    continue

                # extract audio
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
                except Exception as e:
                    yield {"type": "log", "message": f"⚠️ Lỗi tách âm thanh video {idx}: {e}. Bỏ qua, dùng mô tả thay thế."}
                    combined_script += f"""
VIDEO {idx}
Tác giả: {video['creator']}
Mô tả: {video['desc']}
Lời thoại: (Không có âm thanh)
--------------------
"""
                    successful_count += 1
                    continue

                # TRANSCRIBE
                text = "Không có lời thoại"
                try:
                    if log_cb: log_cb(f"⏳ Đang nhận dạng giọng nói video {idx}...")
                    def _transcribe():
                        audio_file = self.client.files.upload(file=self.temp_audio)
                        resp = self.client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[audio_file, "Chuyển toàn bộ lời nói thành văn bản."],
                        )
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
        # BƯỚC 2: PHÂN TÍCH TREND (chỉ khi có video)
        # =========================
        trend_data = ""
        if not gemini_only_mode:
            if stop_cb and stop_cb(): return
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
            try:
                trend_data = trend_resp.text.strip()
            except ValueError:
                yield {"type": "error", "message": "❌ Nội dung video trending chứa từ khóa nhạy cảm bị AI chặn. Bỏ qua bước này!"}
                return

            trend_html = trend_data.replace('\n', '<br>')
            yield {"type": "log", "message": f"📊 Kết quả phân tích Trend từ AI:<br><div style='color: #475569; font-size: 13px;'>{trend_html}</div>"}

        # =========================
        # BƯỚC 3: VIẾT CONTENT 
        # =========================
        if stop_cb and stop_cb(): return
        yield {"type": "log", "message": "B3: Nạp tài liệu & Viết bài Facebook..."}

        system_prompt = config.get("system_prompt", "Bạn là copywriter chuyên nghiệp")
        
        # --- ĐỌC NHIỀU FILE TÀI LIỆU SẢN PHẨM ---
        product_info = "Không có thông tin sản phẩm cụ thể."
        
        # 1. LẤY VÀ LÀM SẠCH DANH SÁCH ĐƯỜNG DẪN
        raw_paths = config.get("doc_file_paths", [])
        if not raw_paths:
            raw_paths = config.get("doc_file_path", "")
            
        doc_paths = []
        if isinstance(raw_paths, str):
            # Xử lý nếu UI truyền vào chuỗi ngăn cách bằng dấu phẩy: "C:/file1.txt, D:/file2.docx"
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

        # Lọc bỏ file rỗng, loại bỏ khoảng trắng (space) thừa ở 2 đầu đường dẫn
        doc_paths = [p.strip() for p in doc_paths if p and p.strip()]
        
        # Xóa các đường dẫn trùng lặp (nếu có)
        doc_paths = list(set(doc_paths))

        yield {"type": "log", "message": f"📄 Khởi động nạp {len(doc_paths)} tài liệu sản phẩm..."}

        all_extracted = []
        for doc_path in doc_paths:
            # 2. GẮN LOA BÁO LỖI NẾU KHÔNG TÌM THẤY FILE
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
            product_info = "\n\n".join(all_extracted)

        write_prompt = f"""{system_prompt}

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

YÊU CẦU ĐỊNH DẠNG ĐẦU RA (TUYỆT ĐỐI PHẢI TUÂN THỦ):
- Viết ĐÚNG {config.get('count', 1)} bài đăng Facebook.
- Phân tách mỗi bài bằng dấu ||| (ba gạch đứng) trên một dòng riêng.
- TUYỆT ĐỐI KHÔNG viết phần mở đầu, lời chào, giải thích hay bình luận trước/sau các bài.
- TUYỆT ĐỐI KHÔNG thêm tiêu đề "Bài 1:", "**Bài 1**", "---" hay bất kỳ nhãn đánh số nào.
- Chỉ trả về NỘI DUNG THUẦN TÚY của từng bài, phân tách bằng |||."""

        write_resp = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=write_prompt,
            config=types.GenerateContentConfig(temperature=0.8)
        )

        # Fix Bug #3: Chống crash do Policy Violation
        try:
            raw_text = write_resp.text.strip()
        except ValueError:
            yield {"type": "error", "message": "❌ AI từ chối viết bài do đầu vào vi phạm chính sách an toàn của Google. Vui lòng thử đổi video khác!"}
            return

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

        posts = [clean_post(p) for p in posts_raw if len(clean_post(p)) > 30]

        if not posts:
            yield {"type": "error", "message": "AI không tạo được nội dung"}
            return

        requested_count = config.get('count', 1)
        if len(posts) > requested_count:
            yield {"type": "log", "message": f"⚠️ AI sinh {len(posts)} bài (yêu cầu {requested_count}), tự động cắt bớt."}
            posts = posts[:requested_count]

        yield {"type": "log", "message": f"✅ Đã viết xong {len(posts)} bài content!"}
        for p_idx, p_content in enumerate(posts, 1):
            preview = p_content[:150].replace('\n', ' ') + "..." if len(p_content) > 150 else p_content.replace('\n', ' ')
            yield {"type": "log", "message": f"📝 Bài {p_idx}: <div style='color: #cbd5e1;'>{preview}</div>"}

        # =========================
        # BƯỚC 4 & 5: XỬ LÝ MEDIA 
        # =========================
        if config.get("gen_image") or config.get("gen_video"):
            yield {"type": "log", "message": "B4: Xử lý Hình ảnh & Video..."}
        else:
            yield {"type": "log", "message": "✅ Đang viết content hoàn tất (Không tạo media)."}

        final_posts = []
        media_fail_count = 0  

        for idx, content in enumerate(posts):
            if stop_cb and stop_cb(): return
            image_path = ""
            video_path = ""
            media_prompt = "" 
            
            # -----------------------------------
            # 1. TẠO ẢNH
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
                        yield {"type": "log", "message": f"✅ Vẽ ảnh bài {idx+1} thành công!"}
                    else:
                        media_fail_count += 1
                        yield {"type": "log", "message": f"⚠️ Bài {idx+1}: AI không trả về ảnh (có thể vi phạm policy), bỏ qua."}
                except Exception as e:
                    media_fail_count += 1
                    yield {"type": "log", "message": f"⚠️ Lỗi vẽ ảnh bài {idx+1}: {e}"}

            # -----------------------------------
            # 2. TẠO VIDEO 
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
                    else:
                        media_fail_count += 1
                        yield {"type": "log", "message": "⚠️ AI không trả về Video (có thể vi phạm policy), bỏ qua."}
                except Exception as e:
                    media_fail_count += 1
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

        # Fix Bug #2: Logic đếm lỗi Media chuẩn xác
        needs_image = bool(config.get("gen_image"))
        needs_video = bool(config.get("gen_video"))
        total_media_tasks = len(posts) * (int(needs_image) + int(needs_video))
        
        if total_media_tasks > 0 and media_fail_count >= total_media_tasks:
            yield {"type": "error", "message": f"❌ Toàn bộ {total_media_tasks} tiến trình tạo Media đều thất bại. Đã dừng pipeline!"}
            return

        yield {"type": "success", "data": final_posts}