import sqlite3
import os
import sys
from config.settings import DB_FILE
from models.post import ContentDraft
from datetime import datetime

# 1. Nhận diện chính xác thư mục gốc
if getattr(sys, 'frozen', False) or '__compiled__' in globals():
    # Khi đã build thành file .exe (Nuitka/PyInstaller)
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
else:
    # Khi đang chạy code Python trên VS Code 
    # (Vì file này nằm trong thư mục 'config', nên phải lùi 1 cấp ra thư mục gốc)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. Tạo thư mục data nằm ngay cạnh file .exe
data_dir = os.path.join(base_dir, 'data')
os.makedirs(data_dir, exist_ok=True)

# 3. Trỏ database vào thư mục data này
DB_FILE = os.path.join(data_dir, 'settings.db')
# ==========================================

class SettingsManager:
    def __init__(self):
        # Đảm bảo thư mục data tồn tại trước khi tạo DB
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        self.init_db()

    def init_db(self):
        """Khởi tạo các bảng trong CSDL nếu chưa có"""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS drafts (keyword TEXT, content TEXT, timestamp TEXT, image_path TEXT, video_path TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS queue_posts (time TEXT, keyword TEXT, content TEXT, image_path TEXT, video_path TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS history_posts (post_time TEXT, keyword TEXT, content TEXT, mode TEXT, image_path TEXT, video_path TEXT)''')
        
        # Cập nhật schema cho các bản cũ (Tự động thêm cột nếu thiếu)
        try: c.execute('ALTER TABLE drafts ADD COLUMN image_path TEXT')
        except: pass
        try: c.execute('ALTER TABLE drafts ADD COLUMN video_path TEXT')
        except: pass
        
        try: c.execute('ALTER TABLE queue_posts ADD COLUMN image_path TEXT')
        except: pass
        try: c.execute('ALTER TABLE queue_posts ADD COLUMN video_path TEXT')
        except: pass
        
        try: c.execute('ALTER TABLE history_posts ADD COLUMN image_path TEXT')
        except: pass
        try: c.execute('ALTER TABLE history_posts ADD COLUMN video_path TEXT')
        except: pass

        conn.commit()
        conn.close()

    # ==========================================
    # QUẢN LÝ CẤU HÌNH HỆ THỐNG (SETTINGS)
    # ==========================================
    def get_config(self):
        """Lấy toàn bộ cấu hình hệ thống trả về dạng Dictionary"""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT key, value FROM settings")
        settings_dict = dict(c.fetchall())
        conn.close()
        default_sys_prompt = "Bạn là một Copywriter chuyên nghiệp. Nhiệm vụ duy nhất của bạn là viết bài đăng Facebook.\nTUYỆT ĐỐI KHÔNG lặp lại yêu cầu của tôi. KHÔNG giải thích. CHỈ TRẢ VỀ NỘI DUNG CÁC BÀI VIẾT."
        
        # Cung cấp giá trị mặc định nếu chưa có trong DB
        return {
            "publish_immediately": settings_dict.get("publish_immediately", "1") == "1",
            "system_prompt": settings_dict.get("system_prompt", default_sys_prompt),
            "gemini_key": settings_dict.get("gemini_key", ""),
            "gemini_model": settings_dict.get("gemini_model", "gemini-2.5-flash"),
            "tiktok_api": settings_dict.get("tiktok_api", ""),
            "fb_id": settings_dict.get("fb_id", ""),
            "fb_token": settings_dict.get("fb_token", ""),
            "target_topics": settings_dict.get("target_topics", ""),
            "auto_az_times": settings_dict.get("auto_az_times", ""),
            "logo_path": settings_dict.get("logo_path", ""),
            "logo_pos": settings_dict.get("logo_pos", "Góc dưới Phải"),
            "logo_opacity": int(settings_dict.get("logo_opacity", "100")),
            "logo_scale": int(settings_dict.get("logo_scale", "20")),
            "run_on_startup": settings_dict.get("run_on_startup", "0") == "1",
            "veo_model": settings_dict.get("veo_model", "veo-3.1-generate-preview"),
            "veo_aspect": settings_dict.get("veo_aspect", "16:9"),
            "veo_res": settings_dict.get("veo_res", "720p"),
            "veo_duration": settings_dict.get("veo_duration", "8"),
            "veo_negative": settings_dict.get("veo_negative", ""),
            # --- 3 DÒNG MỚI THÊM VÀO ---
            "veo_style": settings_dict.get("veo_style", "Mặc định"),
            "veo_camera": settings_dict.get("veo_camera", "Mặc định"),
            "veo_ref_image": settings_dict.get("veo_ref_image", ""),
            
            "dash_keyword": settings_dict.get("dash_keyword", ""),
            "dash_max_videos": int(settings_dict.get("dash_max_videos", "1")),
            "dash_ai_count": int(settings_dict.get("dash_ai_count", "1")),
            "dash_topics": settings_dict.get("dash_topics", ""),
            "dash_doc_file": settings_dict.get("dash_doc_file", ""),
            "dash_custom_prompt": settings_dict.get("dash_custom_prompt", ""),
            "dash_ignore": settings_dict.get("dash_ignore", ""),
            "dash_word_limit": int(settings_dict.get("dash_word_limit", "0")),
            "dash_gen_image": settings_dict.get("dash_gen_image", "False"),
            "dash_gen_video": settings_dict.get("dash_gen_video", "False")
        }

    def save_config(self, config_dict):
        """Lưu lại các cấu hình hệ thống từ Dictionary"""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Tiền xử lý dữ liệu trước khi lưu (ép kiểu về chuỗi)
        config_to_save = config_dict.copy()
        if "run_on_startup" in config_to_save:
            config_to_save["run_on_startup"] = "1" if config_to_save["run_on_startup"] else "0"
            
        for k, v in config_to_save.items():
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, str(v)))
            
        conn.commit()
        conn.close()

    # ==========================================
    # QUẢN LÝ DỮ LIỆU BÀI VIẾT (DRAFTS, QUEUE, HISTORY)
    # ==========================================
    def get_drafts(self):
        """Tải danh sách bản nháp từ DB thành list các Object ContentDraft"""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        drafts = []
        try:
            for row in c.execute("SELECT keyword, content, timestamp, image_path, video_path FROM drafts"):
                drafts.append(ContentDraft(
                    keyword=row[0], content=row[1], timestamp=row[2], 
                    image_path=row[3], video_path=row[4]
                ))
        except sqlite3.OperationalError:
            pass
        conn.close()
        
        # Sắp xếp các bản nháp theo thứ tự mới nhất lên đầu
        def parse_timestamp(d):
            try:
                return datetime.strptime(d.timestamp, "%d/%m/%Y %H:%M:%S")
            except:
                return datetime.min

        drafts.sort(key=parse_timestamp, reverse=True)
        return drafts

    def save_drafts(self, drafts_list):
        """Xóa trắng bảng cũ và lưu danh sách bản nháp mới"""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM drafts")
        for d in drafts_list:
            c.execute("INSERT INTO drafts VALUES (?, ?, ?, ?, ?)", 
                     (d.keyword, d.content, d.timestamp, d.image_path, d.video_path))
        conn.commit()
        conn.close()

    def get_queue(self):
        """Tải danh sách hàng đợi (sắp xếp theo giờ tăng dần)"""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        queue = []
        try:
            for row in c.execute("SELECT time, keyword, content, image_path, video_path FROM queue_posts ORDER BY time ASC"):
                queue.append(ContentDraft(
                    time_queue=row[0], keyword=row[1], content=row[2], 
                    image_path=row[3], video_path=row[4]
                ))
        except sqlite3.OperationalError:
            pass
        conn.close()
        return queue

    def save_queue(self, queue_list):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM queue_posts")
        for q in queue_list:
            c.execute("INSERT INTO queue_posts VALUES (?, ?, ?, ?, ?)", 
                     (q.time_queue, q.keyword, q.content, q.image_path, q.video_path))
        conn.commit()
        conn.close()

    def get_history(self):
        """Tải lịch sử đăng bài (Trả về dict thuần để UI dễ hiển thị lên Table)"""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        history = []
        try:
            for row in c.execute("SELECT post_time, keyword, content, mode, image_path, video_path FROM history_posts"):
                history.append({
                    "post_time": row[0], "keyword": row[1], "content": row[2], 
                    "mode": row[3], "image_path": row[4], "video_path": row[5]
                })
        except sqlite3.OperationalError:
            pass
        conn.close()
        return history

    def add_history_record(self, post_time, keyword, content, mode, image_path="", video_path=""):
        """Thêm 1 record mới vào lịch sử, giới hạn 1000 dòng"""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO history_posts VALUES (?, ?, ?, ?, ?, ?)", 
                 (post_time, keyword, content, mode, image_path, video_path))
        
        # Tự động xóa các dòng cũ nếu vượt quá 1000 (Tránh làm nặng file DB)
        c.execute("""
            DELETE FROM history_posts 
            WHERE rowid NOT IN (
                SELECT rowid FROM history_posts ORDER BY rowid DESC LIMIT 1000
            )
        """)
        conn.commit()
        conn.close()