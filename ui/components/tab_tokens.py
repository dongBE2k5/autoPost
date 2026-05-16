from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QHBoxLayout, QPushButton, QMessageBox,
                             QScrollArea, QFrame, QGridLayout, QFileDialog, QTabWidget, QComboBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QBrush, QFont
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice

# --- CONSTANTS FOR DRY PRINCIPLE ---
OPERATION_MAP = {
    "transcribe": "Nhận dạng giọng nói",
    "trend_analysis": "Phân tích Trend",
    "content_writing": "Viết Content",
    "image_prompt": "Tạo Prompt Ảnh",
    "image_generation": "Tạo Ảnh AI"
}

# tuple: (Background Color, Text Color, Chart Color)
BADGE_COLORS = {
    "Viết Content": ("#dcfce7", "#166534", QColor("#22c55e")), 
    "Tạo Ảnh AI": ("#ffedd5", "#9a3412", QColor("#f97316")),   
    "Tạo Prompt Ảnh": ("#dbeafe", "#1e40af", QColor("#3b82f6")), 
    "Phân tích Trend": ("#f3e8ff", "#6b21a8", QColor("#a855f7")), 
    "Nhận dạng giọng nói": ("#f1f5f9", "#334155", QColor("#64748b")) 
}

class TabTokens(QWidget):
    def __init__(self):
        super().__init__()
        self.token_manager = None  # Sẽ được set từ controller
        self.current_history_data = []
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        
        # Tạo tab con
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabWidget::pane { border: 1px solid #cbd5e1; border-radius: 8px; background: white; }")
        
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
        stats_frame.setStyleSheet("QFrame { background-color: #f8fafc; border-radius: 8px; padding: 10px; }")
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(15)
        
        # Row 1: Tổng token, Số bài viết
        self.lbl_total_tokens = self._create_stat_label("Tổng Token (All-time)", "0", bg_color="#f3e8ff", text_color="#6b21a8", border_color="#c084fc")
        self.lbl_total_posts = self._create_stat_label("Tổng Bài Viết", "0", bg_color="#e0f2fe", text_color="#0369a1", border_color="#7dd3fc")
        stats_layout.addWidget(self.lbl_total_tokens, 0, 0)
        stats_layout.addWidget(self.lbl_total_posts, 0, 1)
        
        # Row 2: Số video, Số lần chạy
        self.lbl_total_videos = self._create_stat_label("Tổng Video", "0", bg_color="#ffedd5", text_color="#c2410c", border_color="#fdba74")
        self.lbl_num_runs = self._create_stat_label("Số Lần Chạy", "0", bg_color="#dcfce7", text_color="#15803d", border_color="#86efac")
        stats_layout.addWidget(self.lbl_total_videos, 1, 0)
        stats_layout.addWidget(self.lbl_num_runs, 1, 1)
        
        # Row 3: Trung bình
        self.lbl_avg_token = self._create_stat_label("Trung Bình Token/Bài", "0", bg_color="#f1f5f9", text_color="#334155", border_color="#94a3b8")
        stats_layout.addWidget(self.lbl_avg_token, 2, 0, 1, 2)
        
        layout.addWidget(stats_frame)
        
        # Khu vực chi tiết & Biểu đồ
        detail_label = QLabel("Phân bổ Token theo Hoạt động (Click vào biểu đồ để xem chi tiết):")
        detail_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 15px;")
        layout.addWidget(detail_label)
        
        chart_table_layout = QHBoxLayout()
        
        # Biểu đồ tròn (Pie Chart) - Nền trắng tinh tế
        self.pie_series = QPieSeries()
        self.pie_series.setHoleSize(0.4) # Donut chart style
        
        self.chart = QChart()
        self.chart.addSeries(self.pie_series)
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        self.chart.legend().setFont(QFont("Arial", 10))
        self.chart.setMargins(self.chart.margins() * 0)
        
        # Sửa màu nền thành trắng tinh
        self.chart.setBackgroundVisible(True)
        self.chart.setBackgroundBrush(QBrush(QColor("#ffffff")))
        
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumSize(350, 250)
        self.chart_view.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px;")
        
        # Bảng dữ liệu chi tiết
        self.table_ops = QTableWidget()
        self.table_ops.setColumnCount(5)
        self.table_ops.setHorizontalHeaderLabels(["Hoạt động", "Token Đầu vào", "Token Đầu ra", "Tổng", "% Tổng"])
        self.table_ops.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_ops.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_ops.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_ops.setMinimumSize(400, 250)
        self.table_ops.itemDoubleClicked.connect(self._on_table_ops_double_clicked)
        self.table_ops.setStyleSheet("QTableWidget { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; }")
        
        chart_table_layout.addWidget(self.chart_view, stretch=1)
        chart_table_layout.addWidget(self.table_ops, stretch=1)
        
        layout.addLayout(chart_table_layout)
        
        return widget
    
    def _create_detail_tab(self):
        """Tạo tab chi tiết lịch sử"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Thanh công cụ & Filter Bar
        toolbar_layout = QHBoxLayout()
        
        self.btn_refresh_detail = QPushButton("🔄 Làm mới")
        toolbar_layout.addWidget(self.btn_refresh_detail)
        
        toolbar_layout.addSpacing(20)
        
        toolbar_layout.addWidget(QLabel("<b>🔍 Lọc Hoạt động:</b>"))
        self.cb_activity = QComboBox()
        self.cb_activity.addItem("Tất cả")
        self.cb_activity.addItems(list(OPERATION_MAP.values()))
        self.cb_activity.setStyleSheet("padding: 5px; border-radius: 4px; border: 1px solid #cbd5e1;")
        self.cb_activity.setMinimumWidth(150)
        self.cb_activity.currentTextChanged.connect(self.apply_filter)
        toolbar_layout.addWidget(self.cb_activity)
        
        toolbar_layout.addSpacing(10)
        
        toolbar_layout.addWidget(QLabel("<b>📅 Lọc Thời gian:</b>"))
        self.cb_time_filter = QComboBox()
        self.cb_time_filter.addItems(["Tất cả thời gian", "Hôm nay", "Tháng này", "Năm nay"])
        self.cb_time_filter.setStyleSheet("padding: 5px; border-radius: 4px; border: 1px solid #cbd5e1;")
        self.cb_time_filter.setMinimumWidth(130)
        self.cb_time_filter.currentTextChanged.connect(self.apply_filter)
        toolbar_layout.addWidget(self.cb_time_filter)
        
        toolbar_layout.addSpacing(10)
        
        self.btn_clear_filter = QPushButton("❌ Xóa lọc")
        self.btn_clear_filter.setStyleSheet("background-color: #f1f5f9; color: #ef4444; border: 1px solid #cbd5e1;")
        self.btn_clear_filter.clicked.connect(self.clear_filters)
        toolbar_layout.addWidget(self.btn_clear_filter)
        
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
        self.table_detail.setStyleSheet("QTableWidget { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; }")
        layout.addWidget(self.table_detail)
        
        return widget
    
    @staticmethod
    def _create_stat_label(title, value, bg_color="#ffffff", text_color="#1e293b", border_color="#cbd5e1"):
        """Tạo widget hiển thị thống kê"""
        container = QWidget()
        container.setObjectName("StatCard")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 15, 20, 15)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5) # Thu gọn khoảng cách
        
        title_label = QLabel(title)
        value_label = QLabel(value)
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)
        text_layout.addStretch()
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        title_label.setStyleSheet(f"font-size: 14px; color: {text_color}; font-weight: bold; background: transparent; border: none; padding-bottom: 2px;")
        value_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {text_color}; background: transparent; border: none; padding-bottom: 6px;")
        
        container.setStyleSheet(f"QWidget#StatCard {{ background-color: {bg_color}; border-radius: 10px; border: 1.5px solid {border_color}; border-left: 6px solid {border_color}; }}")
            
        return container
    
    def clear_filters(self):
        """Xóa toàn bộ các bộ lọc"""
        self.cb_activity.setCurrentIndex(0)
        self.cb_time_filter.setCurrentIndex(0)

    def apply_filter(self):
        """Lọc bảng chi tiết dựa trên các ComboBox"""
        target_activity = self.cb_activity.currentText()
        target_time = self.cb_time_filter.currentText()
        
        from datetime import datetime
        now = datetime.now()
        
        for i in range(self.table_detail.rowCount()):
            item = self.table_detail.item(i, 1) # Hoạt động
            time_item = self.table_detail.item(i, 0) # Thời gian
            if not item or not time_item:
                continue
            
            # Check activity
            match_activity = (target_activity == "Tất cả" or item.text() == target_activity)
            
            # Check time
            match_time = True
            if target_time != "Tất cả thời gian":
                try:
                    # Định dạng thời gian: "%d/%m/%Y %H:%M:%S"
                    row_time = datetime.strptime(time_item.text().strip(), "%d/%m/%Y %H:%M:%S")
                    if target_time == "Hôm nay":
                        match_time = (row_time.date() == now.date())
                    elif target_time == "Tháng này":
                        match_time = (row_time.year == now.year and row_time.month == now.month)
                    elif target_time == "Năm nay":
                        match_time = (row_time.year == now.year)
                except Exception:
                    pass # Bỏ qua nếu lỗi parse
                    
            if match_activity and match_time:
                self.table_detail.setRowHidden(i, False)
            else:
                self.table_detail.setRowHidden(i, True)

    def _on_pie_slice_clicked(self, slice):
        """Xử lý khi click vào mảnh biểu đồ -> Chuyển sang chi tiết và lọc"""
        activity_name = slice.label().split(" (")[0]
        self.tab_widget.setCurrentIndex(1)
        self.cb_activity.setCurrentText(activity_name)

    def _on_table_ops_double_clicked(self, item):
        """Xử lý khi click đúp vào bảng tóm tắt -> Chuyển sang chi tiết và lọc"""
        row = item.row()
        activity_name = self.table_ops.item(row, 0).text()
        self.tab_widget.setCurrentIndex(1)
        self.cb_activity.setCurrentText(activity_name)

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
        self._update_stat_label(self.lbl_total_tokens, f"{total_tokens:,}")
        self._update_stat_label(self.lbl_total_posts, f"{total_posts:,}")
        self._update_stat_label(self.lbl_total_videos, f"{total_videos:,}")
        self._update_stat_label(self.lbl_num_runs, f"{num_runs}")
        self._update_stat_label(self.lbl_avg_token, f"{avg_token:,}")
        
        # Cập nhật bảng và biểu đồ
        self._update_operations_table_and_chart(op_totals)
    
    @staticmethod
    def _update_stat_label(container, text):
        """Cập nhật text cho stat label"""
        text_layout = container.layout().itemAt(0).layout()
        if text_layout:
            value_label = text_layout.itemAt(1).widget()
            if isinstance(value_label, QLabel):
                value_label.setText(text)
    
    def _update_operations_table_and_chart(self, op_totals):
        """Cập nhật bảng chi tiết hoạt động và Biểu đồ tròn"""
        self.table_ops.setRowCount(0)
        self.pie_series.clear()
        
        if not op_totals:
            return
        
        total_all = sum(op.get("total", 0) for op in op_totals.values())
        
        idx = 0
        for op_name, op_data in op_totals.items():
            if op_data.get("total", 0) > 0:
                display_name = OPERATION_MAP.get(op_name, op_name)
                op_total = op_data.get('total', 0)
                pct = (op_total / total_all * 100) if total_all > 0 else 0
                
                # 1. Update Table
                self.table_ops.insertRow(idx)
                self.table_ops.setItem(idx, 0, QTableWidgetItem(display_name))
                self.table_ops.setItem(idx, 1, QTableWidgetItem(f"{op_data.get('input', 0):,}"))
                self.table_ops.setItem(idx, 2, QTableWidgetItem(f"{op_data.get('output', 0):,}"))
                self.table_ops.setItem(idx, 3, QTableWidgetItem(f"{op_total:,}"))
                self.table_ops.setItem(idx, 4, QTableWidgetItem(f"{pct:.1f}%"))
                
                for col in range(1, 5):
                    self.table_ops.item(idx, col).setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                # 2. Update Chart
                slice_label = f"{display_name} ({pct:.1f}%)"
                pie_slice = QPieSlice(slice_label, op_total)
                if display_name in BADGE_COLORS:
                    chart_color = BADGE_COLORS[display_name][2]
                    pie_slice.setBrush(chart_color)
                    
                # Highlight slices when hovered
                pie_slice.hovered.connect(lambda state, s=pie_slice: s.setExploded(state))
                # Interconnection on click
                pie_slice.clicked.connect(lambda s=pie_slice: self._on_pie_slice_clicked(s))
                
                self.pie_series.append(pie_slice)
                idx += 1
                
    @staticmethod
    def _create_badge_item(text):
        """Tạo QTableWidgetItem có style badge (SOLID Principle)"""
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if text in BADGE_COLORS:
            bg_color, fg_color, _ = BADGE_COLORS[text]
            item.setBackground(QColor(bg_color))
            item.setForeground(QColor(fg_color))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        return item
    
    def refresh_detail_table(self, history_data):
        """Cập nhật bảng chi tiết lịch sử"""
        self.table_detail.setRowCount(0)
        
        for idx, record in enumerate(history_data):
            self.table_detail.insertRow(idx)
            
            self.table_detail.setItem(idx, 0, QTableWidgetItem(str(record.get('timestamp', ''))))
            
            op_code = record.get('operation', '')
            display_op = OPERATION_MAP.get(op_code, op_code)
            
            # Sử dụng hàm tiện ích tạo Badge
            op_item = self._create_badge_item(display_op)
            self.table_detail.setItem(idx, 1, op_item)
            
            self.table_detail.setItem(idx, 2, QTableWidgetItem(f"{record.get('input', 0):,}"))
            self.table_detail.setItem(idx, 3, QTableWidgetItem(f"{record.get('output', 0):,}"))
            self.table_detail.setItem(idx, 4, QTableWidgetItem(f"{record.get('total', 0):,}"))
            self.table_detail.setItem(idx, 5, QTableWidgetItem(str(record.get('posts_generated', 0))))
            self.table_detail.setItem(idx, 6, QTableWidgetItem(str(record.get('videos_processed', 0))))
            
            # Căn lề số sang phải
            for col in range(2, 7):
                self.table_detail.item(idx, col).setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
        # Áp dụng lại bộ lọc hiện tại nếu có
        self.apply_filter()
    
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
