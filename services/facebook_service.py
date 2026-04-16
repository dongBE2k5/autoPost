# services/facebook_service.py
import os
import time
import requests

from datetime import datetime, timedelta, timezone
class FacebookService:
    def __init__(self, fb_id, fb_token):
        self.fb_id = fb_id
        self.fb_token = fb_token
        self.base_url = f"https://graph.facebook.com/v25.0/{self.fb_id}"

    def post_content(self, content, image_path="", video_path="", schedule_time_str=None, publish_immediately=True, log_cb=print):
        """
        Hàm xử lý đăng bài lên Facebook.
        """
        if not self.fb_id or not self.fb_token:
            raise Exception("Chưa cấu hình ID Facebook hoặc Token!")

        payload = {
            "access_token": self.fb_token
        }

        # --- LOGIC XỬ LÝ ĐĂNG NGAY HOẶC LÊN LỊCH ---
        if publish_immediately:
            payload["published"] = "true"
            log_cb("-> Chế độ: Đăng CÔNG KHAI ngay lập tức.")
        else:
            payload["published"] = "false"
            
            # Nếu chạy từ Hàng Đợi (có truyền giờ cụ thể)
            if schedule_time_str:
                now = datetime.now()
                target_time = datetime.strptime(schedule_time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
                if target_time < now:
                    target_time = target_time.replace(day=now.day + 1)
            else:
                # Mặc định lên lịch 7 ngày sau nếu chạy Auto A-Z
                target_time = datetime.now() + timedelta(days=7)
                
            unix_timestamp = int(target_time.timestamp())
            current_unix = int(time.time())
            
            # Facebook yêu cầu giờ lên lịch tối thiểu 10 phút tới tối đa 75 ngày
            if unix_timestamp - current_unix < 600:
                unix_timestamp = current_unix + 660 # Ép cộng thêm 11 phút cho an toàn
                
            payload["scheduled_publish_time"] = str(unix_timestamp)
            log_cb(f"-> Chế độ: LÊN LỊCH nháp cho lúc {datetime.fromtimestamp(unix_timestamp).strftime('%d/%m/%Y %H:%M')}")

        try:
            if video_path and os.path.exists(video_path):
                log_cb("-> Phát hiện Video, đang upload lên Facebook...")
                url = f"{self.base_url}/videos"
                payload["description"] = content
                with open(video_path, 'rb') as f:
                    response = requests.post(url, data=payload, files={'source': f})

            elif image_path and os.path.exists(image_path):
                log_cb("-> Phát hiện Ảnh, đang upload lên Facebook...")
                url = f"{self.base_url}/photos"
                payload["caption"] = content
                with open(image_path, 'rb') as f:
                    response = requests.post(url, data=payload, files={'source': f})
            else:
                log_cb("-> Đăng bài viết dạng văn bản (Text) lên Facebook...")
                url = f"{self.base_url}/feed"
                payload["message"] = content
                response = requests.post(url, data=payload)

            resp_json = response.json()
            
            if response.status_code == 200 and ("id" in resp_json or "post_id" in resp_json):
                post_id = resp_json.get("post_id", resp_json.get("id"))
                log_cb(f"✅ [Facebook API] Thao tác thành công! Post ID: {post_id}")
                return True
            else:
                err_msg = resp_json.get("error", {}).get("message", "Lỗi không xác định")
                raise Exception(f"Facebook API: {err_msg}")

        except Exception as e:
            log_cb(f"❌ Lỗi kết nối Facebook: {str(e)}")
            raise e
    def get_published_posts(self, limit=50):
        """Lấy danh sách các bài viết đã đăng trên Fanpage"""
        if not self.fb_id or not self.fb_token:
            raise Exception("Chưa cấu hình ID Facebook hoặc Token!")

        # Graph API endpoint lấy feed, bao gồm tin nhắn, thời gian tạo, id, và ảnh đính kèm (nếu có)
        url = f"https://graph.facebook.com/v25.0/{self.fb_id}/feed"
        params = {
            "access_token": self.fb_token,
            "fields": "id,message,created_time,full_picture,is_published,status_type",
            "limit": limit
        }

        try:
            response = requests.get(url, params=params)
            resp_json = response.json()

            if response.status_code == 200:
                return resp_json.get("data", [])
            else:
                err_msg = resp_json.get("error", {}).get("message", "Lỗi không xác định")
                raise Exception(f"Lỗi lấy bài viết: {err_msg}")
        except Exception as e:
            raise Exception(f"Lỗi kết nối Facebook: {str(e)}")

    def delete_post(self, post_id):
        """Xóa một bài viết trên Fanpage bằng ID"""
        if not self.fb_token:
            raise Exception("Chưa cấu hình Token!")

        url = f"https://graph.facebook.com/v25.0/{post_id}"
        params = {
            "access_token": self.fb_token
        }

        try:
            response = requests.delete(url, params=params)
            resp_json = response.json()

            if response.status_code == 200 and resp_json.get("success"):
                return True
            else:
                err_msg = resp_json.get("error", {}).get("message", "Lỗi không xác định")
                raise Exception(f"Lỗi xóa bài: {err_msg}")
        except Exception as e:
            raise Exception(f"Lỗi kết nối Facebook: {str(e)}")