# ui/dialogs/media_settings.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QComboBox, QSpinBox, QFileDialog)
from config.settings import MODERN_STYLE

class VideoSettingsDialog(QDialog):
    def __init__(self, model, aspect, res, duration, negative, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎥 Cài đặt Video AI (Veo 3.1)")
        self.resize(600, 350)
        self.setStyleSheet(MODERN_STYLE)

        layout = QVBoxLayout(self)

        row_model = QHBoxLayout()
        self.combo_model = QComboBox()
        self.combo_model.addItems(["veo-3.1-generate-preview", "veo-3.1-lite-preview"])
        self.combo_model.setCurrentText(model)
        row_model.addWidget(QLabel("Mô hình Video:"))
        row_model.addWidget(self.combo_model, stretch=1)
        layout.addLayout(row_model)

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
        layout.addLayout(row_format)

        row_duration = QHBoxLayout()
        self.combo_duration = QComboBox()
        self.combo_duration.addItems(["4", "6", "8"])
        self.combo_duration.setCurrentText(duration)
        row_duration.addWidget(QLabel("Thời lượng (giây):"))
        row_duration.addWidget(self.combo_duration, stretch=1)
        lbl_hint = QLabel("<i>*Lưu ý: 1080p & 4k bắt buộc là 8s</i>")
        lbl_hint.setStyleSheet("color: #64748b;")
        row_duration.addWidget(lbl_hint)
        layout.addLayout(row_duration)

        layout.addWidget(QLabel("🚫 Nội dung cần tránh trong Video (Negative Prompt):"))
        self.input_negative = QTextEdit()
        self.input_negative.setPlainText(negative)
        self.input_negative.setPlaceholderText("Ghi bằng tiếng Anh. VD: text, urban background, man-made structures, dark...")
        layout.addWidget(self.input_negative)

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾 Lưu Cài Đặt Video")
        btn_save.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)

    def get_settings(self):
        return self.combo_model.currentText(), self.combo_aspect.currentText(), self.combo_res.currentText(), self.combo_duration.currentText(), self.input_negative.toPlainText().strip()


class LogoSettingsDialog(QDialog):
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