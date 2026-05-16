# services/image_library_service.py
import os
import shutil
import sqlite3
from datetime import datetime
from PIL import Image
from config.settings_manager import DB_FILE
from models.user_image import UserImage

# ==========================================
# 1. ĐỊNH TUYẾN ĐƯỜNG DẪN PORTABLE CHUẨN
# ==========================================
import sys
if getattr(sys, 'frozen', False) or '__compiled__' in globals():
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

data_dir = os.path.join(base_dir, 'data')
user_images_dir = os.path.join(data_dir, 'user_images')
os.makedirs(user_images_dir, exist_ok=True)
# ==========================================


class ImageLibraryService:
    """Service quản lý thư viện ảnh người dùng"""
    
    def __init__(self):
        self.user_images_dir = user_images_dir
    
    def upload_image(self, source_file_path):
        """
        Upload ảnh từ máy của người dùng vào thư viện
        
        Args:
            source_file_path: Đường dẫn file ảnh gốc
        
        Returns:
            UserImage object nếu thành công, None nếu thất bại
        """
        try:
            if not os.path.exists(source_file_path):
                raise FileNotFoundError(f"File không tồn tại: {source_file_path}")
            
            # Kiểm tra định dạng ảnh
            try:
                img = Image.open(source_file_path)
                img.verify()
            except Exception as e:
                raise ValueError(f"File không phải hình ảnh hợp lệ: {e}")
            
            # Tạo tên file duy nhất (timestamp + tên gốc)
            file_name = os.path.basename(source_file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
            unique_filename = timestamp + file_name
            
            # Đường dẫn đích
            dest_path = os.path.join(self.user_images_dir, unique_filename)
            
            # Copy file
            shutil.copy2(source_file_path, dest_path)
            
            # Tạo UserImage object
            user_image = UserImage(
                file_path=dest_path,
                file_name=file_name,
                upload_date=datetime.now().isoformat(),
                file_size=os.path.getsize(dest_path),
                image_id=unique_filename
            )
            
            # Lưu vào DB
            self._save_to_db(user_image)
            
            return user_image
        
        except Exception as e:
            print(f"❌ Lỗi upload ảnh: {e}")
            return None
    
    def delete_image(self, image_id):
        """Xóa ảnh khỏi thư viện"""
        try:
            # Lấy thông tin ảnh từ DB
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT file_path FROM user_images WHERE id = ?", (image_id,))
            result = c.fetchone()
            conn.close()
            
            if not result:
                raise ValueError(f"Ảnh không tồn tại: {image_id}")
            
            file_path = result[0]
            
            # Xóa file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Xóa từ DB
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("DELETE FROM user_images WHERE id = ?", (image_id,))
            conn.commit()
            conn.close()
            
            return True
        
        except Exception as e:
            print(f"❌ Lỗi xóa ảnh: {e}")
            return False
    
    def get_all_images(self):
        """Lấy danh sách tất cả ảnh"""
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT id, file_path, file_name, upload_date, file_size FROM user_images ORDER BY upload_date DESC")
            results = c.fetchall()
            conn.close()
            
            images = []
            for row in results:
                image_data = {
                    "id": row[0],
                    "file_path": row[1],
                    "file_name": row[2],
                    "upload_date": row[3],
                    "file_size": row[4]
                }
                images.append(UserImage.from_dict(image_data))
            
            return images
        
        except Exception as e:
            print(f"❌ Lỗi lấy danh sách ảnh: {e}")
            return []
    
    def get_image_by_id(self, image_id):
        """Lấy ảnh theo ID"""
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT id, file_path, file_name, upload_date, file_size FROM user_images WHERE id = ?", (image_id,))
            result = c.fetchone()
            conn.close()
            
            if not result:
                return None
            
            image_data = {
                "id": result[0],
                "file_path": result[1],
                "file_name": result[2],
                "upload_date": result[3],
                "file_size": result[4]
            }
            return UserImage.from_dict(image_data)
        
        except Exception as e:
            print(f"❌ Lỗi lấy ảnh: {e}")
            return None
    
    def _save_to_db(self, user_image):
        """Lưu thông tin ảnh vào database"""
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("""
                INSERT INTO user_images (id, file_path, file_name, upload_date, file_size)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_image.id,
                user_image.file_path,
                user_image.file_name,
                user_image.upload_date,
                user_image.file_size
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Lỗi lưu vào DB: {e}")
    
    def get_images_by_ids(self, image_ids):
        """Lấy danh sách ảnh theo IDs"""
        try:
            images = []
            for image_id in image_ids:
                image = self.get_image_by_id(image_id)
                if image:
                    images.append(image)
            return images
        except Exception as e:
            print(f"❌ Lỗi lấy danh sách ảnh: {e}")
            return []
    
    def get_image_thumbnail(self, image_id, thumb_size=(150, 150)):
        """Lấy thumbnail của ảnh (dùng cho preview)"""
        try:
            image = self.get_image_by_id(image_id)
            if not image or not os.path.exists(image.file_path):
                return None
            
            img = Image.open(image.file_path)
            img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
            
            return img
        except Exception as e:
            print(f"❌ Lỗi tạo thumbnail: {e}")
            return None
