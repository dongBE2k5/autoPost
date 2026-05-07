from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QHBoxLayout, QPushButton)
from PySide6.QtCore import Qt

class TabTokens(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Thanh trạng thái / Tổng quan
        top_layout = QHBoxLayout()
        self.lbl_total = QLabel("Tổng Token: 0")
        self.lbl_total.setStyleSheet("font-size: 16px; font-weight: bold; color: #8b5cf6;")
        
        self.btn_refresh = QPushButton("🔄 Làm mới")
        self.btn_refresh.setStyleSheet("background-color: #3b82f6; color: white; padding: 5px 15px; border-radius: 4px;")
        
        top_layout.addWidget(self.lbl_total)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_refresh)
        layout.addLayout(top_layout)

        # Bảng thống kê
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Thời gian", "Hoạt động", "Token Đầu vào", "Token Đầu ra", "Tổng"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.table)
        
    def refresh_table(self, history_data):
        """Cập nhật bảng với dữ liệu thống kê mới"""
        self.table.setRowCount(0)
        total_all = 0
        
        for idx, record in enumerate(history_data):
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(str(record.get('timestamp', ''))))
            
            # Translate operation to display name
            op_name = record.get('operation', '')
            mapping = {
                "transcribe": "Nhận dạng giọng nói",
                "trend_analysis": "Phân tích Trend",
                "content_writing": "Viết Content",
                "image_prompt": "Tạo Prompt Ảnh",
                "image_generation": "Tạo Ảnh AI"
            }
            display_op = mapping.get(op_name, op_name)
            
            self.table.setItem(idx, 1, QTableWidgetItem(display_op))
            self.table.setItem(idx, 2, QTableWidgetItem(f"{record.get('input', 0):,}"))
            self.table.setItem(idx, 3, QTableWidgetItem(f"{record.get('output', 0):,}"))
            
            total = record.get('total', 0)
            total_all += total
            self.table.setItem(idx, 4, QTableWidgetItem(f"{total:,}"))
            
            # Căn lề số sang phải
            for col in range(2, 5):
                self.table.item(idx, col).setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.lbl_total.setText(f"Tổng Token (tất cả lịch sử): {total_all:,}")
