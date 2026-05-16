# models/post.py

import json

class ContentDraft:
    """Mô hình dữ liệu lưu trữ một bài nháp (Draft) hoặc Hàng đợi (Queue)"""
    def __init__(self, keyword="", content="", image_path="", video_path="", timestamp="", time_queue="", token_usage=None, image_ids=None):
        self.keyword = keyword
        self.content = content
        # Support both single image_path (backward compatibility) and multiple image_ids
        self.image_path = image_path
        self.video_path = video_path
        # List of image IDs from user library (can be multiple)
        self.image_ids = image_ids or []
        
        # Dùng cho Draft (Thời gian tạo)
        self.timestamp = timestamp
        
        # Dùng cho Queue (Giờ sẽ đăng - VD: "15:30")
        self.time_queue = time_queue
        
        # Token tracking
        self.token_usage = token_usage or {}

    def to_dict(self):
        """Chuyển đổi thành Dict để dễ dàng tương thích với code cũ/Lưu DB"""
        return {
            "keyword": self.keyword,
            "content": self.content,
            "image_path": self.image_path,
            "video_path": self.video_path,
            "image_ids": json.dumps(self.image_ids) if self.image_ids else "",
            "timestamp": self.timestamp,
            "time": self.time_queue,
            "token_usage": self.token_usage
        }
    
    @staticmethod
    def from_dict(data):
        """Tạo ContentDraft từ Dict"""
        image_ids = []
        if data.get("image_ids"):
            try:
                image_ids = json.loads(data.get("image_ids", "[]"))
            except (json.JSONDecodeError, TypeError):
                image_ids = []
        
        return ContentDraft(
            keyword=data.get("keyword", ""),
            content=data.get("content", ""),
            image_path=data.get("image_path", ""),
            video_path=data.get("video_path", ""),
            timestamp=data.get("timestamp", ""),
            time_queue=data.get("time", ""),
            token_usage=data.get("token_usage", {}),
            image_ids=image_ids
        )