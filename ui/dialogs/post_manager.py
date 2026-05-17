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
from PySide6.QtSql import QSqlTableModel, QSqlDatabase
from PySide6.QtCore import Qt

class PostSqlModel(QSqlTableModel):
    """Custom Model để format chữ (xóa \n) và render ảnh Thumbnail"""
    def __init__(self, parent=None, db=None):
        super().__init__(parent, db)
        self._custom_sort_clause = ""
        
    def setSort(self, column, order):
        # Cột 2 là timestamp: DD/MM/YYYY HH:MM:SS
        if column == 2:
            order_str = "DESC" if order == Qt.SortOrder.DescendingOrder else "ASC"
            # Ép kiểu ngày tháng trong SQLite để sort đúng: YYYYMMDD HH:MM:SS
            self._custom_sort_clause = f" ORDER BY substr(timestamp, 7, 4) || substr(timestamp, 4, 2) || substr(timestamp, 1, 2) || substr(timestamp, 11) {order_str}"
            # Xóa sort mặc định của model để tránh bị dính 2 lệnh ORDER BY
            super().setSort(-1, Qt.SortOrder.AscendingOrder)
        else:
            self._custom_sort_clause = ""
            super().setSort(column, order)
            
    def selectStatement(self):
        query = super().selectStatement()
        if self._custom_sort_clause:
            query += self._custom_sort_clause
        return query
    """Custom Model để format chữ (xóa \n) và render ảnh Thumbnail"""
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return super().data(index, role)
            
        col = index.column()
        # Cột 1 là Nội dung
        if col == 1 and role == Qt.ItemDataRole.DisplayRole:
            val = super().data(index, role)
            if val and isinstance(val, str):
                # Thay thế các ký tự xuống dòng bằng khoảng trắng
                val = val.replace('\n', ' ').replace('\r', '')
                # Rút gọn chuỗi nếu quá dài để hiển thị trên 1 dòng
                if len(val) > 100:
                    val = val[:97] + "..."
                return val
                
        # Cột 3 là image_path, Cột 4 là video_path
        if col == 3:
            vid_path = super().data(self.index(index.row(), 4), Qt.ItemDataRole.DisplayRole)
            img_path = super().data(index, Qt.ItemDataRole.DisplayRole)
            
            if role == Qt.ItemDataRole.DisplayRole:
                # Nếu là Video
                if vid_path and os.path.exists(vid_path):
                    return "🎬 VIDEO"
                elif vid_path:
                    return "⚠️ Video không tồn tại"
                    
                # Nếu là Image
                if img_path and os.path.exists(img_path):
                    return "" # Ẩn text để hiển thị Thumbnail
                elif img_path:
                    return "⚠️ Ảnh không tồn tại"
                return "Trống"
            
            elif role == Qt.ItemDataRole.DecorationRole:
                if not (vid_path and os.path.exists(vid_path)) and img_path and os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    if not pixmap.isNull():
                        return pixmap.scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        
            elif role == Qt.ItemDataRole.TextAlignmentRole:
                return int(Qt.AlignmentFlag.AlignCenter)

        return super().data(index, role)

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

    def __init__(self, parent=None):
        super().__init__(parent)
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
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm Content theo từ khóa, nội dung...")
        self.search_input.setMinimumHeight(40)
        self.search_input.setStyleSheet("padding: 8px 15px; font-size: 14px; border-radius: 8px; border: 1.5px solid #cbd5e1; background-color: #ffffff;")
        self.search_input.textChanged.connect(self.filter_drafts)

        top_layout.addWidget(self.search_input, stretch=1)
        layout.addLayout(top_layout)

        # --- BẢNG DỮ LIỆU ---
        self.table_widget = QTableView() 
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) 
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table_widget.doubleClicked.connect(self.on_item_double_clicked)
        self.table_widget.verticalHeader().setDefaultSectionSize(90) 
        self.table_widget.setStyleSheet("QTableView { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; }")
        
        db = QSqlDatabase.database("SettingsDB")
        self.sql_model = PostSqlModel(self, db)
        self.sql_model.setTable("drafts")
        self.sql_model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        
        self.sql_model.setHeaderData(0, Qt.Orientation.Horizontal, "Từ khóa / Nguồn")
        self.sql_model.setHeaderData(1, Qt.Orientation.Horizontal, "Nội dung")
        self.sql_model.setHeaderData(2, Qt.Orientation.Horizontal, "Thời gian tạo")
        self.sql_model.setHeaderData(3, Qt.Orientation.Horizontal, "Media")
        
        self.table_widget.setModel(self.sql_model)
        self.table_widget.setSortingEnabled(True)
        
        # Ẩn các cột thừa (video_path, image_ids)
        for col in range(4, self.sql_model.columnCount()):
            self.table_widget.hideColumn(col)
            
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table_widget.setColumnWidth(0, 200) # Từ khóa
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Nội dung
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table_widget.setColumnWidth(2, 150) # Thời gian
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table_widget.setColumnWidth(3, 100) # Media
        
        self.refresh_table()
        
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

    def update_data(self, new_list=None):
        self.refresh_table()

    def refresh_table(self):
        # Trực tiếp sort bằng model database
        self.sql_model.setSort(2, Qt.SortOrder.DescendingOrder)
        self.sql_model.select()

    def get_checked_rows(self):
        return [idx.row() for idx in self.table_widget.selectionModel().selectedRows()]

    def filter_drafts(self, text):
        search_term = text.lower().replace("'", "''")
        if search_term:
            self.sql_model.setFilter(f"keyword LIKE '%{search_term}%' OR content LIKE '%{search_term}%' OR timestamp LIKE '%{search_term}%'")
        else:
            self.sql_model.setFilter("")
        self.sql_model.select()

    def _get_draft_dict_from_row(self, row):
        return {
            "keyword": self.sql_model.data(self.sql_model.index(row, 0), Qt.ItemDataRole.EditRole),
            "content": self.sql_model.data(self.sql_model.index(row, 1), Qt.ItemDataRole.EditRole),
            "timestamp": self.sql_model.data(self.sql_model.index(row, 2), Qt.ItemDataRole.EditRole),
            "image_path": self.sql_model.data(self.sql_model.index(row, 3), Qt.ItemDataRole.EditRole),
            "video_path": self.sql_model.data(self.sql_model.index(row, 4), Qt.ItemDataRole.EditRole)
        }

    def on_item_double_clicked(self, index):
        row = index.row()
        draft_data = self._get_draft_dict_from_row(row)
        
        dialog = DraftDetailDialog(draft_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Lưu Cả Ảnh
            self.sql_model.setData(self.sql_model.index(row, 0), draft_data.get("keyword"))
            self.sql_model.setData(self.sql_model.index(row, 1), draft_data.get("content"))
            self.sql_model.setData(self.sql_model.index(row, 3), draft_data.get("image_path"))
            self.sql_model.submitAll()
            self.refresh_table()

    def queue_selected_posts(self):
        selected_rows = self.get_checked_rows()
        if not selected_rows: return
        start_time = self.draft_time_picker.time()
        interval_mins = self.spin_interval.value()
        
        for i, row in enumerate(sorted(selected_rows)):
            draft_data = self._get_draft_dict_from_row(row)
            post_time = start_time.addSecs(i * interval_mins * 60)
            self.queue_requested.emit(draft_data, post_time.toString("HH:mm"))
            
        for row in sorted(selected_rows, reverse=True):
            self.sql_model.removeRow(row)
            
        self.sql_model.submitAll()
        self.refresh_table()

    def request_post_now(self):
        selected_rows = self.get_checked_rows()
        if not selected_rows: return
        row = selected_rows[0] 
        draft_data = self._get_draft_dict_from_row(row)
        
        if QMessageBox.question(self, 'Xác nhận', 'Đăng ngay?') == QMessageBox.StandardButton.Yes:
            self.post_now_requested.emit(draft_data) 
            self.sql_model.removeRow(row)
            self.sql_model.submitAll()
            self.accept() 

    def delete_draft(self):
        selected_rows = self.get_checked_rows()
        if not selected_rows: return
        
        if QMessageBox.question(self, 'Xác nhận', f'Bạn có chắc chắn muốn xóa {len(selected_rows)} bài đã chọn?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            for row in sorted(selected_rows, reverse=True):
                self.sql_model.removeRow(row)
                
            self.sql_model.submitAll()
            self.refresh_table()


from PySide6.QtWidgets import QTableView
from PySide6.QtSql import QSqlTableModel, QSqlDatabase

class QueueDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 Quản lý Hàng Đợi")
        self.resize(900, 600)
        self.setStyleSheet(MODERN_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        self.table_widget = QTableView()
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) 
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) 
        self.table_widget.doubleClicked.connect(self.edit_queue_time)
        self.table_widget.verticalHeader().setDefaultSectionSize(70) 
        self.table_widget.setStyleSheet("QTableView { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; }")
        
        db = QSqlDatabase.database("SettingsDB")
        self.model = PostSqlModel(self, db)
        self.model.setTable("queue_posts")
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        
        self.model.setHeaderData(0, Qt.Orientation.Horizontal, "Giờ sẽ đăng")
        self.model.setHeaderData(1, Qt.Orientation.Horizontal, "Từ khóa / Nguồn")
        self.model.setHeaderData(2, Qt.Orientation.Horizontal, "Nội dung")
        self.model.setHeaderData(3, Qt.Orientation.Horizontal, "Media")
        
        self.table_widget.setModel(self.model)
        # Hide extra columns (video_path, image_ids)
        for col in range(4, self.model.columnCount()):
            self.table_widget.hideColumn(col)
            
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table_widget.setColumnWidth(0, 120) # Giờ sẽ đăng
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table_widget.setColumnWidth(1, 200) # Từ khóa
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Nội dung
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table_widget.setColumnWidth(3, 100) # Media
        
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
        
        self.refresh_table()

    def update_data(self, new_list=None):
        self.refresh_table()

    def refresh_table(self):
        # Sort by time ascending (column 0)
        self.model.setSort(0, Qt.SortOrder.AscendingOrder)
        self.model.select()

    def edit_queue_time(self):
        selected_indexes = self.table_widget.selectionModel().selectedRows()
        if not selected_indexes: return
        row = selected_indexes[0].row()
        current_time = self.model.data(self.model.index(row, 0))
        
        dialog = EditTimeDialog(current_time, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.model.setData(self.model.index(row, 0), dialog.get_new_time())
            self.model.submitAll()
            self.refresh_table()

    def delete_queue_item(self):
        selected_indexes = self.table_widget.selectionModel().selectedRows()
        if not selected_indexes: return
        
        if QMessageBox.question(self, 'Xác nhận', f'Bạn có chắc chắn muốn xóa {len(selected_indexes)} mục?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            for index in sorted(selected_indexes, key=lambda x: x.row(), reverse=True):
                self.model.removeRow(index.row())
            self.model.submitAll()
            self.refresh_table()