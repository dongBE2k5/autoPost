from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QHBoxLayout, QPushButton, QMessageBox,
                             QScrollArea, QFrame, QGridLayout, QFileDialog, QTabWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class TabTokens(QWidget):
    def __init__(self):
        super().__init__()
        self.token_manager = None  # Sẽ được set từ controller
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        
        # Tạo tab con
        self.tab_widget = QTabWidget()
        
        # Tab 1: Tóm tắt
        tab_summary = self._create_summary_tab()
        self.tab_widget.addTab(tab_summary, "Tóm Tắt")
        
        # Tab 2: Chi tiết
        tab_detail = self._create_detail_tab()
        self.tab_widget.addTab(tab_detail, "Chi Tiết")
        
        main_layout.addWidget(self.tab_widget)
    
    def _create_summary_tab(self):
        """Tạo tab tóm tắt thống kê"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Thanh công cụ
        toolbar_layout = QHBoxLayout()
        self.btn_refresh_summary = QPushButton("🔄 Làm mới")
        self.btn_clear = QPushButton("🗑️ Xóa lịch sử")
        self.btn_export = QPushButton("📥 Xuất CSV")
        
        toolbar_layout.addWidget(self.btn_refresh_summary)
        toolbar_layout.addWidget(self.btn_export)
        toolbar_layout.addWidget(self.btn_clear)
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Khu vực thống kê
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: #f0f4f8; border-radius: 8px; padding: 15px;")
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(15)
        
        # Row 1: Tổng token, Số bài viết
        self.lbl_total_tokens = self._create_stat_label("Tổng Token (All-time)", "0")
        self.lbl_total_posts = self._create_stat_label("Tổng Bài Viết", "0")
        stats_layout.addWidget(self.lbl_total_tokens, 0, 0)
        stats_layout.addWidget(self.lbl_total_posts, 0, 1)
        
        # Row 2: Số video, Số lần chạy
        self.lbl_total_videos = self._create_stat_label("Tổng Video", "0")
        self.lbl_num_runs = self._create_stat_label("Số Lần Chạy", "0")
        stats_layout.addWidget(self.lbl_total_videos, 1, 0)
        stats_layout.addWidget(self.lbl_num_runs, 1, 1)
        
        # Row 3: Trung bình
        self.lbl_avg_token = self._create_stat_label("Trung Bình Token/Bài", "0")
        stats_layout.addWidget(self.lbl_avg_token, 2, 0, 1, 2)
        
        layout.addWidget(stats_frame)
        
        # Biểu đồ chi tiết theo hoạt động
        detail_label = QLabel("Chi tiết Token theo Hoạt động:")
        detail_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 15px;")
        layout.addWidget(detail_label)
        
        self.table_ops = QTableWidget()
        self.table_ops.setColumnCount(5)
        self.table_ops.setHorizontalHeaderLabels(["Hoạt động", "Token Đầu vào", "Token Đầu ra", "Tổng", "% Tổng"])
        self.table_ops.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_ops.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_ops.setMaximumHeight(250)
        layout.addWidget(self.table_ops)
        
        layout.addStretch()
        return widget
    
    def _create_detail_tab(self):
        """Tạo tab chi tiết lịch sử"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Thanh công cụ
        toolbar_layout = QHBoxLayout()
        self.btn_refresh_detail = QPushButton("🔄 Làm mới")
        toolbar_layout.addWidget(self.btn_refresh_detail)
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Bảng chi tiết
        self.table_detail = QTableWidget()
        self.table_detail.setColumnCount(7)
        self.table_detail.setHorizontalHeaderLabels([
            "Thời gian", "Hoạt động", "Token Đầu vào", 
            "Token Đầu ra", "Tổng", "Bài viết", "Video"
        ])
        self.table_detail.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_detail.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_detail.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table_detail)
        
        return widget
    
    @staticmethod
    def _create_stat_label(title, value):
        """Tạo widget hiển thị thống kê"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #64748b;")
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #8b5cf6;")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        container.setStyleSheet("background-color: white; border-radius: 6px; border: 1px solid #e2e8f0;")
        return container
    
    def refresh_summary(self, summary_data):
        """Cập nhật tab tóm tắt"""
        if not summary_data:
            return
        
        total_tokens = summary_data.get("total_tokens", 0)
        total_posts = summary_data.get("total_posts", 0)
        total_videos = summary_data.get("total_videos", 0)
        avg_token = summary_data.get("avg_token_per_post", 0)
        num_runs = summary_data.get("num_runs", 0)
        op_totals = summary_data.get("operation_totals", {})
        
        # Cập nhật các label thống kê
        # Lấy value_label (con thứ 2) từ mỗi container
        self._update_stat_label(self.lbl_total_tokens, f"{total_tokens:,}")
        self._update_stat_label(self.lbl_total_posts, f"{total_posts:,}")
        self._update_stat_label(self.lbl_total_videos, f"{total_videos:,}")
        self._update_stat_label(self.lbl_num_runs, f"{num_runs}")
        self._update_stat_label(self.lbl_avg_token, f"{avg_token:,}")
        
        # Cập nhật bảng hoạt động
        self._update_operations_table(op_totals)
    
    @staticmethod
    def _update_stat_label(container, text):
        """Cập nhật text cho stat label"""
        labels = container.findChildren(QLabel)
        if len(labels) >= 2:
            labels[1].setText(text)  # Index 1 là value_label
    
    def _update_operations_table(self, op_totals):
        """Cập nhật bảng chi tiết hoạt động"""
        self.table_ops.setRowCount(0)
        
        if not op_totals:
            return
        
        total_all = sum(op.get("total", 0) for op in op_totals.values())
        
        mapping = {
            "transcribe": "Nhận dạng giọng nói",
            "trend_analysis": "Phân tích Trend",
            "content_writing": "Viết Content",
            "image_prompt": "Tạo Prompt Ảnh",
            "image_generation": "Tạo Ảnh AI"
        }
        
        idx = 0
        for op_name, op_data in op_totals.items():
            if op_data.get("total", 0) > 0:
                self.table_ops.insertRow(idx)
                
                display_name = mapping.get(op_name, op_name)
                self.table_ops.setItem(idx, 0, QTableWidgetItem(display_name))
                self.table_ops.setItem(idx, 1, QTableWidgetItem(f"{op_data.get('input', 0):,}"))
                self.table_ops.setItem(idx, 2, QTableWidgetItem(f"{op_data.get('output', 0):,}"))
                self.table_ops.setItem(idx, 3, QTableWidgetItem(f"{op_data.get('total', 0):,}"))
                
                pct = (op_data.get("total", 0) / total_all * 100) if total_all > 0 else 0
                self.table_ops.setItem(idx, 4, QTableWidgetItem(f"{pct:.1f}%"))
                
                # Căn lề
                for col in range(1, 5):
                    self.table_ops.item(idx, col).setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                idx += 1
    
    def refresh_detail_table(self, history_data):
        """Cập nhật bảng chi tiết lịch sử"""
        self.table_detail.setRowCount(0)
        
        for idx, record in enumerate(history_data):
            self.table_detail.insertRow(idx)
            
            self.table_detail.setItem(idx, 0, QTableWidgetItem(str(record.get('timestamp', ''))))
            
            mapping = {
                "transcribe": "Nhận dạng giọng nói",
                "trend_analysis": "Phân tích Trend",
                "content_writing": "Viết Content",
                "image_prompt": "Tạo Prompt Ảnh",
                "image_generation": "Tạo Ảnh AI"
            }
            display_op = mapping.get(record.get('operation', ''), record.get('operation', ''))
            self.table_detail.setItem(idx, 1, QTableWidgetItem(display_op))
            
            self.table_detail.setItem(idx, 2, QTableWidgetItem(f"{record.get('input', 0):,}"))
            self.table_detail.setItem(idx, 3, QTableWidgetItem(f"{record.get('output', 0):,}"))
            self.table_detail.setItem(idx, 4, QTableWidgetItem(f"{record.get('total', 0):,}"))
            self.table_detail.setItem(idx, 5, QTableWidgetItem(str(record.get('posts_generated', 0))))
            self.table_detail.setItem(idx, 6, QTableWidgetItem(str(record.get('videos_processed', 0))))
            
            # Căn lề số sang phải
            for col in range(2, 7):
                self.table_detail.item(idx, col).setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    
    def set_token_manager(self, manager):
        """Set token history manager"""
        self.token_manager = manager
    
    def show_clear_confirm(self):
        """Hiển thị dialog xác nhận xóa lịch sử"""
        reply = QMessageBox.warning(
            self, 
            "Xác nhận xóa", 
            "Bạn có chắc muốn xóa toàn bộ lịch sử token?\n\nHành động này không thể hoàn tác!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    def show_export_success(self, filepath):
        """Hiển thị thông báo xuất thành công"""
        QMessageBox.information(
            self,
            "Thành công",
            f"Đã xuất dữ liệu thành công:\n{filepath}"
        )
