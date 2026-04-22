# ui/dialogs/post_manager.py
import os
import sys
import subprocess
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QGroupBox, QMessageBox, QTimeEdit, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QAbstractItemView, QSpinBox)
from PySide6.QtCore import QTime, Qt, pyqtSignal
from PySide6.QtGui import QFont, QColor, QPixmap
from config.settings import MODERN_STYLE
from ui.dialogs.schedule_settings import EditTimeDialog

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

        vid_path = self.draft_data.get("video_path", "")
        img_path = self.draft_data.get("image_path", "")
        
        if vid_path and os.path.exists(vid_path):
            media_frame = QFrame()
            media_frame.setObjectName("MediaFrame") 
            media_layout = QVBoxLayout(media_frame)
            media_layout.setContentsMargins(20, 20, 20, 20)
            media_layout.addWidget(QLabel('<b>🎬 Video minh họa (Veo 3.1):</b>'))
            
            lbl_vid = QLabel("Phát hiện Video đính kèm.\n(Không thể xem trước trực tiếp trong app)")
            lbl_vid.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_vid.setStyleSheet("color: #94a3b8; font-size: 16px; font-style: italic;")
            media_layout.addWidget(lbl_vid, stretch=1)
            
            btn_play = QPushButton("▶️ MỞ VIDEO BẰNG PHẦN MỀM MÁY TÍNH")
            btn_play.setStyleSheet("background-color: #ef4444; color: white; padding: 15px; font-weight: bold;")
            btn_play.clicked.connect(lambda: os.startfile(vid_path) if sys.platform == "win32" else subprocess.call(["open" if sys.platform == "darwin" else "xdg-open", vid_path]))
            media_layout.addWidget(btn_play)
            
            main_layout.addWidget(media_frame, stretch=4)
            
        elif img_path and os.path.exists(img_path):
            media_frame = QFrame()
            media_frame.setObjectName("MediaFrame") 
            media_layout = QVBoxLayout(media_frame)
            media_layout.setContentsMargins(10, 10, 10, 10)
            
            media_layout.addWidget(QLabel('<b>🖼️ Hình ảnh minh họa:</b>'))
            self.image_label = QLabel()
            self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.image_label.setMinimumSize(450, 450)
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(450, 450, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.image_label.setText("⚠️ Không thể tải hình ảnh.")
            media_layout.addWidget(self.image_label, stretch=1)
            main_layout.addWidget(media_frame, stretch=4) 

        editor_layout = QVBoxLayout()
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel('<b>🕒 Thời gian:</b>'))
        time_edit = QLineEdit(self.draft_data.get("timestamp", "Không xác định"))
        time_edit.setReadOnly(True)
        time_edit.setStyleSheet("background-color: #f1f5f9; color: #64748b;")
        info_layout.addWidget(time_edit)

        info_layout.addWidget(QLabel('<b>📌 Nguồn/Trend:</b>'))
        self.kw_edit = QLineEdit(self.draft_data.get("keyword", ""))
        info_layout.addWidget(self.kw_edit)
        editor_layout.addLayout(info_layout)

        editor_layout.addWidget(QLabel('<b>📝 Nội dung bài viết (Có thể chỉnh sửa trực tiếp):</b>'))
        self.content_edit = QTextEdit()
        self.content_edit.setPlainText(self.draft_data.get("content", ""))
        self.content_edit.setStyleSheet("font-size: 15px; line-height: 1.6;")
        editor_layout.addWidget(self.content_edit)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton('💾 Lưu lại thay đổi')
        self.btn_save.setStyleSheet("background-color: #22c55e; color: white; min-height: 40px;")
        self.btn_save.clicked.connect(self.save_changes) 
        
        self.btn_cancel = QPushButton('Đóng (Không lưu)')
        self.btn_cancel.setStyleSheet("background-color: #e2e8f0; color: #334155; min-height: 40px;")
        self.btn_cancel.clicked.connect(self.reject) 
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save, stretch=1)
        editor_layout.addLayout(btn_layout)
        
        main_layout.addLayout(editor_layout, stretch=6)

    def save_changes(self):
        self.draft_data["keyword"] = self.kw_edit.text().strip()
        self.draft_data["content"] = self.content_edit.toPlainText().strip()
        self.accept()


class DraftsDialog(QDialog):
    post_now_requested = pyqtSignal(dict) 
    queue_requested = pyqtSignal(dict, str) 

    def __init__(self, drafts_list, parent=None):
        super().__init__(parent)
        self.drafts_list = drafts_list 
        self.setWindowTitle("📁 Kho Content đã tạo (Chờ xếp lịch)")
        self.resize(1100, 700) 
        self.setStyleSheet(MODERN_STYLE)
        self.is_all_checked = False
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm Content theo từ khóa, nội dung...")
        self.search_input.textChanged.connect(self.filter_drafts)
        
        self.btn_select_all = QPushButton("☑️ Chọn / Bỏ chọn tất cả")
        self.btn_select_all.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1;")
        self.btn_select_all.clicked.connect(self.toggle_select_all)

        top_layout.addWidget(self.search_input, stretch=1)
        top_layout.addWidget(self.btn_select_all)
        layout.addLayout(top_layout)

        self.table_widget = QTableWidget(len(self.drafts_list), 5) 
        self.table_widget.setHorizontalHeaderLabels(["Chọn", "Media", "Thời gian tạo", "Từ khóa / Nguồn", "Nội dung"])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) 
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.table_widget.verticalHeader().setDefaultSectionSize(80) 
        
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) 

        self.load_table_data()
        layout.addWidget(self.table_widget, stretch=1)

        schedule_group = QGroupBox("⏳ Thiết lập lịch cho các bài ĐÃ TÍCH CHỌN (☑️)")
        schedule_layout = QHBoxLayout()

        self.draft_time_picker = QTimeEdit()
        self.draft_time_picker.setDisplayFormat("HH:mm")
        self.draft_time_picker.setTime(QTime.currentTime())
        
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(0, 1440) 
        self.spin_interval.setSuffix(" phút")
        self.spin_interval.setValue(15) 

        self.btn_queue_selected = QPushButton("🚀 Chuyển vào Hàng đợi")
        self.btn_queue_selected.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold; padding: 10px 20px;")
        self.btn_queue_selected.clicked.connect(self.queue_selected_posts)

        schedule_layout.addWidget(QLabel("🕒 Bắt đầu đăng lúc:"))
        schedule_layout.addWidget(self.draft_time_picker)
        schedule_layout.addSpacing(20)
        schedule_layout.addWidget(QLabel("⏳ Giãn cách giữa các bài:"))
        schedule_layout.addWidget(self.spin_interval)
        schedule_layout.addStretch()
        schedule_layout.addWidget(self.btn_queue_selected)

        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)

        action_layout = QHBoxLayout()
        self.btn_post_now = QPushButton('⚡ Đăng Ngay bài ĐẦU TIÊN được tích chọn')
        self.btn_post_now.setStyleSheet("background-color: #3b82f6; color: white;")
        self.btn_post_now.clicked.connect(self.request_post_now)
        
        self.btn_delete = QPushButton('🗑️ Xóa các bài đã chọn')
        self.btn_delete.setStyleSheet("background-color: #ef4444; color: white;")
        self.btn_delete.clicked.connect(self.delete_draft)
        
        action_layout.addWidget(self.btn_post_now)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_delete)
        layout.addLayout(action_layout)
        self.setLayout(layout)

    def load_table_data(self):
        self.table_widget.setRowCount(0)
        for row, d in enumerate(self.drafts_list):
            self.table_widget.insertRow(row)
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_item.setCheckState(Qt.CheckState.Unchecked)
            chk_item.setData(Qt.ItemDataRole.UserRole, d) 
            
            vid_path = d.get('video_path', '')
            img_path = d.get('image_path', '')
            
            if vid_path and os.path.exists(vid_path):
                lbl = QLabel("🎬 CÓ VIDEO")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet("font-weight: bold; color: #ef4444;")
                self.table_widget.setCellWidget(row, 1, lbl)
            elif img_path and os.path.exists(img_path):
                img_label = QLabel()
                pixmap = QPixmap(img_path).scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                img_label.setPixmap(pixmap)
                img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setCellWidget(row, 1, img_label)
            else:
                no_img_item = QTableWidgetItem("Không có")
                no_img_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(row, 1, no_img_item)
            
            self.table_widget.setItem(row, 0, chk_item)
            self.table_widget.setItem(row, 2, QTableWidgetItem(d.get("timestamp", "Bản cũ")))
            self.table_widget.setItem(row, 3, QTableWidgetItem(d.get("keyword", "")))
            self.table_widget.setItem(row, 4, QTableWidgetItem(d.get("content", "").replace('\n', ' ')))

    def toggle_select_all(self):
        self.is_all_checked = not self.is_all_checked
        new_state = Qt.CheckState.Checked if self.is_all_checked else Qt.CheckState.Unchecked
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
            d_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if search_term in d_data.get("keyword", "").lower() or search_term in d_data.get("content", "").lower():
                self.table_widget.setRowHidden(row, False)
            else: 
                self.table_widget.setRowHidden(row, True)

    def on_item_double_clicked(self, item):
        row = item.row()
        draft_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = DraftDetailDialog(draft_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.table_widget.setItem(row, 3, QTableWidgetItem(draft_data.get("keyword", "")))
            self.table_widget.setItem(row, 4, QTableWidgetItem(draft_data.get("content", "").replace('\n', ' ')))

    def queue_selected_posts(self):
        selected_rows = self.get_checked_rows()
        if not selected_rows: return
        start_time = self.draft_time_picker.time()
        interval_mins = self.spin_interval.value()
        for i, row in enumerate(selected_rows):
            draft_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            post_time = start_time.addSecs(i * interval_mins * 60)
            self.queue_requested.emit(draft_data, post_time.toString("HH:mm"))
            
        for row in reversed(selected_rows):
            draft_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if draft_data in self.drafts_list: self.drafts_list.remove(draft_data)
            self.table_widget.removeRow(row)
        self.is_all_checked = False

    def request_post_now(self):
        selected_rows = self.get_checked_rows()
        if not selected_rows: return
        row = selected_rows[0] 
        draft_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self, 'Xác nhận', 'Đăng ngay?') == QMessageBox.StandardButton.Yes:
            self.post_now_requested.emit(draft_data) 
            if draft_data in self.drafts_list: self.drafts_list.remove(draft_data)
            self.accept() 

    def delete_draft(self):
        selected_rows = self.get_checked_rows()
        if not selected_rows: return
        if QMessageBox.question(self, 'Xác nhận', f'Xóa {len(selected_rows)} bài?') == QMessageBox.StandardButton.Yes:
            for row in reversed(selected_rows):
                draft_data = self.table_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
                if draft_data in self.drafts_list: self.drafts_list.remove(draft_data) 
                self.table_widget.removeRow(row)
            self.is_all_checked = False


class QueueDialog(QDialog):
    def __init__(self, queue_list, parent=None):
        super().__init__(parent)
        self.queue_list = queue_list 
        self.setWindowTitle("📋 Quản lý Hàng Đợi")
        self.resize(900, 600)
        self.setStyleSheet(MODERN_STYLE)
        
        layout = QVBoxLayout(self)
        self.table_widget = QTableWidget(0, 3)
        self.table_widget.setHorizontalHeaderLabels(["Giờ sẽ đăng", "Từ khóa / Nguồn", "Nội dung"])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) 
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) 
        self.table_widget.itemDoubleClicked.connect(self.edit_queue_time)
        self.table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) 
        layout.addWidget(self.table_widget)

        action_layout = QHBoxLayout()
        self.btn_edit = QPushButton('✏️ Sửa giờ đăng')
        self.btn_edit.setStyleSheet("background-color: #eab308; color: white;")
        self.btn_edit.clicked.connect(self.edit_queue_time)
        self.btn_delete = QPushButton('❌ Xóa khỏi Hàng đợi')
        self.btn_delete.setStyleSheet("background-color: #ef4444; color: white;")
        self.btn_delete.clicked.connect(self.delete_queue_item)
        
        action_layout.addStretch()
        action_layout.addWidget(self.btn_edit)
        action_layout.addWidget(self.btn_delete)
        layout.addLayout(action_layout)
        self.refresh_table()

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