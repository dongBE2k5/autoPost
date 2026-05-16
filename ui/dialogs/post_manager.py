# ui/dialogs/post_manager.py
import os
import sys
import subprocess
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QGroupBox, QMessageBox, QTimeEdit, 
                             QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QAbstractItemView, QSpinBox, QCheckBox)
from PySide6.QtCore import QTime, Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap
from config.settings import MODERN_STYLE
from ui.dialogs.schedule_settings import EditTimeDialog
from ui.dialogs.user_image_selector import UserImageSelectorDialog
from services.image_library_service import ImageLibraryService

class DraftDetailDialog(QDialog):
    def __init__(self, draft_data, parent=None):
        super().__init__(parent)
        self.draft_data = draft_data
        self.setWindowTitle("🔍 Xem và Chỉnh sửa Content")
        self.resize(1000, 600) 
        self.setStyleSheet(MODERN_STYLE)
        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # ----------------------------------------------------
        # --- CỘT TRÁI (MEDIA FRAME)
        # ----------------------------------------------------
        media_frame = QFrame()
        media_frame.setObjectName("MediaFrame")
        media_frame.setStyleSheet("QFrame#MediaFrame { background-color: #f8fafc; border-right: 1.5px solid #cbd5e1; border-radius: 0px; }")
        media_layout = QVBoxLayout(media_frame)
        media_layout.setContentsMargins(15, 20, 15, 20)
        
        media_layout.addWidget(QLabel('<b>📸 Media đính kèm:</b>'))
        
        # Thumbnail Label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(350, 350)
        self.image_label.setStyleSheet("background-color: #e2e8f0; border: 1.5px dashed #94a3b8; border-radius: 8px;")
        
        vid_path = self.draft_data.get("video_path", "")
        img_path = self.draft_data.get("image_path", "")
        
        if vid_path and os.path.exists(vid_path):
            self.image_label.setText("🎬 Video minh họa\\n(Không hỗ trợ xem trước)")
            self.image_label.setStyleSheet("background-color: #fef2f2; border: 1.5px dashed #fca5a5; border-radius: 8px; color: #ef4444; font-weight: bold; font-size: 14px;")
            media_layout.addWidget(self.image_label, stretch=1)
            
            btn_play = QPushButton("▶️ MỞ VIDEO")
            btn_play.setStyleSheet("background-color: #ef4444; color: white; padding: 8px; font-weight: bold; border-radius: 6px;")
            btn_play.clicked.connect(lambda: os.startfile(vid_path) if sys.platform == "win32" else subprocess.call(["open" if sys.platform == "darwin" else "xdg-open", vid_path]))
            media_layout.addWidget(btn_play)
        else:
            if img_path and os.path.exists(img_path):
                self.update_thumbnail(img_path)
            else:
                self.image_label.setText("🖼️ Chưa có Media")
                self.image_label.setStyleSheet("background-color: #f1f5f9; border: 1.5px dashed #cbd5e1; border-radius: 8px; color: #94a3b8; font-weight: bold; font-size: 16px;")
            media_layout.addWidget(self.image_label, stretch=1)
            
            # Button change image (Only if it's not a video)
            self.btn_change_image = QPushButton('📁 Thêm / Thay ảnh')
            self.btn_change_image.setStyleSheet("background-color: #ffffff; color: #3b82f6; font-weight: bold; border: 1.5px solid #3b82f6; border-radius: 6px; padding: 8px;")
            self.btn_change_image.clicked.connect(self.choose_image)
            media_layout.addWidget(self.btn_change_image)
            
        main_layout.addWidget(media_frame, stretch=3)

        # ----------------------------------------------------
        # --- CỘT PHẢI (EDITOR)
        # ----------------------------------------------------
        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(10, 15, 10, 10)
        
        # Info Layout
        info_layout = QHBoxLayout()
        
        info_layout.addWidget(QLabel('<b>🕒 Thời gian:</b>'))
        time_edit = QLineEdit(self.draft_data.get("timestamp", "Không xác định"))
        time_edit.setReadOnly(True)
        time_edit.setStyleSheet("background-color: #f1f5f9; color: #64748b; border: 1px solid #cbd5e1; padding: 6px 10px;")
        info_layout.addWidget(time_edit, stretch=1)

        info_layout.addSpacing(15)

        info_layout.addWidget(QLabel('<b>📌 Nguồn/Trend:</b>'))
        self.kw_edit = QLineEdit(self.draft_data.get("keyword", ""))
        info_layout.addWidget(self.kw_edit, stretch=3)
        
        editor_layout.addLayout(info_layout)

        editor_layout.addSpacing(10)
        editor_layout.addWidget(QLabel('<b>📝 Nội dung bài viết (Có thể chỉnh sửa trực tiếp):</b>'))
        
        self.content_edit = QTextEdit()
        self.content_edit.setPlainText(self.draft_data.get("content", ""))
        self.content_edit.setStyleSheet("font-size: 15px; padding: 12px; background-color: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 8px;")
        editor_layout.addWidget(self.content_edit)

        editor_layout.addSpacing(10)

        # Button Layout (Bottom Right)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1) # Đẩy các nút sang phải
        
        self.btn_cancel = QPushButton('Đóng (Không lưu)')
        self.btn_cancel.setMinimumWidth(120)
        self.btn_cancel.setStyleSheet("""
            QPushButton { background-color: #ffffff; color: #334155; border: 1.5px solid #cbd5e1; font-weight: bold; border-radius: 6px; padding: 8px 15px; }
            QPushButton:hover { background-color: #f1f5f9; border-color: #94a3b8; }
        """)
        self.btn_cancel.clicked.connect(self.reject) 
        
        self.btn_save = QPushButton('💾 Lưu lại thay đổi')
        self.btn_save.setMinimumWidth(140)
        self.btn_save.setStyleSheet("""
            QPushButton { background-color: #22c55e; color: white; font-weight: bold; border-radius: 6px; padding: 8px 15px; border: none; }
            QPushButton:hover { background-color: #16a34a; }
        """)
        self.btn_save.clicked.connect(self.save_changes) 
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(self.btn_save)
        
        editor_layout.addLayout(btn_layout)
        
        main_layout.addLayout(editor_layout, stretch=5)

    def update_thumbnail(self, path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.image_label.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 8px; background-color: transparent;")
            self.image_label.setPixmap(pixmap.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.image_label.setText("⚠️ Lỗi hiển thị ảnh")

    def save_changes(self):
        self.draft_data["keyword"] = self.kw_edit.text().strip()
        self.draft_data["content"] = self.content_edit.toPlainText().strip()
        self.accept()

    def choose_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn ảnh minh họa",
            "",
            "Ảnh (*.png *.jpg *.jpeg *.webp *.bmp);;Tất cả file (*)"
        )
        if path:
            self.draft_data["image_path"] = path
            self.update_thumbnail(path)


class DraftsDialog(QDialog):
    post_now_requested = Signal(dict) 
    queue_requested = Signal(dict, str) 

    def __init__(self, drafts_list, parent=None):
        super().__init__(parent)
        self.drafts_list = drafts_list 
        self.setWindowTitle("📁 Kho Content đã tạo (Chờ xếp lịch)")
        self.resize(1100, 700) 
        self.setStyleSheet(MODERN_STYLE)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # --- THANH CÔNG CỤ TÌM KIẾM ---
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 5)
        
        self.chk_select_all = QCheckBox("☑️ Chọn tất cả")
        self.chk_select_all.setStyleSheet("font-weight: bold; color: #334155; padding-right: 15px;")
        self.chk_select_all.toggled.connect(self.toggle_select_all)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm Content theo từ khóa, nội dung...")
        self.search_input.setMinimumHeight(40)
        self.search_input.setStyleSheet("padding: 8px 15px; font-size: 14px; border-radius: 8px; border: 1.5px solid #cbd5e1; background-color: #ffffff;")
        self.search_input.textChanged.connect(self.filter_drafts)

        top_layout.addWidget(self.chk_select_all)
        top_layout.addWidget(self.search_input, stretch=1)
        layout.addLayout(top_layout)

        # --- BẢNG DỮ LIỆU ---
        self.table_widget = QTableWidget(len(self.drafts_list), 5) 
        self.table_widget.setHorizontalHeaderLabels(["Chọn", "Media", "Thời gian tạo", "Từ khóa / Nguồn", "Nội dung"])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) 
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.table_widget.verticalHeader().setDefaultSectionSize(90) 
        self.table_widget.setStyleSheet("QTableWidget { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; }")
        
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table_widget.setColumnWidth(0, 60)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table_widget.setColumnWidth(1, 100)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_widget.setColumnWidth(2, 120)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table_widget.setColumnWidth(3, 160)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) 
        
        self.table_widget.itemChanged.connect(self._on_item_changed)

        # Tránh lag khi mở form: Load dữ liệu sau khi vẽ xong giao diện (đợi 100ms)
        QTimer.singleShot(100, self.load_table_data)
        
        layout.addWidget(self.table_widget, stretch=1)

        # --- LÊN LỊCH & NÚT BẤM (BOTTOM LAYOUT) ---
        bottom_group = QGroupBox("🚀 Cài đặt & Thao tác (Áp dụng cho các bài đã chọn)")
        bottom_group.setStyleSheet("QGroupBox { border: 1px solid #cbd5e1; border-radius: 8px; font-weight: bold; color: #1e293b; margin-top: 15px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 10px; background-color: #f1f5f9; }")
        bg_layout = QHBoxLayout(bottom_group)
        bg_layout.setContentsMargins(15, 20, 15, 15)
        bg_layout.setSpacing(10)

        # 1. Trái: Delete
        self.btn_delete = QPushButton('🗑️ Xóa đã chọn')
        self.btn_delete.setMinimumHeight(40)
        self.btn_delete.setStyleSheet("""
            QPushButton { background-color: #ffffff; color: #ef4444; font-weight: bold; border-radius: 6px; border: 1.5px solid #fca5a5; padding: 5px 15px; }
            QPushButton:hover { background-color: #fef2f2; border: 1.5px solid #ef4444; }
        """)
        self.btn_delete.clicked.connect(self.delete_draft)
        
        # 2. Giữa: Schedule Group
        self.draft_time_picker = QTimeEdit()
        self.draft_time_picker.setDisplayFormat("HH:mm")
        self.draft_time_picker.setTime(QTime.currentTime())
        self.draft_time_picker.setMinimumHeight(35)
        self.draft_time_picker.setToolTip("Công cụ sẽ tự đăng trong ngày hôm nay. Nếu giờ đã qua, sẽ tự động chuyển lịch sang ngày mai.")
        
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(0, 1440) 
        self.spin_interval.setSuffix(" phút")
        self.spin_interval.setValue(15) 
        self.spin_interval.setMinimumHeight(35)

        # 3. Phải: Actions
        self.btn_post_now = QPushButton('⚡ Đăng Ngay bài đầu')
        self.btn_post_now.setMinimumHeight(40)
        self.btn_post_now.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; border-radius: 6px; padding: 5px 15px;")
        self.btn_post_now.clicked.connect(self.request_post_now)
        
        self.btn_queue_selected = QPushButton("🚀 CHUYỂN VÀO HÀNG ĐỢI")
        self.btn_queue_selected.setMinimumHeight(40)
        self.btn_queue_selected.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold; padding: 5px 15px; border-radius: 6px;")
        self.btn_queue_selected.clicked.connect(self.queue_selected_posts)

        bg_layout.addWidget(self.btn_delete)
        bg_layout.addStretch(1)
        bg_layout.addWidget(QLabel("🕒 Bắt đầu lúc:"))
        bg_layout.addWidget(self.draft_time_picker)
        bg_layout.addSpacing(10)
        bg_layout.addWidget(QLabel("⏳ Giãn cách:"))
        bg_layout.addWidget(self.spin_interval)
        bg_layout.addStretch(1)
        bg_layout.addWidget(self.btn_post_now)
        bg_layout.addWidget(self.btn_queue_selected)
        
        layout.addWidget(bottom_group)
        self.setLayout(layout)

    def update_data(self, new_list):
        self.drafts_list = new_list
        self.table_widget.setRowCount(0)
        # Tăng thời gian chờ lên 100ms để đảm bảo UI kịp vẽ (paint) xong trước khi vòng lặp data làm nghẽn CPU
        QTimer.singleShot(100, self.load_table_data)

    def load_table_data(self):
        self.table_widget.setRowCount(0)
        for row, d in enumerate(self.drafts_list):
            self.table_widget.insertRow(row)
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_item.setCheckState(Qt.CheckState.Unchecked)
            chk_item.setData(Qt.ItemDataRole.UserRole, row)
            
            vid_path = d.get('video_path', '')
            img_path = d.get('image_path', '')
            
            if vid_path and os.path.exists(vid_path):
                lbl = QLabel("🎬 VIDEO")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet("font-weight: bold; color: #ef4444;")
                self.table_widget.setItem(row, 1, QTableWidgetItem("")) # Placeholder for background
                self.table_widget.setCellWidget(row, 1, lbl)
            elif img_path and os.path.exists(img_path):
                img_label = QLabel()
                pixmap = QPixmap(img_path).scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                img_label.setPixmap(pixmap)
                img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(row, 1, QTableWidgetItem("")) # Placeholder for background
                self.table_widget.setCellWidget(row, 1, img_label)
            else:
                no_img_item = QTableWidgetItem("")
                no_img_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(row, 1, no_img_item)
            
            self.table_widget.setItem(row, 0, chk_item)
            self.table_widget.setItem(row, 2, QTableWidgetItem(d.get("timestamp", "Bản cũ")))
            self.table_widget.setItem(row, 3, QTableWidgetItem(d.get("keyword", "")))
            self.table_widget.setItem(row, 4, QTableWidgetItem(d.get("content", "").replace('\n', ' ')))

    def _on_item_changed(self, item):
        if getattr(self, 'is_loading', False):
            return
        if item.column() == 0:
            row = item.row()
            color = QColor("#e0f2fe") if item.checkState() == Qt.CheckState.Checked else QColor("#ffffff")
            for col in range(self.table_widget.columnCount()):
                it = self.table_widget.item(row, col)
                if it:
                    it.setBackground(color)

    def toggle_select_all(self):
        new_state = Qt.CheckState.Checked if self.chk_select_all.isChecked() else Qt.CheckState.Unchecked
        for row in range(self.table_widget.rowCount()):
            if not self.table_widget.isRowHidden(row): 
                self.table_widget.item(row, 0).setCheckState(new_state)

    def get_checked_rows(self):
        rows = []
        for row in range(self.table_widget.rowCount()):
            if self.table_widget.item(row, 0).checkState() == Qt.CheckState.Checked:
                rows.append(row)
        return rows

    def filter_drafts(self, text):
        search_term = text.lower()
        for row in range(self.table_widget.rowCount()):
            d_data = self.drafts_list[row]
            if search_term in d_data.get("keyword", "").lower() or search_term in d_data.get("content", "").lower():
                self.table_widget.setRowHidden(row, False)
            else: 
                self.table_widget.setRowHidden(row, True)

    def on_item_double_clicked(self, item):
        row = item.row()
        draft_data = self.drafts_list[row]
        dialog = DraftDetailDialog(draft_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_table_data()

    def queue_selected_posts(self):
        selected_rows = self.get_checked_rows()
        if not selected_rows: return
        start_time = self.draft_time_picker.time()
        interval_mins = self.spin_interval.value()
        for i, row in enumerate(selected_rows):
            draft_data = self.drafts_list[row]
            post_time = start_time.addSecs(i * interval_mins * 60)
            self.queue_requested.emit(draft_data, post_time.toString("HH:mm"))
            
        for row in reversed(selected_rows):
            draft_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if draft_data in self.drafts_list: self.drafts_list.remove(draft_data)
            self.table_widget.removeRow(row)
        if hasattr(self, 'chk_select_all'):
            self.chk_select_all.setChecked(False)

    def request_post_now(self):
        selected_rows = self.get_checked_rows()
        if not selected_rows: return
        row = selected_rows[0] 
        draft_data = self.drafts_list[row]
        if QMessageBox.question(self, 'Xác nhận', 'Đăng ngay?') == QMessageBox.StandardButton.Yes:
            self.post_now_requested.emit(draft_data) 
            if draft_data in self.drafts_list: self.drafts_list.remove(draft_data)
            self.accept() 

    def delete_draft(self):
        selected_rows = self.get_checked_rows()
        if not selected_rows: return
        from PySide6.QtWidgets import QMessageBox
        if QMessageBox.question(self, 'Xác nhận', f'Bạn có chắc chắn muốn xóa {len(selected_rows)} bài đã chọn?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            for row in reversed(selected_rows):
                draft_data = self.drafts_list[row]
                if draft_data in self.drafts_list: self.drafts_list.remove(draft_data) 
                self.table_widget.removeRow(row)
            if hasattr(self, 'chk_select_all'):
                self.chk_select_all.setChecked(False)


class QueueDialog(QDialog):
    def __init__(self, queue_list, parent=None):
        super().__init__(parent)
        self.queue_list = queue_list 
        self.setWindowTitle("📋 Quản lý Hàng Đợi")
        self.resize(900, 600)
        self.setStyleSheet(MODERN_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        self.table_widget = QTableWidget(0, 3)
        self.table_widget.setHorizontalHeaderLabels(["Giờ sẽ đăng", "Từ khóa / Nguồn", "Nội dung"])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) 
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) 
        self.table_widget.itemDoubleClicked.connect(self.edit_queue_time)
        self.table_widget.verticalHeader().setDefaultSectionSize(70) 
        self.table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) 
        self.table_widget.setStyleSheet("QTableWidget { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; }")
        layout.addWidget(self.table_widget, stretch=1)

        action_layout = QHBoxLayout()
        self.btn_edit = QPushButton('✏️ Sửa giờ đăng')
        self.btn_edit.setMinimumHeight(45)
        self.btn_edit.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold; font-size: 14px; border-radius: 8px; padding: 10px 20px;")
        self.btn_edit.clicked.connect(self.edit_queue_time)
        
        self.btn_delete = QPushButton('❌ Xóa khỏi Hàng đợi')
        self.btn_delete.setMinimumHeight(45)
        self.btn_delete.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold; font-size: 14px; border-radius: 8px; padding: 10px 20px;")
        self.btn_delete.clicked.connect(self.delete_queue_item)
        
        action_layout.addStretch(1)
        action_layout.addWidget(self.btn_edit, stretch=2)
        action_layout.addSpacing(15)
        action_layout.addWidget(self.btn_delete, stretch=2)
        layout.addLayout(action_layout)
        
        # Tránh lag khi mở form: Load dữ liệu sau khi vẽ xong giao diện
        QTimer.singleShot(100, self.refresh_table)

    def update_data(self, new_list):
        self.queue_list = new_list
        self.table_widget.setRowCount(0)
        QTimer.singleShot(100, self.refresh_table)

    def refresh_table(self):
        self.table_widget.setRowCount(0)
        self.queue_list.sort(key=lambda x: x['time'])
        for row, q in enumerate(self.queue_list):
            self.table_widget.insertRow(row)
            time_item = QTableWidgetItem(f" 🕒 {q.get('time', '00:00')} ")
            time_item.setData(Qt.ItemDataRole.UserRole, q)
            time_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.table_widget.setItem(row, 0, time_item)
            kw_display = f"🖼️ {q.get('keyword', '')}" if q.get('image_path') else q.get("keyword", "")
            self.table_widget.setItem(row, 1, QTableWidgetItem(kw_display))
            self.table_widget.setItem(row, 2, QTableWidgetItem(q.get("content", "").replace('\n', ' ')))

    def edit_queue_time(self):
        selected_items = self.table_widget.selectedItems()
        if not selected_items: return
        queue_data = self.table_widget.item(selected_items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        
        dialog = EditTimeDialog(queue_data.get("time", "00:00"), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            queue_data["time"] = dialog.get_new_time() 
            self.refresh_table()

    def delete_queue_item(self):
        selected_rows = set(item.row() for item in self.table_widget.selectedItems())
        for row in sorted(selected_rows, reverse=True):
            queue_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if queue_data in self.queue_list: self.queue_list.remove(queue_data) 
            self.table_widget.removeRow(row)