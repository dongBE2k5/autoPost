# ui/components/tab_settings.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QCheckBox, QTextEdit)

class TabSettings(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        from PySide6.QtWidgets import QFormLayout, QHBoxLayout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- NHÓM 1: Cấu hình API AI & Dịch vụ ---
        api_group = QGroupBox("🧠 Cấu hình AI & Dịch vụ (API Keys)")
        api_layout = QFormLayout()
        api_layout.setSpacing(10)
        
        self.input_gemini = QLineEdit()
        self.input_gemini.setEchoMode(QLineEdit.EchoMode.Password) 
        self.input_gemini.setPlaceholderText("Nhập API Key của Google Gemini...")
        
        self.combo_gemini_model = QComboBox() 
        self.combo_gemini_model.addItems(["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.1-pro-preview", "gemini-2.5-flash-lite"])
        
        self.input_system_prompt = QTextEdit()
        self.input_system_prompt.setMaximumHeight(80)
        self.input_system_prompt.setPlaceholderText("Bạn là một chuyên gia Content Marketing...")
        
        self.input_tiktok_api = QLineEdit()
        self.input_tiktok_api.setEchoMode(QLineEdit.EchoMode.Password) 
        self.input_tiktok_api.setPlaceholderText("Nhập Apify Token (Dùng để cào video TikTok)...")
        
        api_layout.addRow("🔑 Gemini API Key:", self.input_gemini)
        api_layout.addRow("🤖 Model AI:", self.combo_gemini_model)
        api_layout.addRow("🔥 System Prompt:", self.input_system_prompt)
        api_layout.addRow("🎬 Apify Token:", self.input_tiktok_api)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # --- NHÓM 2: Cấu hình Facebook ---
        fb_group = QGroupBox("📘 Cấu hình Facebook (Graph API)")
        fb_layout = QFormLayout()
        fb_layout.setSpacing(10)
        
        self.input_fb_id = QLineEdit()
        self.input_fb_id.setPlaceholderText("Nhập ID Page hoặc Group Facebook...")
        
        self.input_fb_token = QLineEdit()
        self.input_fb_token.setEchoMode(QLineEdit.EchoMode.Password) 
        self.input_fb_token.setPlaceholderText("Nhập Facebook Page Access Token (Sống lâu)...")
        
        fb_layout.addRow("🆔 ID Facebook:", self.input_fb_id)
        fb_layout.addRow("🔐 Access Token:", self.input_fb_token)
        fb_group.setLayout(fb_layout)
        layout.addWidget(fb_group)
        
        # --- CÁC NÚT TIỆN ÍCH ---
        utils_layout = QHBoxLayout()
        self.btn_open_cookie = QPushButton('🍪 CẬP NHẬT COOKIES TIKTOK')
        self.btn_open_cookie.setStyleSheet("background-color: #f59e0b; color: white;")
        utils_layout.addWidget(self.btn_open_cookie)
        utils_layout.addStretch()
        layout.addLayout(utils_layout)
        
        # --- THIẾT LẬP ỨNG DỤNG ---
        app_group = QGroupBox("⚙️ Thiết Lập Ứng Dụng")
        app_layout = QVBoxLayout()
        app_layout.setSpacing(8)
        
        self.check_publish_immediately = QCheckBox("🌍 Đăng công khai ngay lập tức (Bỏ tích để tự động Lên lịch 7 ngày tới)")
        self.check_publish_immediately.setChecked(True)
        self.check_publish_immediately.setStyleSheet("font-weight: bold; color: #2563eb; font-size: 15px;")
        app_layout.addWidget(self.check_publish_immediately)
        
        self.lbl_schedule_note = QLabel(
            "⚠️ <i><b>Lưu ý:</b> Nếu KHÔNG công khai bài viết ngay, vui lòng vào Facebook -> Bảng điều khiển -> Nội dung -> "
            "Đã lên lịch -> Chọn \"...\" -> Chọn Reschedule post để đăng ngay hoặc chọn Xóa bài viết để xóa.</i>"
        )
        self.lbl_schedule_note.setStyleSheet("color: #ef4444; font-size: 13px; margin-left: 25px;")
        self.lbl_schedule_note.setWordWrap(True)
        app_layout.addWidget(self.lbl_schedule_note)
        
        self.check_startup = QCheckBox("🚀 Khởi động phần mềm ngầm cùng Windows (Khuyên dùng khi chạy chế độ Auto)")
        self.check_startup.setStyleSheet("font-weight: bold; color: #475569; font-size: 14px;")
        app_layout.addWidget(self.check_startup)
        
        app_group.setLayout(app_layout)
        layout.addWidget(app_group)

        self.btn_save_config = QPushButton('💾 LƯU TOÀN BỘ CẤU HÌNH')
        self.btn_save_config.setStyleSheet("background-color: #2563eb; color: white; min-height: 45px; font-size: 15px; margin-top: 15px;")
        layout.addWidget(self.btn_save_config)
        layout.addStretch()

    def get_settings_data(self):
        return {
            "gemini_key": self.input_gemini.text(),
            "gemini_model": self.combo_gemini_model.currentText(),
            "system_prompt": self.input_system_prompt.toPlainText().strip(),
            "tiktok_api": self.input_tiktok_api.text(),
            "fb_id": self.input_fb_id.text(),
            "fb_token": self.input_fb_token.text(),
            "publish_immediately": self.check_publish_immediately.isChecked(), # LẤY DATA
            "run_on_startup": self.check_startup.isChecked()
        }
        
    def set_settings_data(self, cfg):
        self.input_gemini.setText(cfg.get("gemini_key", ""))
        self.input_tiktok_api.setText(cfg.get("tiktok_api", ""))
        self.input_fb_id.setText(cfg.get("fb_id", ""))
        self.input_fb_token.setText(cfg.get("fb_token", ""))
        self.check_startup.setChecked(cfg.get("run_on_startup", False))
        
        # NẠP DATA
        self.check_publish_immediately.setChecked(cfg.get("publish_immediately", True))
        
        default_sys_prompt = "Bạn là một Copywriter chuyên nghiệp. Nhiệm vụ duy nhất của bạn là viết bài đăng Facebook.\nTUYỆT ĐỐI KHÔNG lặp lại yêu cầu của tôi. KHÔNG giải thích. CHỈ TRẢ VỀ NỘI DUNG CÁC BÀI VIẾT."
        self.input_system_prompt.setPlainText(cfg.get("system_prompt", default_sys_prompt))
        idx = self.combo_gemini_model.findText(cfg.get("gemini_model", ""))
        if idx >= 0: self.combo_gemini_model.setCurrentIndex(idx)