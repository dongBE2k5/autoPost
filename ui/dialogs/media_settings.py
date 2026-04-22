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