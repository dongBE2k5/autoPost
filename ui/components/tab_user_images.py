# ui/components/tab_user_images.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QScrollArea, QGridLayout, QLabel, QFileDialog,
                             QMessageBox, QInputDialog)
from PySide6.QtCore import Qt, Signal, QSize, QThread
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QFrame
import os

class ImageThumbnailWidget(QFrame):
    """Widget hiển thị thumbnail ảnh"""
    delete_requested = Signal(str)  # image_id
    
    def __init__(self, user_image, parent=None):
        super().__init__(parent)
        self.user_image = user_image
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                background-color: #f8fafc;
            }
            QFrame:hover {
                border: 2px solid #3b82f6;
                background-color: #f0f7ff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Hiển thị ảnh
        img_label = QLabel()
        if os.path.exists(user_image.file_path):
            pixmap = QPixmap(user_image.file_path)
            pixmap = pixmap.scaledToWidth(150, Qt.TransformationMode.SmoothTransformation)
            img_label.setPixmap(pixmap)
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            img_label.setText("❌ File không tồn tại")
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_label.setStyleSheet("color: #ef4444; font-weight: bold;")
        
        layout.addWidget(img_label)
        
        # Tên file
        name_label = QLabel(user_image.file_name[:20] + "..." if len(user_image.file_name) > 20 else user_image.file_name)
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        # Kích thước file
        size_kb = user_image.file_size / 1024
        size_label = QLabel(f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB")
        size_label.setStyleSheet("color: #64748b; font-size: 11px;")
        size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(size_label)
        
        # Nút xóa
        btn_delete = QPushButton("🗑️ Xóa")
        btn_delete.setStyleSheet("background-color: #fee2e2; color: #ef4444; padding: 5px;")
        btn_delete.clicked.connect(self._on_delete_clicked)
        layout.addWidget(btn_delete)
        
        self.setMinimumSize(QSize(180, 250))
        self.setMaximumSize(QSize(200, 280))
    
    def _on_delete_clicked(self):
        reply = QMessageBox.warning(
            self,
            "Xác nhận xóa",
            f"Bạn chắc chắn muốn xóa ảnh '{self.user_image.file_name}' không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self.user_image.id)


class TabUserImages(QWidget):
    """Tab quản lý thư viện ảnh người dùng"""
    upload_requested = Signal(str)  # file_path
    delete_requested = Signal(str)  # image_id
    
    def __init__(self):
        super().__init__()
        self.image_service = None  # Sẽ được gắn từ Controller
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # --- Thanh công cụ ---
        toolbar_layout = QHBoxLayout()
        
        self.lbl_status = QLabel("📸 Thư Viện Ảnh")
        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b;")
        
        self.btn_upload = QPushButton("➕ Thêm Ảnh")
        self.btn_upload.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 10px 20px;")
        self.btn_upload.clicked.connect(self._on_upload_clicked)
        
        self.btn_refresh = QPushButton("🔄 Làm mới")
        self.btn_refresh.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 10px 20px;")
        self.btn_refresh.clicked.connect(self.refresh_images)
        
        toolbar_layout.addWidget(self.lbl_status)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_upload)
        toolbar_layout.addWidget(self.btn_refresh)
        layout.addLayout(toolbar_layout)
        
        # --- Khu vực hiển thị ảnh ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: #f8fafc;
            }
        """)
        
        self.images_container = QWidget()
        self.images_grid = QGridLayout(self.images_container)
        self.images_grid.setSpacing(15)
        self.images_grid.setContentsMargins(15, 15, 15, 15)
        
        scroll_area.setWidget(self.images_container)
        layout.addWidget(scroll_area)
        
        # --- Status bar ---
        self.lbl_count = QLabel("Chưa tải ảnh")
        self.lbl_count.setStyleSheet("color: #64748b; font-style: italic;")
        layout.addWidget(self.lbl_count)
    
    def set_image_service(self, service):
        """Gắn ImageLibraryService"""
        self.image_service = service
    
    def refresh_images(self):
        """Tải lại danh sách ảnh từ thư viện"""
        if not self.image_service:
            return
        
        # Xóa các widget cũ
        while self.images_grid.count():
            child = self.images_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Lấy danh sách ảnh
        images = self.image_service.get_all_images()
        
        if not images:
            empty_label = QLabel("📭 Chưa có ảnh nào. Hãy thêm ảnh mới!")
            empty_label.setStyleSheet("color: #94a3b8; font-size: 14px; padding: 40px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.images_grid.addWidget(empty_label, 0, 0)
            self.lbl_count.setText("Tổng cộng: 0 ảnh")
        else:
            # Thêm thumbnail vào grid
            row = 0
            col = 0
            for image in images:
                thumb = ImageThumbnailWidget(image)
                thumb.delete_requested.connect(self._on_image_delete_requested)
                self.images_grid.addWidget(thumb, row, col)
                
                col += 1
                if col >= 3:  # 3 ảnh trên 1 hàng
                    col = 0
                    row += 1
            
            # Cộng số ảnh
            self.lbl_count.setText(f"Tổng cộng: {len(images)} ảnh")
    
    def _on_upload_clicked(self):
        """Xử lý sự kiện upload ảnh"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn ảnh để thêm vào thư viện",
            "",
            "Hình ảnh (*.png *.jpg *.jpeg *.bmp *.webp);;Tất cả file (*)"
        )
        
        if file_path:
            self.upload_requested.emit(file_path)
    
    def _on_image_delete_requested(self, image_id):
        """Xử lý sự kiện xóa ảnh"""
        self.delete_requested.emit(image_id)
    
    def show_success_message(self, title, message):
        """Hiển thị thông báo thành công"""
        QMessageBox.information(self, title, message)
    
    def show_error_message(self, title, message):
        """Hiển thị thông báo lỗi"""
        QMessageBox.critical(self, title, message)
