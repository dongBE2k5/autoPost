# ui/components/tab_post_manager.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
                             QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
import datetime

class TabPostManager(QWidget):
    # Phát tín hiệu ra cho Controller xử lý
    refresh_requested = pyqtSignal()
    delete_requested = pyqtSignal(str) # Truyền Post ID
    
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        
        # --- Thanh công cụ phía trên ---
        toolbar_layout = QHBoxLayout()
        
        self.lbl_status = QLabel("Trạng thái: Chưa tải dữ liệu.")
        self.lbl_status.setStyleSheet("color: #64748b; font-style: italic;")
        
        self.btn_refresh = QPushButton("🔄 Tải lại Danh sách Bài viết")
        self.btn_refresh.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 10px 20px;")
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        
        toolbar_layout.addWidget(self.lbl_status)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_refresh)
        layout.addLayout(toolbar_layout)

        # --- Bảng hiển thị bài viết ---
        self.table_posts = QTableWidget(0, 5)
        self.table_posts.setHorizontalHeaderLabels(["ID Bài viết", "Trạng thái", "Thời gian", "Nội dung (Trích dẫn)", "Thao tác"])
        self.table_posts.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_posts.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        header = self.table_posts.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table_posts.verticalHeader().setDefaultSectionSize(60)
        layout.addWidget(self.table_posts)

    def populate_table(self, posts_data):
        """Hàm này được Controller gọi để nhét dữ liệu từ Facebook vào bảng"""
        self.table_posts.setRowCount(0)
        
        for row, post in enumerate(posts_data):
            self.table_posts.insertRow(row)
            
            # ID
            post_id = post.get("id", "N/A")
            self.table_posts.setItem(row, 0, QTableWidgetItem(post_id))
            
            # Trạng thái (Live hoặc Lên lịch)
            is_published = post.get("is_published", True)
            status_text = "🟢 Đã đăng (Live)" if is_published else "⏳ Đã lên lịch"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor("#16a34a") if is_published else QColor("#f59e0b"))
            status_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            self.table_posts.setItem(row, 1, status_item)
            
            # Thời gian (Chuyển chuẩn ISO 8601 sang format dễ nhìn)
            raw_time = post.get("created_time", "")
            try:
                parsed_time = datetime.datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%S%z")
                time_str = parsed_time.strftime("%d/%m/%Y %H:%M")
            except:
                time_str = raw_time
            self.table_posts.setItem(row, 2, QTableWidgetItem(time_str))
            
            # Nội dung trích dẫn
            msg = post.get("message", "Không có văn bản")
            short_msg = msg[:80] + "..." if len(msg) > 80 else msg
            
            # Nếu có ảnh thì thêm icon
            if post.get("full_picture"):
                short_msg = f"🖼️ {short_msg}"
                
            self.table_posts.setItem(row, 3, QTableWidgetItem(short_msg.replace('\n', ' ')))
            
            # Nút Thao tác (Mở Link và Xóa)
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 5, 5, 5)
            
            btn_view = QPushButton("🔗 Xem")
            btn_view.setStyleSheet("background-color: #f1f5f9; color: #334155; padding: 5px 10px;")
            # Mở link fb.com/ID_BÀI_VIẾT
            btn_view.clicked.connect(lambda checked, pid=post_id: self._open_browser(pid))
            
            btn_delete = QPushButton("🗑️ Xóa")
            btn_delete.setStyleSheet("background-color: #fee2e2; color: #ef4444; padding: 5px 10px;")
            btn_delete.clicked.connect(lambda checked, pid=post_id: self.delete_requested.emit(pid))
            
            action_layout.addWidget(btn_view)
            action_layout.addWidget(btn_delete)
            self.table_posts.setCellWidget(row, 4, action_widget)
            
        self.lbl_status.setText(f"Trạng thái: Tải thành công {len(posts_data)} bài viết.")

    def set_loading_state(self):
        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("⏳ Đang tải từ Facebook...")
        self.lbl_status.setText("Trạng thái: Đang kết nối Facebook API...")
        
    def reset_loading_state(self):
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("🔄 Tải lại Danh sách Bài viết")

    def _open_browser(self, post_id):
        import webbrowser
        webbrowser.open(f"https://facebook.com/{post_id}")