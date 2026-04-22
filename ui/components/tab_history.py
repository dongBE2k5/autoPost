# ui/components/tab_history.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView

class TabHistory(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.table_posted_history = QTableWidget(0, 4)
        self.table_posted_history.setHorizontalHeaderLabels(["Thời gian Đăng", "Nguồn", "Nội dung", "Loại đăng"])
        self.table_posted_history.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_posted_history)

    def refresh_table(self, history_data_list):
        """Nhận data từ DB (thông qua Controller) và vẽ lên bảng"""
        self.table_posted_history.setRowCount(0) 
        for i, record in enumerate(reversed(history_data_list)):
            self.table_posted_history.insertRow(i)
            self.table_posted_history.setItem(i, 0, QTableWidgetItem(record.get('post_time', '')))
            
            kw_display = f"🖼️ {record.get('keyword', '')}" if record.get('image_path') else record.get("keyword", "")
            self.table_posted_history.setItem(i, 1, QTableWidgetItem(kw_display))
            self.table_posted_history.setItem(i, 2, QTableWidgetItem(record.get("content", "").replace('\n', ' ')))
            self.table_posted_history.setItem(i, 3, QTableWidgetItem(record.get("mode", "")))