# ui/components/tab_dashboard.py
import os
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QGroupBox, QSpinBox, QRadioButton, 
                             QButtonGroup, QFrame, QCheckBox, QFileDialog)
from PySide6.QtCore import Qt
import datetime

class TabDashboard(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window 
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout(self)
        
        # ==========================================
        # CỘT TRÁI: TERMINAL SYSTEM LOGS (ĐÃ BỎ NÚT XÓA/LƯU)
        # ==========================================
        log_group = QGroupBox("💻 Terminal: System Logs")
        log_layout = QVBoxLayout()
        
        # --- Toolbar tinh giản ---
        log_toolbar = QHBoxLayout()
        self.chk_autoscroll = QCheckBox("Cuộn tự động")
        self.chk_autoscroll.setChecked(True)
        self.chk_autoscroll.setStyleSheet("color: #475569; font-weight: bold;")
        
        log_toolbar.addStretch() # Đẩy nút check sang lề phải
        log_toolbar.addWidget(self.chk_autoscroll)
        
        log_layout.addLayout(log_toolbar)

        # --- Màn hình Terminal ---
        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a;
                color: #e2e8f0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                padding: 10px;
                border: 1px solid #1e293b;
                border-radius: 6px;
            }
            QScrollBar:vertical {
                background: #0f172a;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background: #475569;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #64748b;
            }
        """)
        self.console_log.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        log_layout.addWidget(self.console_log)
        log_group.setLayout(log_layout)
        
        # ==========================================
        # CỘT PHẢI: BẢNG ĐIỀU KHIỂN
        # ==========================================
        right_layout = QVBoxLayout()
        
        # 1. Trợ lý AI
        ai_group = QGroupBox("✨ Trợ lý AI Sinh Content")
        ai_layout = QVBoxLayout()
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel('Nguồn/Trend:'))
        self.console_keyword = QLineEdit() 
        self.console_keyword.setPlaceholderText("VD: Thời trang, Review...")
        row1.addWidget(self.console_keyword, stretch=1)
        row1.addWidget(QLabel('Số video:'))
        self.spin_max_videos = QSpinBox()
        self.spin_max_videos.setRange(1, 50)
        self.spin_max_videos.setValue(1)
        row1.addWidget(self.spin_max_videos)
        row1.addWidget(QLabel('📝 Số bài:'))
        self.spin_ai_count = QSpinBox()
        self.spin_ai_count.setRange(1, 20)
        self.spin_ai_count.setValue(1)
        row1.addWidget(self.spin_ai_count)
        ai_layout.addLayout(row1)

        row1_5 = QHBoxLayout()
        row1_5.addWidget(QLabel('Chủ đề / Ngách:'))
        self.input_target_topics = QLineEdit()
        self.input_target_topics.setPlaceholderText("VD: Sức khỏe, Ăn uống, Mẹ bé...")
        row1_5.addWidget(self.input_target_topics, stretch=1)
        ai_layout.addLayout(row1_5)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel('Tài liệu SP:'))
        self.input_doc_file = QLineEdit()
        self.input_doc_file.setReadOnly(True)
        self.btn_browse_file = QPushButton('Chọn File')
        self.btn_clear_file = QPushButton('❌')
        self.btn_clear_file.clicked.connect(self.input_doc_file.clear)
        self.btn_browse_file.clicked.connect(self.browse_doc_file)
        row2.addWidget(self.input_doc_file, stretch=1)
        row2.addWidget(self.btn_browse_file)
        row2.addWidget(self.btn_clear_file)
        ai_layout.addLayout(row2)

        row3 = QVBoxLayout()
        row3.addWidget(QLabel('Yêu cầu thêm (Prompt):'))
        self.input_custom_prompt = QTextEdit()
        self.input_custom_prompt.setMaximumHeight(60)
        row3.addWidget(self.input_custom_prompt)
        ai_layout.addLayout(row3)

        row4 = QVBoxLayout()
        row4.addWidget(QLabel('Nội dung cấm (Negative):'))
        self.input_ignore_keywords = QTextEdit()
        self.input_ignore_keywords.setMaximumHeight(60)
        row4.addWidget(self.input_ignore_keywords)
        ai_layout.addLayout(row4)
        
        row_limit = QHBoxLayout()
        row_limit.addWidget(QLabel('Giới hạn từ:'))
        self.spin_word_limit = QSpinBox()
        self.spin_word_limit.setRange(0, 5000)
        self.spin_word_limit.setSpecialValueText("Không giới hạn")
        row_limit.addWidget(self.spin_word_limit)
        row_limit.addStretch()
        ai_layout.addLayout(row_limit)
        
        row_logo = QHBoxLayout()
        self.check_gen_image = QCheckBox("🎨 Tạo Ảnh (Image)")
        self.btn_logo_settings = QPushButton('🖼️ Cài Logo')
        self.check_gen_video = QCheckBox("🎬 Tạo Video (Veo 3.1)")
        self.btn_video_settings = QPushButton('🎥 Cài Video')
        row_logo.addWidget(self.check_gen_image)
        row_logo.addWidget(self.btn_logo_settings)
        row_logo.addWidget(self.check_gen_video)
        row_logo.addWidget(self.btn_video_settings)
        row_logo.addStretch()
        ai_layout.addLayout(row_logo)
        
        self.btn_auto_pipeline = QPushButton('⚡ BẮT ĐẦU CÀO & PHÂN TÍCH')
        self.btn_auto_pipeline.setStyleSheet("background-color: #8b5cf6; color: white; padding: 15px; font-size: 15px; border-radius: 8px; border: none;")
        ai_layout.addWidget(self.btn_auto_pipeline)
        ai_group.setLayout(ai_layout)
        right_layout.addWidget(ai_group)

        # 2. Quản lý kho bài
        storage_group = QGroupBox("📁 Quản lý Kho Bài")
        storage_layout = QHBoxLayout()
        self.btn_open_drafts = QPushButton('📂 MỞ KHO CONTENT')
        self.btn_open_queue = QPushButton('📋 XEM HÀNG ĐỢI')
        storage_layout.addWidget(self.btn_open_drafts)
        storage_layout.addWidget(self.btn_open_queue)
        storage_group.setLayout(storage_layout)
        right_layout.addWidget(storage_group)

        # 3. Chế độ Bot
        schedule_group = QGroupBox("🤖 Thiết lập Chế độ Bot")
        schedule_layout = QVBoxLayout()
        mode_layout = QHBoxLayout()
        self.mode_group = QButtonGroup(self)
        self.radio_mode_queue = QRadioButton("🟢 Bốc bài từ Hàng Đợi")
        self.radio_mode_queue.setChecked(True)
        self.radio_mode_az = QRadioButton("🚀 Auto A-Z")
        self.mode_group.addButton(self.radio_mode_queue, 1)
        self.mode_group.addButton(self.radio_mode_az, 2)
        mode_layout.addWidget(self.radio_mode_queue); mode_layout.addWidget(self.radio_mode_az)
        schedule_layout.addLayout(mode_layout)

        time_layout = QHBoxLayout()
        time_input_col = QVBoxLayout()
        self.btn_open_schedule = QPushButton('📅 CÀI ĐẶT KHUNG GIỜ')
        time_input_col.addWidget(self.btn_open_schedule)
        time_input_col.addStretch()
        
        action_col = QVBoxLayout()
        self.lbl_bot_status = QLabel("🔴 ĐANG TẮT")
        self.lbl_bot_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_start_bot = QPushButton('🤖 BẬT BOT')
        self.btn_start_bot.setStyleSheet("background-color: #16a34a; color: white; min-height: 50px; border-radius: 8px; border: none;")
        action_col.addWidget(self.lbl_bot_status)
        action_col.addWidget(self.btn_start_bot)
        
        time_layout.addLayout(time_input_col, stretch=2)
        time_layout.addLayout(action_col, stretch=1)
        schedule_layout.addLayout(time_layout)
        schedule_group.setLayout(schedule_layout)
        right_layout.addWidget(schedule_group)

        # Ráp các mảng lại
        layout.addWidget(log_group, stretch=3)
        layout.addLayout(right_layout, stretch=7)

    # ==========================================
    # CÁC HÀM XỬ LÝ TERMINAL LOGS
    # ==========================================
    def add_log(self, msg):
        time_str = datetime.datetime.now().strftime('%H:%M:%S')
        
        # Logic tô màu tự động cho Console
        color = "#e2e8f0" # Màu xám sáng mặc định
        if "❌" in msg or "Lỗi" in msg or "Thất bại" in msg:
            color = "#ef4444" # Màu Đỏ
        elif "✅" in msg or "Thành công" in msg:
            color = "#22c55e" # Màu Xanh lá
        elif "⚠️" in msg:
            color = "#eab308" # Màu Vàng
        elif any(step in msg for step in ["B1:", "B2:", "B3:", "B4:", "B5:", "B6:", "B7:", "B8:", "->"]):
            color = "#38bdf8" # Màu Xanh lơ (Cyan)
        elif "🪙" in msg:
            color = "#c084fc" # Màu Tím
            
        html_msg = f"<span style='color: #64748b;'>[{time_str}]</span> <span style='color: {color};'>{msg}</span>"
        self.console_log.append(html_msg)

        # Xử lý tự động cuộn (Auto-scroll)
        if self.chk_autoscroll.isChecked():
            scrollbar = self.console_log.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def get_pipeline_config(self):
        """Đóng gói dữ liệu nhập từ UI thành 1 Dict để gửi cho Controller"""
        return {
            'custom_trend': self.console_keyword.text().strip(),
            'max_videos': self.spin_max_videos.value(),
            'count': self.spin_ai_count.value(),
            'target_topics': self.input_target_topics.text().strip(),
            'doc_file_path': self.input_doc_file.text().strip(),
            'custom_prompt': self.input_custom_prompt.toPlainText().strip(),
            'ignore_keywords': self.input_ignore_keywords.toPlainText().strip(),
            'word_limit': self.spin_word_limit.value(),
            'gen_image': self.check_gen_image.isChecked(),
            'gen_video': self.check_gen_video.isChecked(),
        }
    def browse_doc_file(self):
        """Mở cửa sổ chọn file .txt"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Chọn File Tài Liệu Sản Phẩm", 
            "", 
           "Tài liệu (*.txt *.docx *.pdf);;All Files (*)"
        )
        if file_path:
            self.input_doc_file.setText(file_path)
    def load_config(self, cfg):
        """Nạp dữ liệu đã lưu từ Database lên Giao diện"""
        self.console_keyword.setText(cfg.get('dash_keyword', ''))
        self.spin_max_videos.setValue(int(cfg.get('dash_max_videos', 1)))
        self.spin_ai_count.setValue(int(cfg.get('dash_ai_count', 1)))
        self.input_target_topics.setText(cfg.get('dash_topics', ''))
        self.input_doc_file.setText(cfg.get('dash_doc_file', ''))
        self.input_custom_prompt.setPlainText(cfg.get('dash_custom_prompt', ''))
        self.input_ignore_keywords.setPlainText(cfg.get('dash_ignore', ''))
        self.spin_word_limit.setValue(int(cfg.get('dash_word_limit', 0)))
        
        # Checkbox lưu dạng chuỗi "True"/"False" nên cần so sánh
        self.check_gen_image.setChecked(cfg.get('dash_gen_image', 'False') == 'True')
        self.check_gen_video.setChecked(cfg.get('dash_gen_video', 'False') == 'True')