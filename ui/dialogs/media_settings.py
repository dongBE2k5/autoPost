# ui/dialogs/media_settings.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QComboBox, QSpinBox, QFileDialog,
                             QGroupBox)
from config.settings import MODERN_STYLE

class VideoSettingsDialog(QDialog):
    # Đã thêm các tham số mới: style, camera, ref_image
    def __init__(self, model, aspect, res, duration, negative, style="Mặc định", camera="Mặc định", ref_image="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎥 Cài đặt Video AI Chuyên Sâu (Veo 3.1)")
        self.resize(650, 500) # Tăng kích thước cửa sổ để chứa thêm nút
        self.setStyleSheet(MODERN_STYLE)

        layout = QVBoxLayout(self)

        # ==========================================
        # 1. CẤU HÌNH KỸ THUẬT CƠ BẢN
        # ==========================================
        tech_group = QGroupBox("⚙️ Thông số Kỹ thuật")
        tech_layout = QVBoxLayout()
        
        row_model = QHBoxLayout()
        self.combo_model = QComboBox()
        self.combo_model.addItems(["veo-3.1-generate-preview", "veo-3.1-lite-preview"])
        self.combo_model.setCurrentText(model)
        row_model.addWidget(QLabel("Mô hình Video:"))
        row_model.addWidget(self.combo_model, stretch=1)
        tech_layout.addLayout(row_model)

        row_format = QHBoxLayout()
        self.combo_aspect = QComboBox()
        self.combo_aspect.addItems(["16:9", "9:16"])
        self.combo_aspect.setCurrentText(aspect)
        row_format.addWidget(QLabel("Tỷ lệ khung hình:"))
        row_format.addWidget(self.combo_aspect, stretch=1)
        
        self.combo_res = QComboBox()
        self.combo_res.addItems(["720p", "1080p", "4k"])
        self.combo_res.setCurrentText(res)
        row_format.addWidget(QLabel("Độ phân giải:"))
        row_format.addWidget(self.combo_res, stretch=1)
        tech_layout.addLayout(row_format)

        row_duration = QHBoxLayout()
        self.combo_duration = QComboBox()
        self.combo_duration.addItems(["4", "6", "8"])
        self.combo_duration.setCurrentText(duration)
        row_duration.addWidget(QLabel("Thời lượng (giây):"))
        row_duration.addWidget(self.combo_duration, stretch=1)
        lbl_hint = QLabel("<i>*Lưu ý: 1080p & 4k bắt buộc là 8s</i>")
        lbl_hint.setStyleSheet("color: #64748b;")
        row_duration.addWidget(lbl_hint)
        tech_layout.addLayout(row_duration)
        
        tech_group.setLayout(tech_layout)
        layout.addWidget(tech_group)

        # ==========================================
        # 2. CẤU HÌNH BỐI CẢNH & PHONG CÁCH (NÂNG CẤP)
        # ==========================================
        context_group = QGroupBox("🎨 Bối cảnh & Đạo diễn (Context & Style)")
        context_layout = QVBoxLayout()

        row_style = QHBoxLayout()
        self.combo_style = QComboBox()
        self.combo_style.addItems([
            "Mặc định", "Cinematic (Điện ảnh)", "Photorealistic (Siêu thực)", 
            "3D Animation (Hoạt hình 3D)", "Anime/Manga", "Cyberpunk", "Vintage/Retro"
        ])
        self.combo_style.setCurrentText(style)
        row_style.addWidget(QLabel("Phong cách:"))
        row_style.addWidget(self.combo_style, stretch=1)

        self.combo_camera = QComboBox()
        self.combo_camera.addItems([
            "Mặc định", "Slow Motion (Quay chậm)", "Macro (Cận cảnh chi tiết)", 
            "Drone/Aerial (Góc quay từ trên cao)", "Panning (Lướt ngang)", "Zoom In"
        ])
        self.combo_camera.setCurrentText(camera)
        row_style.addWidget(QLabel("Góc máy:"))
        row_style.addWidget(self.combo_camera, stretch=1)
        context_layout.addLayout(row_style)

        # Tùy chọn chèn Ảnh Tham Chiếu (Dành cho Veo)
        row_ref = QHBoxLayout()
        self.input_ref_image = QLineEdit(ref_image)
        self.input_ref_image.setPlaceholderText("Ảnh tham chiếu (Tùy chọn - Giúp AI giữ đúng hình ảnh SP)")
        btn_browse_ref = QPushButton("📁 Chọn Ảnh")
        btn_browse_ref.clicked.connect(self.browse_ref_image)
        btn_clear_ref = QPushButton("❌")
        btn_clear_ref.clicked.connect(self.input_ref_image.clear)
        row_ref.addWidget(QLabel("Ảnh tham chiếu:"))
        row_ref.addWidget(self.input_ref_image, stretch=1)
        row_ref.addWidget(btn_browse_ref)
        row_ref.addWidget(btn_clear_ref)
        context_layout.addLayout(row_ref)

        context_group.setLayout(context_layout)
        layout.addWidget(context_group)

        # ==========================================
        # 3. NỘI DUNG CẤM
        # ==========================================
        layout.addWidget(QLabel("🚫 Nội dung cần tránh trong Video (Negative Prompt):"))
        self.input_negative = QTextEdit()
        self.input_negative.setPlainText(negative)
        self.input_negative.setPlaceholderText("Ghi bằng tiếng Anh. VD: text, watermark, bad anatomy, blurry...")
        self.input_negative.setMaximumHeight(60)
        layout.addWidget(self.input_negative)

        # ==========================================
        # NÚT ĐIỀU KHIỂN
        # ==========================================
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾 Lưu Cài Đặt Video")
        btn_save.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold; padding: 8px 15px;")
        btn_save.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)

    def browse_ref_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn Ảnh Tham Chiếu", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.input_ref_image.setText(file_path)

    def get_settings(self):
        # Trả về TẤT CẢ các thông số bao gồm cả các cài đặt nâng cao
        return (
            self.combo_model.currentText(), 
            self.combo_aspect.currentText(), 
            self.combo_res.currentText(), 
            self.combo_duration.currentText(), 
            self.input_negative.toPlainText().strip(),
            self.combo_style.currentText(),         # Mới thêm
            self.combo_camera.currentText(),        # Mới thêm
            self.input_ref_image.text().strip()     # Mới thêm
        )


class LogoSettingsDialog(QDialog):
    # (Phần này giữ nguyên code cũ của bạn)
    def __init__(self, path, pos, opacity, scale, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🖼️ Cài đặt Logo / Watermark")
        self.resize(550, 300)
        self.setStyleSheet(MODERN_STYLE)

        layout = QVBoxLayout(self)

        row_file = QHBoxLayout()
        self.input_file = QLineEdit(path)
        self.input_file.setPlaceholderText("Đường dẫn file Logo (.png nền trong suốt)")
        btn_browse = QPushButton("📁 Chọn Logo")
        btn_browse.clicked.connect(self.browse_logo)
        btn_clear = QPushButton("❌")
        btn_clear.clicked.connect(self.input_file.clear)
        row_file.addWidget(QLabel("File Logo:"))
        row_file.addWidget(self.input_file, stretch=1)
        row_file.addWidget(btn_browse)
        row_file.addWidget(btn_clear)
        layout.addLayout(row_file)

        row_pos = QHBoxLayout()
        self.combo_pos = QComboBox()
        self.combo_pos.addItems(["Góc dưới Phải", "Góc dưới Trái", "Góc trên Phải", "Góc trên Trái", "Chính giữa"])
        self.combo_pos.setCurrentText(pos)
        row_pos.addWidget(QLabel("Vị trí đóng dấu:"))
        row_pos.addWidget(self.combo_pos, stretch=1)
        layout.addLayout(row_pos)

        row_scale = QHBoxLayout()
        self.spin_scale = QSpinBox()
        self.spin_scale.setRange(5, 100)
        self.spin_scale.setValue(int(scale))
        self.spin_scale.setSuffix(" % (so với ảnh gốc)")
        row_scale.addWidget(QLabel("Kích thước Logo:"))
        row_scale.addWidget(self.spin_scale, stretch=1)
        layout.addLayout(row_scale)

        row_opacity = QHBoxLayout()
        self.spin_opacity = QSpinBox()
        self.spin_opacity.setRange(10, 100)
        self.spin_opacity.setValue(int(opacity))
        self.spin_opacity.setSuffix(" % (Độ rõ nét)")
        row_opacity.addWidget(QLabel("Độ mờ (Opacity):"))
        row_opacity.addWidget(self.spin_opacity, stretch=1)
        layout.addLayout(row_opacity)

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾 Lưu Cài Đặt Logo")
        btn_save.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addStretch()
        layout.addLayout(btn_layout)

    def browse_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file Logo", "", "Images (*.png *.jpg *.jpeg);;All Files (*)")
        if file_path:
            self.input_file.setText(file_path)

    def get_settings(self):
        return self.input_file.text(), self.combo_pos.currentText(), self.spin_opacity.value(), self.spin_scale.value()


class ImageSettingsDialog(QDialog):
    def __init__(self, aspect="1:1", style="Mặc định", subject="", action="", lighting="", camera="", context="", parent=None, image_paths=None):
        super().__init__(parent)
        self.setWindowTitle("🎨 Cài đặt Tạo Hình Ảnh AI (Imagen 3)")
        self.resize(600, 600)
        self.setStyleSheet(MODERN_STYLE)
        
        self.selected_image_paths = image_paths or []  # Lưu list file paths

        layout = QVBoxLayout(self)

        # 1. Tỷ lệ & Phong cách
        basic_group = QGroupBox("⚙️ Cơ bản")
        basic_layout = QVBoxLayout()
        
        row_aspect = QHBoxLayout()
        self.combo_aspect = QComboBox()
        self.combo_aspect.addItems(["1:1", "16:9", "9:16", "4:3", "3:4"])
        self.combo_aspect.setCurrentText(aspect)
        row_aspect.addWidget(QLabel("Tỷ lệ khung hình:"))
        row_aspect.addWidget(self.combo_aspect, stretch=1)
        
        self.combo_style = QComboBox()
        self.combo_style.addItems([
            "Mặc định", "Photorealistic (Ảnh chụp siêu thực)", "Cinematic (Điện ảnh chuyên nghiệp)", 
            "3D Render (Đồ họa 3D)", "Anime (Hoạt hình Nhật Bản)", "Digital Art (Nghệ thuật số)", 
            "Oil Painting (Tranh sơn dầu)", "Watercolor (Tranh màu nước)"
        ])
        self.combo_style.setCurrentText(style)
        row_aspect.addWidget(QLabel("Phong cách:"))
        row_aspect.addWidget(self.combo_style, stretch=1)
        basic_layout.addLayout(row_aspect)
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 2. Chi tiết nâng cao (Manual Prompting)
        adv_group = QGroupBox("🎭 Chi tiết nội dung (Tùy chọn)")
        from PySide6.QtWidgets import QFormLayout
        adv_layout = QFormLayout()
        adv_layout.setSpacing(10)
        
        # --- Chủ thể ---
        row_subject = QHBoxLayout()
        self.combo_subject = QComboBox()
        self.combo_subject.addItems([
            "-- Chọn --", 
            "Phụ nữ trẻ", "Đàn ông trẻ", "Gia đình", " Cặp đôi", 
            "Trẻ em", "Người cao tuổi", "Nhóm bạn",
            "Sản phẩm thời trang", "Phụ kiện", "Sản phẩm công nghệ", 
            "Thực phẩm/Đồ ăn", "Mỹ phẩm", "Nội thất", "Phương tiện",
            "Khác"
        ])
        self.subject_custom = QLineEdit(subject)
        self.subject_custom.setPlaceholderText("Nhập tùy chỉnh...")
        self.subject_custom.setVisible(False)
        # Kết nối signal trước khi setCurrentText
        self.combo_subject.currentTextChanged.connect(self._on_subject_changed)
        # Nếu giá trị không tìm thấy trong dropdown, select "Khác"
        if subject and subject != "-- Chọn --":
            self.combo_subject.setCurrentText(subject)
            if self.combo_subject.currentText() != subject:  # Không tìm thấy
                self.combo_subject.setCurrentText("Khác")
                self.subject_custom.setVisible(True)
        row_subject.addWidget(self.combo_subject, stretch=1)
        row_subject.addWidget(self.subject_custom, stretch=1)
        adv_layout.addRow("Chủ thể:", row_subject)

        # --- Hành động ---
        row_action = QHBoxLayout()
        self.combo_action = QComboBox()
        self.combo_action.addItems([
            "-- Chọn --", "Mỉm cười rạng rỡ", "Tính toán suy nghĩ", "Gõ bàn phím", 
            "Chạy nhanh", "Nằm yên tĩnh", "Ngồi yên tĩnh", "Nhảy vui vẻ",
            "Được trưng bày", "Đang sử dụng", "Đang làm sạch", "Được xếp gọn","Không Có",
            "Khác"
        ])
        self.action_custom = QLineEdit(action)
        self.action_custom.setPlaceholderText("Nhập tùy chỉnh...")
        self.action_custom.setVisible(False)
        # Kết nối signal trước khi setCurrentText
        self.combo_action.currentTextChanged.connect(self._on_action_changed)
        # Nếu giá trị không tìm thấy trong dropdown, select "Khác"
        if action and action != "-- Chọn --":
            self.combo_action.setCurrentText(action)
            if self.combo_action.currentText() != action:  # Không tìm thấy
                self.combo_action.setCurrentText("Khác")
                self.action_custom.setVisible(True)
        row_action.addWidget(self.combo_action, stretch=1)
        row_action.addWidget(self.action_custom, stretch=1)
        adv_layout.addRow("Hành động:", row_action)

        # --- Ánh sáng/Màu ---
        row_lighting = QHBoxLayout()
        self.combo_lighting = QComboBox()
        self.combo_lighting.addItems([
            "-- Chọn --", "Ánh sáng điện ảnh", "Giờ vàng", "Màu sắc rực rỡ", 
            "Ánh sáng tự nhiên", "Ánh sáng studio", "Mịn nhẹ", "Tương phản cao", "Khác"
        ])
        self.lighting_custom = QLineEdit(lighting)
        self.lighting_custom.setPlaceholderText("Nhập tùy chỉnh...")
        self.lighting_custom.setVisible(False)
        # Kết nối signal trước khi setCurrentText
        self.combo_lighting.currentTextChanged.connect(self._on_lighting_changed)
        # Nếu giá trị không tìm thấy trong dropdown, select "Khác"
        if lighting and lighting != "-- Chọn --":
            self.combo_lighting.setCurrentText(lighting)
            if self.combo_lighting.currentText() != lighting:  # Không tìm thấy
                self.combo_lighting.setCurrentText("Khác")
                self.lighting_custom.setVisible(True)
        row_lighting.addWidget(self.combo_lighting, stretch=1)
        row_lighting.addWidget(self.lighting_custom, stretch=1)
        adv_layout.addRow("Ánh sáng/Màu:", row_lighting)

        # --- Góc máy ---
        row_camera = QHBoxLayout()
        self.combo_camera = QComboBox()
        self.combo_camera.addItems([
            "-- Chọn --", "Cận cảnh chi tiết", "Toàn cảnh rộng", "Góc nhìn trung bình", 
            "Góc nhìn thấp", "Góc nhìn cao", "Nhìn từ trên cao", "Khác"
        ])
        self.camera_custom = QLineEdit(camera)
        self.camera_custom.setPlaceholderText("Nhập tùy chỉnh...")
        self.camera_custom.setVisible(False)
        # Kết nối signal trước khi setCurrentText
        self.combo_camera.currentTextChanged.connect(self._on_camera_changed)
        # Nếu giá trị không tìm thấy trong dropdown, select "Khác"
        if camera and camera != "-- Chọn --":
            self.combo_camera.setCurrentText(camera)
            if self.combo_camera.currentText() != camera:  # Không tìm thấy
                self.combo_camera.setCurrentText("Khác")
                self.camera_custom.setVisible(True)
        row_camera.addWidget(self.combo_camera, stretch=1)
        row_camera.addWidget(self.camera_custom, stretch=1)
        adv_layout.addRow("Góc máy:", row_camera)

        # --- Bối cảnh ---
        row_context = QHBoxLayout()
        self.combo_context = QComboBox()
        self.combo_context.addItems([
            "-- Chọn --", "Quán cà phê", "Văn phòng", "Nhà", "Đường phố", 
            "Biển", "Rừng", "Thành phố", "Khác"
        ])
        self.context_custom = QLineEdit(context)
        self.context_custom.setPlaceholderText("Nhập tùy chỉnh...")
        self.context_custom.setVisible(False)
        # Kết nối signal trước khi setCurrentText
        self.combo_context.currentTextChanged.connect(self._on_context_changed)
        # Nếu giá trị không tìm thấy trong dropdown, select "Khác"
        if context and context != "-- Chọn --":
            self.combo_context.setCurrentText(context)
            if self.combo_context.currentText() != context:  # Không tìm thấy
                self.combo_context.setCurrentText("Khác")
                self.context_custom.setVisible(True)
        row_context.addWidget(self.combo_context, stretch=1)
        row_context.addWidget(self.context_custom, stretch=1)
        adv_layout.addRow("Bối cảnh:", row_context)

        adv_group.setLayout(adv_layout)
        layout.addWidget(adv_group)

        # 3. Ghi chú
        lbl_hint = QLabel("<i>*Lưu ý: Chọn 'Khác' để nhập tùy chỉnh. Các ô để trống AI sẽ tự động sáng tạo.</i>")
        lbl_hint.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(lbl_hint)
        
        # 4. Chọn ảnh từ thư viện người dùng
        user_image_group = QGroupBox("📸 Sử dụng Ảnh Người Dùng (Hỗ trợ nhiều ảnh)")
        user_image_layout = QVBoxLayout()
        user_image_layout.setSpacing(12)
        
        btn_row = QHBoxLayout()
        btn_select_user_image = QPushButton("📸 Thêm ảnh từ máy")
        btn_select_user_image.setMinimumHeight(40)
        btn_select_user_image.setStyleSheet("background-color: #06b6d4; color: white; font-weight: bold; font-size: 14px; border-radius: 8px; padding: 5px 15px;")
        btn_select_user_image.clicked.connect(self._on_select_user_image)
        
        btn_remove_selected = QPushButton("❌ Xóa ảnh đang chọn")
        btn_remove_selected.setMinimumHeight(40)
        btn_remove_selected.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold; font-size: 14px; border-radius: 8px; padding: 5px 15px;")
        btn_remove_selected.clicked.connect(self._on_remove_selected_image)

        btn_clear_user_image = QPushButton("🗑️ Xóa tất cả")
        btn_clear_user_image.setMinimumHeight(40)
        btn_clear_user_image.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold; font-size: 14px; border-radius: 8px; padding: 5px 15px;")
        btn_clear_user_image.clicked.connect(self._on_clear_user_image)
        
        btn_row.addWidget(btn_select_user_image, stretch=2)
        btn_row.addWidget(btn_remove_selected, stretch=1)
        btn_row.addWidget(btn_clear_user_image, stretch=1)
        
        from PySide6.QtWidgets import QListWidget, QListWidgetItem, QListView, QAbstractItemView
        from PySide6.QtGui import QIcon, QPixmap
        from PySide6.QtCore import QSize
        
        self.list_selected_images = QListWidget()
        self.list_selected_images.setViewMode(QListView.ViewMode.IconMode)
        self.list_selected_images.setIconSize(QSize(160, 160))
        self.list_selected_images.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_selected_images.setSpacing(15)
        self.list_selected_images.setMaximumHeight(220)
        self.list_selected_images.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_selected_images.setStyleSheet("background-color: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 8px; color: #1e293b;")
        
        user_image_layout.addLayout(btn_row)
        user_image_layout.addWidget(self.list_selected_images)
        user_image_group.setLayout(user_image_layout)
        layout.addWidget(user_image_group)

        # NÚT ĐIỀU KHIỂN
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.setMinimumHeight(45)
        btn_cancel.setMinimumWidth(100)
        btn_cancel.setStyleSheet("background-color: #f1f5f9; color: #475569; font-weight: bold; font-size: 14px; border: 1.5px solid #cbd5e1; border-radius: 8px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 LƯU CÀI ĐẶT ẢNH")
        btn_save.setMinimumHeight(45)
        btn_save.setMinimumWidth(180)
        btn_save.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold; font-size: 14px; border-radius: 8px;")
        btn_save.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
        
        # Gọi cập nhật giao diện ban đầu
        self._update_image_list()

    def _on_remove_selected_image(self):
        """Xóa các ảnh đang được người dùng chọn trong danh sách"""
        selected_items = self.list_selected_images.selectedItems()
        if not selected_items:
            return
        
        # Lấy tooltip (lưu đường dẫn) của các item đang chọn
        paths_to_remove = [item.toolTip() for item in selected_items]
        
        # Cập nhật lại danh sách paths
        self.selected_image_paths = [p for p in self.selected_image_paths if p not in paths_to_remove]
        self._update_image_list()

    def _on_clear_user_image(self):
        """Xóa toàn bộ danh sách ảnh đã chọn"""
        self.selected_image_paths = []
        self._update_image_list()

    def _update_image_list(self):
        """Cập nhật giao diện danh sách ảnh được chọn"""
        from PySide6.QtWidgets import QListWidgetItem
        from PySide6.QtGui import QIcon, QPixmap
        from PySide6.QtCore import Qt
        import os
        
        self.list_selected_images.clear()
        
        if not self.selected_image_paths:
            item = QListWidgetItem("Chưa chọn ảnh")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_selected_images.addItem(item)
            return
            
        for path in self.selected_image_paths:
            if os.path.exists(path):
                pixmap = QPixmap(path)
                icon = QIcon(pixmap)
                filename = os.path.basename(path)
                # Giới hạn độ dài tên file
                if len(filename) > 15:
                    filename = filename[:12] + "..."
                item = QListWidgetItem(icon, filename)
                item.setToolTip(path)
                self.list_selected_images.addItem(item)

    def _on_subject_changed(self):
        """Hiển thị ô tùy chỉnh khi chọn 'Khác'"""
        if self.combo_subject.currentText() == "Khác":
            self.subject_custom.setVisible(True)
            self.subject_custom.setFocus()
        else:
            self.subject_custom.setVisible(False)
            self.subject_custom.clear()

    def _on_action_changed(self):
        """Hiển thị ô tùy chỉnh khi chọn 'Khác'"""
        if self.combo_action.currentText() == "Khác":
            self.action_custom.setVisible(True)
            self.action_custom.setFocus()
        else:
            self.action_custom.setVisible(False)
            self.action_custom.clear()

    def _on_lighting_changed(self):
        """Hiển thị ô tùy chỉnh khi chọn 'Khác'"""
        if self.combo_lighting.currentText() == "Khác":
            self.lighting_custom.setVisible(True)
            self.lighting_custom.setFocus()
        else:
            self.lighting_custom.setVisible(False)
            self.lighting_custom.clear()

    def _on_camera_changed(self):
        """Hiển thị ô tùy chỉnh khi chọn 'Khác'"""
        if self.combo_camera.currentText() == "Khác":
            self.camera_custom.setVisible(True)
            self.camera_custom.setFocus()
        else:
            self.camera_custom.setVisible(False)
            self.camera_custom.clear()

    def _on_context_changed(self):
        """Hiển thị ô tùy chỉnh khi chọn 'Khác'"""
        if self.combo_context.currentText() == "Khác":
            self.context_custom.setVisible(True)
            self.context_custom.setFocus()
        else:
            self.context_custom.setVisible(False)
            self.context_custom.clear()

    def get_settings(self):
        # Lấy giá trị: nếu chọn "Khác" thì lấy từ ô tùy chỉnh, ngược lại lấy từ dropdown
        subject = self.subject_custom.text().strip() if self.combo_subject.currentText() == "Khác" else (self.combo_subject.currentText() if self.combo_subject.currentText() != "-- Chọn --" else "")
        action = self.action_custom.text().strip() if self.combo_action.currentText() == "Khác" else (self.combo_action.currentText() if self.combo_action.currentText() != "-- Chọn --" else "")
        lighting = self.lighting_custom.text().strip() if self.combo_lighting.currentText() == "Khác" else (self.combo_lighting.currentText() if self.combo_lighting.currentText() != "-- Chọn --" else "")
        camera = self.camera_custom.text().strip() if self.combo_camera.currentText() == "Khác" else (self.combo_camera.currentText() if self.combo_camera.currentText() != "-- Chọn --" else "")
        context = self.context_custom.text().strip() if self.combo_context.currentText() == "Khác" else (self.combo_context.currentText() if self.combo_context.currentText() != "-- Chọn --" else "")

        return (
            self.combo_aspect.currentText(), 
            self.combo_style.currentText(),
            subject,
            action,
            lighting,
            camera,
            context,
            self.selected_image_paths  # Trả về list của image paths
        )
    
    def _on_select_user_image(self):
        """Mở dialog chọn ảnh từ máy tính (hỗ trợ chọn nhiều ảnh)"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "Chọn Ảnh", 
            "", 
            "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if file_paths:
            for path in file_paths:
                if path not in self.selected_image_paths:
                    self.selected_image_paths.append(path)
            self._update_image_list()

