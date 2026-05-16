# ui/dialogs/user_image_selector.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QScrollArea, QGridLayout, QLabel, QCheckBox,
                             QRadioButton, QButtonGroup, QFrame, QWidget)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap
from config.settings import MODERN_STYLE


class ImageSelectorThumbnail(QFrame):
    """Widget hiển thị thumbnail ảnh trong dialog chọn"""
    toggled = Signal(str, bool)  # image_id, is_selected
    
    def __init__(self, user_image, is_multi_select=False, parent=None):
        super().__init__(parent)
        self.user_image = user_image
        self.is_multi_select = is_multi_select
        self.is_selected = False
        
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.update_style()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Checkbox/Radio button
        select_layout = QHBoxLayout()
        if is_multi_select:
            self.checkbox = QCheckBox()
            self.checkbox.toggled.connect(self._on_toggled)
            select_layout.addWidget(self.checkbox)
        else:
            self.radio = QRadioButton()
            self.radio.toggled.connect(self._on_toggled)
            select_layout.addWidget(self.radio)
        select_layout.addStretch()
        layout.addLayout(select_layout)
        
        # Hiển thị ảnh
        import os
        img_label = QLabel()
        if os.path.exists(user_image.file_path):
            pixmap = QPixmap(user_image.file_path)
            pixmap = pixmap.scaledToWidth(120, Qt.TransformationMode.SmoothTransformation)
            img_label.setPixmap(pixmap)
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            img_label.setText("❌")
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 24px;")
        
        layout.addWidget(img_label)
        
        # Tên file
        name_label = QLabel(user_image.file_name[:15] + "..." if len(user_image.file_name) > 15 else user_image.file_name)
        name_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        self.setMinimumSize(QSize(150, 200))
        self.setMaximumSize(QSize(160, 220))
    
    def _on_toggled(self, checked):
        self.is_selected = checked
        self.update_style()
        self.toggled.emit(self.user_image.id, checked)
    
    def update_style(self):
        if self.is_selected:
            self.setStyleSheet("""
                QFrame {
                    border: 3px solid #3b82f6;
                    border-radius: 8px;
                    background-color: #eff6ff;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    background-color: #f8fafc;
                }
                QFrame:hover {
                    border: 2px solid #cbd5e1;
                    background-color: #f1f5f9;
                }
            """)
    
    def set_selected(self, selected):
        self.is_selected = selected
        if self.is_multi_select:
            self.checkbox.setChecked(selected)
        else:
            self.radio.setChecked(selected)
        self.update_style()
    
    def get_selected(self):
        if self.is_multi_select:
            return self.checkbox.isChecked()
        else:
            return self.radio.isChecked()


class UserImageSelectorDialog(QDialog):
    """Dialog cho phép người dùng chọn ảnh từ thư viện"""
    
    def __init__(self, image_service, multi_select=False, parent=None):
        super().__init__(parent)
        self.image_service = image_service
        self.multi_select = multi_select
        self.selected_images = []
        
        self.setWindowTitle("📸 Chọn Ảnh từ Thư Viện" if multi_select else "📸 Chọn Ảnh")
        self.resize(800, 600)
        self.setStyleSheet(MODERN_STYLE)
        
        self.initUI()
        self.load_images()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # Tiêu đề
        title_label = QLabel("📸 Chọn Ảnh từ Thư Viện")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b;")
        layout.addWidget(title_label)
        
        # Khu vực hiển thị ảnh
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
        self.images_grid.setSpacing(12)
        self.images_grid.setContentsMargins(12, 12, 12, 12)
        
        scroll_area.setWidget(self.images_container)
        layout.addWidget(scroll_area)
        
        # Các nút điều khiển
        button_layout = QHBoxLayout()
        
        self.btn_cancel = QPushButton("❌ Hủy bỏ")
        self.btn_cancel.setStyleSheet("background-color: #f3f4f6; color: #374151; padding: 10px 20px; border-radius: 5px;")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("✅ Xác nhận")
        self.btn_ok.setStyleSheet("background-color: #10b981; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;")
        self.btn_ok.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_ok)
        layout.addLayout(button_layout)
    
    def load_images(self):
        """Tải ảnh từ thư viện"""
        images = self.image_service.get_all_images()
        
        if not images:
            empty_label = QLabel("📭 Chưa có ảnh nào trong thư viện")
            empty_label.setStyleSheet("color: #94a3b8; font-size: 14px; padding: 40px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.images_grid.addWidget(empty_label, 0, 0)
        else:
            row = 0
            col = 0
            for image in images:
                thumb = ImageSelectorThumbnail(image, self.multi_select)
                thumb.toggled.connect(self._on_image_toggled)
                self.images_grid.addWidget(thumb, row, col)
                
                col += 1
                if col >= 4:  # 4 ảnh trên 1 hàng
                    col = 0
                    row += 1
    
    def _on_image_toggled(self, image_id, is_selected):
        """Xử lý sự kiện chọn/bỏ chọn ảnh"""
        if is_selected:
            if image_id not in self.selected_images:
                if not self.multi_select and self.selected_images:
                    # Nếu là single select, xóa lựa chọn cũ
                    self.selected_images = [image_id]
                else:
                    self.selected_images.append(image_id)
        else:
            if image_id in self.selected_images:
                self.selected_images.remove(image_id)
    
    def get_selected_images(self):
        """Lấy danh sách ảnh đã chọn"""
        return self.selected_images
    
    def get_selected_image(self):
        """Lấy ảnh đã chọn (cho single select)"""
        return self.selected_images[0] if self.selected_images else None
