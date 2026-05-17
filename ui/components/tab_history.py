# ui/components/tab_history.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView
from PySide6.QtSql import QSqlTableModel, QSqlDatabase
from PySide6.QtCore import Qt

class TabHistory(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.table_posted_history = QTableView()
        
        # Kết nối tới SettingsDB đã được khởi tạo trong main.py
        db = QSqlDatabase.database("SettingsDB")
        self.model = QSqlTableModel(self, db)
        self.model.setTable("history_posts")
        
        # Thiết lập header theo yêu cầu
        self.model.setHeaderData(0, Qt.Orientation.Horizontal, "Thời gian Đăng")
        self.model.setHeaderData(1, Qt.Orientation.Horizontal, "Nguồn / Từ khóa")
        self.model.setHeaderData(2, Qt.Orientation.Horizontal, "Nội dung")
        self.model.setHeaderData(3, Qt.Orientation.Horizontal, "Loại đăng")
        
        # Nạp dữ liệu
        self.model.select()
        
        # Sắp xếp theo ID giảm dần (để bài mới nhất lên trên)
        self.model.setSort(self.model.fieldIndex("rowid"), Qt.SortOrder.DescendingOrder)
        self.model.select()

        self.table_posted_history.setModel(self.model)
        
        # Cấu hình giao diện bảng
        self.table_posted_history.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_posted_history.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_posted_history.verticalHeader().setVisible(False)
        
        # Ẩn các cột thừa (nếu có trong bảng, thường từ cột 4 trở đi)
        for col in range(4, self.model.columnCount()):
            self.table_posted_history.hideColumn(col)
            
        header = self.table_posted_history.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table_posted_history.setColumnWidth(0, 150)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table_posted_history.setColumnWidth(1, 200)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table_posted_history.setColumnWidth(3, 150)
        
        layout.addWidget(self.table_posted_history)

    def refresh_table(self, history_data_list=None):
        """Làm mới dữ liệu trực tiếp từ Database"""
        self.model.select()