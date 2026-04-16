# services/ai_service.py
import os
import time
from PIL import Image
from moviepy import VideoFileClip
import yt_dlp
from google import genai
from google.genai import types

class AIService:
    def __init__(self, gemini_key):
        self.gemini_key = gemini_key
        self.client = genai.Client(api_key=self.gemini_key) if gemini_key else None
        
        self.temp_video = "data/temp_video.mp4" 
        self.temp_audio = "data/temp_audio.mp3"

    class SilentLogger:
        """Tắt log rác của yt-dlp"""
        def debug(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass

    def process_content_pipeline(self, videos_data, config):
        """
        Quy trình xử lý A-Z: Tải -> Bóc băng -> Viết bài -> Tạo Ảnh/Video.
        Sử dụng yield để báo cáo log từng bước ra UI.
        """
        if not self.client:
            yield {"type": "error", "message": "Chưa có Gemini API Key!"}
            return

        # Tạo thư mục data nếu chưa có
        os.makedirs("data", exist_ok=True)

        combined_script = ""
        successful_count = 0
        total_in_tokens = 0
        total_out_tokens = 0
        
        yield {"type": "log", "message": "Bắt đầu tải và bóc băng video..."}

        # ==========================================
        # BƯỚC 1: TẢI & BÓC BĂNG VIDEO
        # ==========================================
        for idx, video in enumerate(videos_data, 1):
            if successful_count >= config.get('max_videos', 1):
                break
                
            yield {"type": "log", "message": f"B2: [yt-dlp] Đang tải video {idx}/{len(videos_data)}..."}
            if os.path.exists(self.temp_video): os.remove(self.temp_video)
            
            ydl_opts = {
                'outtmpl': self.temp_video, 
                'format': 'best', 
                'quiet': True, 
                'no_warnings': True,
                'logger': self.SilentLogger(),
                'nopart': True,
                'cookiefile': 'cookies.txt'
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl: 
                    ydl.download([video["link"]])
            except Exception as e:
                yield {"type": "log", "message": f"⚠️ Bỏ qua video {idx} do lỗi tải: {str(e)}"}
                continue

            if not os.path.exists(self.temp_video) or os.path.getsize(self.temp_video) == 0:
                yield {"type": "log", "message": f"⚠️ Bỏ qua video {idx} (File rỗng)"}
                continue

            yield {"type": "log", "message": f"B3: [MoviePy] Tách âm thanh video {successful_count + 1}..."}
            if os.path.exists(self.temp_audio): os.remove(self.temp_audio)
            
            try:
                video_clip = VideoFileClip(self.temp_video)
                audio_clip = video_clip.audio
                audio_clip.write_audiofile(self.temp_audio, logger=None)
                audio_clip.close()
                video_clip.close()
            except Exception as e:
                yield {"type": "log", "message": f"⚠️ Bỏ qua video {idx} do lỗi âm thanh: {e}"}
                continue

            yield {"type": "log", "message": f"B4: [{config.get('ai_model')}] Đang bóc băng video {successful_count + 1}..."}
            try:
                audio_file = self.client.files.upload(file=self.temp_audio)
                transcribe_resp = self.client.models.generate_content(
                    model=config.get('ai_model', 'gemini-2.5-flash'), 
                    contents=[audio_file, "Hãy nghe và gõ lại chính xác lời thoại thành văn bản. Nếu không có tiếng người, nói 'Không có lời thoại'."],
                )
                transcribed_text = transcribe_resp.text.strip()
                if getattr(transcribe_resp, 'usage_metadata', None):
                    total_in_tokens += getattr(transcribe_resp.usage_metadata, 'prompt_token_count', 0)
                    total_out_tokens += getattr(transcribe_resp.usage_metadata, 'candidates_token_count', 0)
            except Exception as e:
                transcribed_text = f"(Lỗi nhận diện giọng nói: {str(e)})"
            
            combined_script += f"--- VIDEO SỐ {successful_count + 1} ---\n- Tác giả: {video['creator']}\n- Mô tả: {video['desc']}\n- Lời thoại: {transcribed_text}\n\n"
            successful_count += 1

        # Dọn dẹp file tạm
        if os.path.exists(self.temp_video): os.remove(self.temp_video)
        if os.path.exists(self.temp_audio): os.remove(self.temp_audio)

        if successful_count == 0:
            yield {"type": "error", "message": "Tất cả video tìm được đều tải/bóc băng thất bại!"}
            return

        # ==========================================
        # BƯỚC 2: VIẾT BÀI FACEBOOK (ĐÃ NÂNG CẤP BỘ LỌC)
        # ==========================================
        yield {"type": "log", "message": f"B5: [{config.get('ai_model')}] Phân tích ngữ cảnh & Viết bài..."}

        
        # --- LẤY SYSTEM PROMPT NGƯỜI DÙNG TỰ CÀI ---
        default_sys_prompt = "Bạn là một Copywriter chuyên nghiệp. Nhiệm vụ duy nhất của bạn là viết bài đăng Facebook"
        system_prompt = config.get('system_prompt', default_sys_prompt)
        
        prompt = (
            f"{system_prompt}\n\n" # <--- CHÈN VÀO ĐÂY
            "TUYỆT ĐỐI KHÔNG lặp lại yêu cầu của tôi. KHÔNG giải thích. CHỈ TRẢ VỀ NỘI DUNG CÁC BÀI VIẾT.\n\n"
            f"Dữ liệu gốc từ {successful_count} video TikTok:\n{combined_script}\n"
            f"{config.get('doc_context', '')}\n" 
            f"YÊU CẦU: Viết ra ĐÚNG {config.get('count', 1)} BÀI ĐĂNG FACEBOOK FANPAGE.\n\n"
        )

        if config.get('target_topics'):
            prompt += f"**🎯 CHỦ ĐỀ:** Bẻ lái nội dung nhắm vào ngách: [{config['target_topics']}].\n"
        if config.get('ignore_keywords'):
            prompt += f"**⚠️ TỪ KHÓA CẤM KỴ:** KHÔNG dùng các từ: [{config['ignore_keywords']}].\n"
        if config.get('custom_prompt'):
            prompt += f"**💡 YÊU CẦU THÊM:** {config['custom_prompt']}\n"

        limit_text = f"Mỗi bài TỐI ĐA {config['word_limit']} từ. " if config.get('word_limit', 0) > 0 else ""
        prompt += (
            f"\n{limit_text}\n"
            "BẮT BUỘC PHÂN TÁCH các bài viết bằng đúng 3 dấu gạch đứng: |||\n"
            "KHÔNG ghi tiêu đề như 'Bài 1', 'Bài 2'. CHỈ ghi nội dung."
        )

        try:
            write_resp = self.client.models.generate_content(
                model=config.get('ai_model', 'gemini-2.5-flash'), 
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.8),
            )
            if getattr(write_resp, 'usage_metadata', None):
                total_in_tokens += getattr(write_resp.usage_metadata, 'prompt_token_count', 0)
                total_out_tokens += getattr(write_resp.usage_metadata, 'candidates_token_count', 0)
                
            raw_text = write_resp.text.strip()
            
            # --- BỘ LỌC LÀM SẠCH DỮ LIỆU ---
            raw_contents = raw_text.split("|||")
            generated_contents = []
            
            for text in raw_contents:
                cleaned_text = text.strip()
                if len(cleaned_text) > 30 and not cleaned_text.startswith("Bạn là một Copywriter"):
                    import re
                    cleaned_text = re.sub(r'^(?:\*\*|)?(?:Bài|Bài viết|Option|Biến thể) \d+[:\.\-]?(?:\*\*|)?\s*', '', cleaned_text, flags=re.IGNORECASE)
                    generated_contents.append(cleaned_text.strip())
            
            if len(generated_contents) > config.get('count', 1):
                generated_contents = generated_contents[:config.get('count', 1)]
                
            if not generated_contents:
                yield {"type": "error", "message": "AI không trả về bài viết nào hợp lệ hoặc sai định dạng phân tách."}
                return
                
            yield {"type": "log", "message": f"-> Đã chắp bút thành công {len(generated_contents)} bài viết!"}
            
        except Exception as e:
            yield {"type": "error", "message": f"Lỗi tạo nội dung: {str(e)}"}
            return

        # ==========================================
        # BƯỚC 3: TẠO MEDIA VÀ TRẢ VỀ DỮ LIỆU
        # ==========================================
        final_posts = []
        search_keyword = config.get('custom_trend', 'viral') 
        
        for idx, text_content in enumerate(generated_contents):
            image_save_path = ""
            video_save_path = ""
            
            # Sinh Video
            if config.get('gen_video'):
                yield {"type": "log", "message": f"🎬 B6: [Veo 3.1] Đang render Video bài số {idx + 1} (Mất khoảng 2-5 phút)..."}
                try:
                    summary_prompt = f"Write a highly detailed, cinematic video generation prompt in English for a Facebook post about: {search_keyword}. Context: {text_content[:200]}. Do not include text, typography or dialogue in the video prompt. Focus purely on visual descriptions."
                    veo_prompt_resp = self.client.models.generate_content(model="gemini-2.5-flash", contents=summary_prompt)
                    veo_prompt = veo_prompt_resp.text.strip()
                    
                    if config.get('veo_negative'):
                        veo_prompt += f"\n\nNegative prompt: {config['veo_negative']}"
                        
                    veo_config = {
                        "aspect_ratio": config.get('veo_aspect', '16:9'),
                        "resolution": config.get('veo_res', '720p'),
                        "durationSeconds": config.get('veo_duration', '8')
                    }
                    
                    operation = self.client.models.generate_videos(
                        model=config.get('veo_model', 'veo-3.1-generate-preview'),
                        prompt=veo_prompt,
                        config=veo_config
                    )
                    
                    while not operation.done:
                        yield {"type": "log", "message": f"-> [Veo 3.1] Vẫn đang render bài {idx + 1}... Vui lòng đợi..."}
                        time.sleep(10)
                        operation = self.client.operations.get(operation)
                        
                    generated_video = operation.response.generated_videos[0]
                    os.makedirs("data/video", exist_ok=True)
                    video_save_path = f"data/video/ai_video_{int(time.time())}_{idx}.mp4"
                    
                    self.client.files.download(file=generated_video.video)
                    generated_video.video.save(video_save_path)
                    yield {"type": "log", "message": f"✅ Đã render xong Video: {video_save_path}"}
                    
                except Exception as vid_err:
                    yield {"type": "log", "message": f"⚠️ Lỗi tạo Video: {str(vid_err)}"}
            
            # Sinh Ảnh
            elif config.get('gen_image'):
                yield {"type": "log", "message": f"B6: [Gemini Image] Đang vẽ ảnh minh họa bài số {idx + 1}..."}
                try:
                    summary_prompt = f"Write a short, highly descriptive image generation prompt in English for a Facebook post about: {search_keyword}. Context: {text_content[:200]}. Do not include any text in the image itself. High quality, professional photography style."
                    img_prompt_resp = self.client.models.generate_content(model="gemini-2.5-flash", contents=summary_prompt)
                    english_img_prompt = img_prompt_resp.text.strip()
                    
                    img_response = self.client.models.generate_content(
                        model="gemini-2.5-flash-image",
                        contents=english_img_prompt
                    )
                    
                    if getattr(img_response, "candidates", None) and hasattr(img_response.candidates[0].content.parts[0], "inline_data"):
                        img_bytes = img_response.candidates[0].content.parts[0].inline_data.data
                        os.makedirs("data/image", exist_ok=True)
                        image_save_path = f"data/image/ai_image_{int(time.time())}_{idx}.png"
                        
                        with open(image_save_path, "wb") as f:
                             f.write(img_bytes)
                        yield {"type": "log", "message": f"-> Đã vẽ xong ảnh: {image_save_path}"}
                        
                        logo_path = config.get('logo_path')
                        if logo_path and os.path.exists(logo_path):
                            yield {"type": "log", "message": "-> Đang đóng dấu Logo (Watermark)..."}
                            try:
                                base_img = Image.open(image_save_path).convert("RGBA")
                                watermark = Image.open(logo_path).convert("RGBA")
                                base_w, base_h = base_img.size
                                wm_w, wm_h = watermark.size
                                
                                scale_factor = int(config.get('logo_scale', 20)) / 100.0
                                new_wm_w = int(base_w * scale_factor)
                                new_wm_h = int(wm_h * (new_wm_w / wm_w))
                                watermark = watermark.resize((new_wm_w, new_wm_h), Image.Resampling.LANCZOS)
                                
                                opacity = int(config.get('logo_opacity', 100))
                                if opacity < 100:
                                    alpha = watermark.split()[3]
                                    alpha = alpha.point(lambda p: p * (opacity / 100.0))
                                    watermark.putalpha(alpha)
                                    
                                padding = 20 
                                pos_x, pos_y = 0, 0
                                pos_setting = config.get('logo_pos', 'Góc dưới Phải')
                                
                                if pos_setting == "Góc trên Trái": pos_x, pos_y = padding, padding
                                elif pos_setting == "Góc trên Phải": pos_x, pos_y = base_w - new_wm_w - padding, padding
                                elif pos_setting == "Góc dưới Trái": pos_x, pos_y = padding, base_h - new_wm_h - padding
                                elif pos_setting == "Góc dưới Phải": pos_x, pos_y = base_w - new_wm_w - padding, base_h - new_wm_h - padding
                                elif pos_setting == "Chính giữa": pos_x, pos_y = (base_w - new_wm_w) // 2, (base_h - new_wm_h) // 2
                                    
                                base_img.paste(watermark, (pos_x, pos_y), watermark)
                                base_img.convert("RGB").save(image_save_path)
                                yield {"type": "log", "message": "-> Đóng dấu Logo thành công! ✅"}
                            except Exception as wm_err:
                                yield {"type": "log", "message": f"⚠️ Lỗi đóng dấu Logo: {str(wm_err)}"}
                    else:
                        yield {"type": "log", "message": "⚠️ Lỗi: API không trả về ảnh."}
                except Exception as img_err:
                    yield {"type": "log", "message": f"⚠️ Lỗi vẽ ảnh: {str(img_err)}"}
                    
            # GOM DỮ LIỆU ĐỂ TRẢ VỀ CHO CONTROLLER
            final_posts.append({
                "content": text_content,
                "image_path": image_save_path,
                "video_path": video_save_path 
            })
        
        total_tokens = total_in_tokens + total_out_tokens
        yield {"type": "log", "message": f"🪙 [Chi phí Token] Tổng sử dụng Text: {total_tokens:,}"}
        
        # LỆNH NÀY CỰC KỲ QUAN TRỌNG: Gửi list final_posts ra ngoài
        yield {"type": "success", "data": final_posts}