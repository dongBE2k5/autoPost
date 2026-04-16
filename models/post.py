# models/post.py

class ContentDraft:
    """Mô hình dữ liệu lưu trữ một bài nháp (Draft) hoặc Hàng đợi (Queue)"""
    def __init__(self, keyword="", content="", image_path="", video_path="", timestamp="", time_queue=""):
        self.keyword = keyword
        self.content = content
        self.image_path = image_path
        self.video_path = video_path
        
        # Dùng cho Draft (Thời gian tạo)
        self.timestamp = timestamp
        
        # Dùng cho Queue (Giờ sẽ đăng - VD: "15:30")
        self.time_queue = time_queue

    def to_dict(self):
        """Chuyển đổi thành Dict để dễ dàng tương thích với code cũ/Lưu DB"""
        return {
            "keyword": self.keyword,
            "content": self.content,
            "image_path": self.image_path,
            "video_path": self.video_path,
            "timestamp": self.timestamp,
            "time": self.time_queue
        }