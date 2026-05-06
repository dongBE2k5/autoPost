# ui/components/tab_dashboard.py
import os
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QGroupBox, QSpinBox, QRadioButton, 
                             QButtonGroup, QFrame, QCheckBox, QFileDialog, QSizePolicy,
                             QListWidget, QScrollArea)
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
        # CỘT PHẢI: BẢNG ĐIỀU KHIỂN (có scroll)
        # ==========================================
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 4, 0)
        right_layout.setSpacing(8)
        
        # 1. Trợ lý AI
        ai_group = QGroupBox("✨ Trợ lý AI Sinh Content")
        ai_layout = QVBoxLayout()
        
        # --- TÀI LIỆU SẢN PHẨM (MULTI-FILE) ---
        doc_group_box = QGroupBox("📂 Tài liệu sản phẩm")
        doc_group_layout = QVBoxLayout()
        doc_group_layout.setContentsMargins(6, 6, 6, 6)
        doc_group_layout.setSpacing(4)

        self.list_doc_files = QListWidget()
        self.list_doc_files.setMaximumHeight(70)
        self.list_doc_files.setStyleSheet(
            "QListWidget { border: 1px solid #334155; border-radius: 6px; background: #1e293b; color: #e2e8f0; font-size: 12px; }"
            "QListWidget::item { padding: 2px 6px; }"
            "QListWidget::item:selected { background: #334155; }"
        )
        doc_group_layout.addWidget(self.list_doc_files)

        doc_btn_row = QHBoxLayout()
        doc_btn_row.setSpacing(6)
        self.btn_add_doc = QPushButton("➕ Thêm File")
        self.btn_add_doc.setFixedWidth(110)
        self.btn_add_doc.clicked.connect(self.browse_doc_file)
        self.btn_remove_doc = QPushButton("❌ Xóa")
        self.btn_remove_doc.setFixedWidth(80)
        self.btn_remove_doc.clicked.connect(self.remove_selected_doc)
        self.btn_clear_docs = QPushButton("🗑️ Xóa tất cả")
        self.btn_clear_docs.setFixedWidth(110)
        self.btn_clear_docs.clicked.connect(self.list_doc_files.clear)
        doc_btn_row.addWidget(self.btn_add_doc)
        doc_btn_row.addWidget(self.btn_remove_doc)
        doc_btn_row.addWidget(self.btn_clear_docs)
        doc_btn_row.addStretch()
        doc_group_layout.addLayout(doc_btn_row)
        doc_group_box.setLayout(doc_group_layout)
        ai_layout.addWidget(doc_group_box)

        # --- CHECKBOX: SEARCH TREND TIKTOK ---
        self.chk_search_tiktok = QCheckBox("📡 Search Trend TikTok (dùng API TikTok để lấy video trending)")
        self.chk_search_tiktok.setChecked(False)
        self.chk_search_tiktok.setStyleSheet("font-weight: bold; color: #38bdf8; padding: 4px 0;")
        ai_layout.addWidget(self.chk_search_tiktok)

        # --- PHẦN TIKTOK: Ẩn/Hiện theo checkbox ---
        self.tiktok_section = QFrame()
        tiktok_layout = QVBoxLayout(self.tiktok_section)
        tiktok_layout.setContentsMargins(0, 0, 0, 0)
        tiktok_layout.setSpacing(6)

        row1 = QHBoxLayout()
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
        row1.addStretch()
        tiktok_layout.addLayout(row1)

        row1_5 = QHBoxLayout()
        row1_5.addWidget(QLabel('Chủ đề / Ngách:'))
        self.input_target_topics = QLineEdit()
        self.input_target_topics.setPlaceholderText("VD: Sức khỏe, Ăn uống, Mẹ bé...")
        row1_5.addWidget(self.input_target_topics, stretch=1)
        tiktok_layout.addLayout(row1_5)

        # --- HASHTAGS & SEARCH QUERIES ---
        hs_row = QHBoxLayout()
        sq_col = QVBoxLayout()
        sq_col.addWidget(QLabel('🔍 Nguồn / searchQueries (mỗi dòng 1 câu tìm kiếm):'))
        self.console_keyword = QTextEdit()
        self.console_keyword.setMaximumHeight(65)
        self.console_keyword.setPlaceholderText("thu hoạch lúa miền tây việt nam\ncánh đồng lúa chín vàng")
        sq_col.addWidget(self.console_keyword)
        hs_row.addLayout(sq_col)

        hashtag_col = QVBoxLayout()
        hashtag_col.addWidget(QLabel('#️ Hashtags (mỗi dòng 1 từ, không cần dấu #):'))
        self.input_hashtags = QTextEdit()
        self.input_hashtags.setMaximumHeight(65)
        self.input_hashtags.setPlaceholderText("luamia\nnongdan\ncanhdonglua")
        hashtag_col.addWidget(self.input_hashtags)
        hs_row.addLayout(hashtag_col)
        tiktok_layout.addLayout(hs_row)

        ai_layout.addWidget(self.tiktok_section)

        # --- Ẩn/Hiện TikTok section theo checkbox ---
        self.tiktok_section.setVisible(False)  # Mặc định ẩn

        # Số bài khi không dùng TikTok (ẩn khi tick TikTok)
        self.solo_count_section = QFrame()
        solo_layout = QHBoxLayout(self.solo_count_section)
        solo_layout.setContentsMargins(0, 0, 0, 0)
        solo_layout.addWidget(QLabel('📝 Số bài viết:'))
        self.spin_ai_count_solo = QSpinBox()
        self.spin_ai_count_solo.setRange(1, 20)
        self.spin_ai_count_solo.setValue(1)
        solo_layout.addWidget(self.spin_ai_count_solo)
        solo_layout.addStretch()
        ai_layout.addWidget(self.solo_count_section)

        # Toggle: khi tick TikTok → hiện tiktok_section, ẩn solo; ngược lại
        def _toggle_tiktok(checked):
            self.tiktok_section.setVisible(checked)
            self.solo_count_section.setVisible(not checked)
        self.chk_search_tiktok.toggled.connect(_toggle_tiktok)


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
        self.btn_auto_pipeline.setStyleSheet("background-color: #8b5cf6; color: white; padding: 15px; font-size: 15px; border-radius: 8px; border: none; font-weight: bold; min-height: 50px;")
        self.btn_auto_pipeline.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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

        # Bọc cột phải trong QScrollArea để tránh bị cắt khi full window
        right_scroll = QScrollArea()
        right_scroll.setWidget(right_container)
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # Ráp các mảng lại
        layout.addWidget(log_group, stretch=3)
        layout.addWidget(right_scroll, stretch=7)

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
        elif "📝" in msg:
            color = "#f472b6" # Màu Hồng
            
        html_msg = f"<span style='color: #64748b;'>[{time_str}]</span> <span style='color: {color};'>{msg}</span>"
        self.console_log.append(html_msg)

        # Xử lý tự động cuộn (Auto-scroll)
        if self.chk_autoscroll.isChecked():
            scrollbar = self.console_log.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def get_pipeline_config(self):
        """Đóng gói dữ liệu nhập từ UI thành 1 Dict để gửi cho Controller"""
        doc_paths = [self.list_doc_files.item(i).text() for i in range(self.list_doc_files.count())]
        use_tiktok = self.chk_search_tiktok.isChecked()

        # Nếu dùng TikTok: lấy search queries và số bài từ phần TikTok
        if use_tiktok:
            raw_sq = self.console_keyword.toPlainText().strip()
            search_queries = [s.strip() for s in raw_sq.splitlines() if s.strip()]
            custom_trend = search_queries[0] if search_queries else ''
            raw_tags = self.input_hashtags.toPlainText().strip()
            hashtags = [t.strip().lstrip('#') for t in raw_tags.splitlines() if t.strip()]
            count = self.spin_ai_count.value()
        else:
            search_queries = []
            custom_trend = ''
            hashtags = []
            count = self.spin_ai_count_solo.value()

        return {
            'use_tiktok': use_tiktok,
            'custom_trend': custom_trend,
            'search_queries': search_queries,
            'max_videos': self.spin_max_videos.value(),
            'count': count,
            'target_topics': self.input_target_topics.text().strip() if use_tiktok else '',
            'doc_file_paths': doc_paths,
            'doc_file_path': doc_paths[0] if doc_paths else '',
            'hashtags': hashtags,
            'custom_prompt': self.input_custom_prompt.toPlainText().strip(),
            'ignore_keywords': self.input_ignore_keywords.toPlainText().strip(),
            'word_limit': self.spin_word_limit.value(),
            'gen_image': self.check_gen_image.isChecked(),
            'gen_video': self.check_gen_video.isChecked(),
        }
    def browse_doc_file(self):
        """Mở cửa sổ chọn nhiều file tài liệu"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Chọn File Tài Liệu Sản Phẩm",
            "",
            "Tài liệu (*.txt *.docx *.pdf);;All Files (*)"
        )
        for path in file_paths:
            # Tránh thêm trùng
            existing = [self.list_doc_files.item(i).text() for i in range(self.list_doc_files.count())]
            if path not in existing:
                self.list_doc_files.addItem(path)

    def remove_selected_doc(self):
        """Xóa file đang được chọn trong danh sách"""
        for item in self.list_doc_files.selectedItems():
            self.list_doc_files.takeItem(self.list_doc_files.row(item))
    def load_config(self, cfg):
        """Nạp dữ liệu đã lưu từ Database lên Giao diện"""
        # Nguồn/Trend = searchQueries (lưu nhiều dòng)
        self.console_keyword.setPlainText(cfg.get('dash_keyword', ''))
        self.spin_max_videos.setValue(int(cfg.get('dash_max_videos', 1)))
        self.spin_ai_count.setValue(int(cfg.get('dash_ai_count', 1)))
        self.input_target_topics.setText(cfg.get('dash_topics', ''))

        # Nạp danh sách file tài liệu (lưu dưới dạng JSON list)
        import json
        saved_paths_raw = cfg.get('dash_doc_file', '')
        self.list_doc_files.clear()
        try:
            paths = json.loads(saved_paths_raw) if saved_paths_raw.startswith('[') else ([saved_paths_raw] if saved_paths_raw else [])
            for p in paths:
                if p:
                    self.list_doc_files.addItem(p)
        except Exception:
            if saved_paths_raw:
                self.list_doc_files.addItem(saved_paths_raw)

        self.input_custom_prompt.setPlainText(cfg.get('dash_custom_prompt', ''))
        self.input_ignore_keywords.setPlainText(cfg.get('dash_ignore', ''))
        self.spin_word_limit.setValue(int(cfg.get('dash_word_limit', 0)))

        # Checkbox TikTok
        self.chk_search_tiktok.setChecked(cfg.get('dash_use_tiktok', 'False') == 'True')
        # Nạp hashtags
        self.input_hashtags.setPlainText(cfg.get('dash_hashtags', ''))
        self.spin_ai_count_solo.setValue(int(cfg.get('dash_ai_count', 1)))

        # Checkbox lưu dạng chuỗi "True"/"False" nên cần so sánh
        self.check_gen_image.setChecked(cfg.get('dash_gen_image', 'False') == 'True')
        self.check_gen_video.setChecked(cfg.get('dash_gen_video', 'False') == 'True')

    def set_ui_locked(self, locked):
        """Khóa hoặc mở khóa các thao tác của người dùng"""
        self.chk_search_tiktok.setEnabled(not locked)
        self.console_keyword.setReadOnly(locked)
        self.spin_max_videos.setReadOnly(locked)
        self.spin_ai_count.setReadOnly(locked)
        self.spin_ai_count_solo.setReadOnly(locked)
        self.input_target_topics.setReadOnly(locked)
        self.btn_add_doc.setEnabled(not locked)
        self.btn_remove_doc.setEnabled(not locked)
        self.btn_clear_docs.setEnabled(not locked)
        self.input_custom_prompt.setReadOnly(locked)
        self.input_ignore_keywords.setReadOnly(locked)
        self.input_hashtags.setReadOnly(locked)
        self.spin_word_limit.setReadOnly(locked)
        self.check_gen_image.setEnabled(not locked)
        self.check_gen_video.setEnabled(not locked)
        self.btn_logo_settings.setEnabled(not locked)
        self.btn_video_settings.setEnabled(not locked)
        self.btn_open_drafts.setEnabled(not locked)
        self.btn_open_queue.setEnabled(not locked)
        self.btn_open_schedule.setEnabled(not locked)
        
    def set_analysis_state(self, is_analyzing):
        """Chuyển đổi trạng thái giao diện khi đang phân tích"""
        if is_analyzing:
            self.btn_auto_pipeline.setText("⏹️ DỪNG PHÂN TÍCH")
            self.btn_auto_pipeline.setStyleSheet("background-color: #ef4444; color: white; padding: 15px; font-size: 15px; border-radius: 8px; border: none; font-weight: bold;")
        else:
            self.btn_auto_pipeline.setText("⚡ BẮT ĐẦU CÀO & PHÂN TÍCH")
            self.btn_auto_pipeline.setStyleSheet("background-color: #8b5cf6; color: white; padding: 15px; font-size: 15px; border-radius: 8px; border: none; font-weight: bold;")
        self.btn_auto_pipeline.setEnabled(True)