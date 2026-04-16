# ui/dialogs/schedule_settings.py
import re
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTimeEdit, QSpinBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox)
from PyQt6.QtCore import QTime, Qt
from PyQt6.QtGui import QFont, QColor
from config.settings import MODERN_STYLE

class EditTimeDialog(QDialog):
    def __init__(self, current_time_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✏️ Sửa giờ đăng")
        self.resize(300, 150)
        self.setStyleSheet(MODERN_STYLE)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Nhập giờ mới cho bài viết này:</b>"))
        self.time_picker = QTimeEdit()
        self.time_picker.setDisplayFormat("HH:mm")
        parsed_time = QTime.fromString(current_time_str, "HH:mm")
        if parsed_time.isValid(): self.time_picker.setTime(parsed_time)
        layout.addWidget(self.time_picker)
        
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Hủy"); self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok = QPushButton("Lưu"); self.btn_ok.setStyleSheet("background-color: #22c55e; color: white;")
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_cancel); btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)

    def get_new_time(self): return self.time_picker.time().toString("HH:mm")

class ScheduleDialog(QDialog):
    def __init__(self, schedule_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📅 Cài đặt Khung giờ Bot Auto A-Z")
        self.resize(500, 450)
        self.setStyleSheet(MODERN_STYLE)
        self.initUI()
        self.load_schedule(schedule_str)

    def initUI(self):
        layout = QVBoxLayout(self)
        
        input_layout = QHBoxLayout()
        self.time_picker = QTimeEdit()
        self.time_picker.setDisplayFormat("HH:mm")
        self.time_picker.setTime(QTime.currentTime())
        self.time_picker.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.time_picker.setMinimumHeight(40)
        
        self.spin_time_count = QSpinBox()
        self.spin_time_count.setRange(1, 50)
        self.spin_time_count.setPrefix("Số bài: ")
        self.spin_time_count.setFont(QFont("Segoe UI", 13))
        self.spin_time_count.setMinimumHeight(40)
        
        self.btn_add = QPushButton('➕ Thêm Lịch')
        self.btn_add.setStyleSheet("background-color: #0ea5e9; color: white; font-weight: bold; min-height: 40px;")
        self.btn_add.clicked.connect(self.add_time)
        
        input_layout.addWidget(self.time_picker)
        input_layout.addWidget(self.spin_time_count)
        input_layout.addWidget(self.btn_add)
        layout.addLayout(input_layout)

        self.table_times = QTableWidget(0, 3)
        self.table_times.setHorizontalHeaderLabels(["⏰ Khung Giờ", "📝 Số bài", "Thao tác"])
        self.table_times.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_times.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_times.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_times.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table_times.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_times.setAlternatingRowColors(True)
        self.table_times.verticalHeader().setVisible(False)
        self.table_times.verticalHeader().setDefaultSectionSize(50) 
        self.table_times.setStyleSheet("QTableWidget { border: 1px solid #cbd5e1; border-radius: 8px; background-color: #ffffff; alternate-background-color: #f8fafc; font-size: 15px; } QHeaderView::section { background-color: #f1f5f9; border: none; border-bottom: 2px solid #cbd5e1; font-weight: bold; color: #334155; padding: 10px; }")
        layout.addWidget(self.table_times)

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Hủy bỏ")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save = QPushButton("💾 Lưu Cài Đặt")
        self.btn_save.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold;")
        self.btn_save.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def load_schedule(self, schedule_str):
        if not schedule_str: return
        for p in schedule_str.split(','):
            match = re.search(r"(\d{2}:\d{2})(?:\s*\(x(\d+)\))?", p.strip())
            if match:
                time_val = match.group(1)
                count_val = match.group(2) if match.group(2) else "1"
                self._insert_row(time_val, count_val)

    def add_time(self):
        time_str = self.time_picker.time().toString("HH:mm")
        count_str = str(self.spin_time_count.value())
        for i in range(self.table_times.rowCount()):
            if self.table_times.item(i, 0).data(Qt.ItemDataRole.UserRole) == time_str:
                QMessageBox.warning(self, "Lỗi trùng lặp", f"Khung giờ {time_str} đã có trong danh sách rồi!")
                return
        self._insert_row(time_str, count_str)

    def _insert_row(self, time_val, count_val):
        row = self.table_times.rowCount()
        self.table_times.insertRow(row)
        
        it_t = QTableWidgetItem(f"{time_val}")
        it_t.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        it_t.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        it_t.setForeground(QColor("#2563eb"))
        it_t.setData(Qt.ItemDataRole.UserRole, time_val)
        
        it_c = QTableWidgetItem(f"{count_val} bài")
        it_c.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        it_c.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        it_c.setForeground(QColor("#475569"))
        it_c.setData(Qt.ItemDataRole.UserRole, count_val)

        btn_del = QPushButton("❌ Xóa")
        btn_del.setStyleSheet("QPushButton { background-color: #fee2e2; color: #ef4444; border: none; padding: 6px 10px; border-radius: 6px; font-weight: bold; margin: 4px; } QPushButton:hover { background-color: #fca5a5; }")
        btn_del.clicked.connect(self.delete_row)
        
        self.table_times.setItem(row, 0, it_t)
        self.table_times.setItem(row, 1, it_c)
        self.table_times.setCellWidget(row, 2, btn_del)

    def delete_row(self):
        button = self.sender()
        if button:
            for row in range(self.table_times.rowCount()):
                if self.table_times.cellWidget(row, 2) == button:
                    self.table_times.removeRow(row)
                    break

    def get_schedule_string(self):
        times = []
        for i in range(self.table_times.rowCount()):
            t = self.table_times.item(i, 0).data(Qt.ItemDataRole.UserRole)
            c = self.table_times.item(i, 1).data(Qt.ItemDataRole.UserRole)
            times.append(f"{t} (x{c})" if int(c) > 1 else t)
        return ", ".join(times)