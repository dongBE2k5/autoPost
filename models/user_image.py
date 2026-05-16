# models/user_image.py
import os
from datetime import datetime


class UserImage:
    """Model để lưu trữ thông tin ảnh của người dùng"""
    
    def __init__(self, file_path, file_name=None, upload_date=None, file_size=None, image_id=None):
        self.id = image_id or os.path.basename(file_path)
        self.file_path = file_path
        self.file_name = file_name or os.path.basename(file_path)
        self.upload_date = upload_date or datetime.now().isoformat()
        self.file_size = file_size or (os.path.getsize(file_path) if os.path.exists(file_path) else 0)
    
    def to_dict(self):
        """Chuyển đổi thành Dict để lưu vào DB"""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "upload_date": self.upload_date,
            "file_size": self.file_size
        }
    
    @staticmethod
    def from_dict(data):
        """Tạo UserImage từ Dict"""
        return UserImage(
            file_path=data.get("file_path"),
            file_name=data.get("file_name"),
            upload_date=data.get("upload_date"),
            file_size=data.get("file_size"),
            image_id=data.get("id")
        )
