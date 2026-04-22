# ui/main_window.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel, 
                             QInputDialog, QLineEdit, QSystemTrayIcon, QStyle)
from PySide6.QtCore import pyqtSignal

from config.settings import MODERN_STYLE, ADMIN_PASSWORD
from ui.dialogs.toast import CustomToast

# Import các components (Tabs) vừa tách
from ui.components.tab_dashboard import TabDashboard
from ui.components.tab_guide import TabGuide
from ui.components.tab_history import TabHistory
from ui.components.tab_settings import TabSettings
from ui.components.tab_post_manager import TabPostManager

class MainWindow(QWidget):
    request_post_now = pyqtSignal(object, str, bool) 
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet(MODERN_STYLE)
        
        self.drafts_list = []
        self.queue_list = []
        
        self.initUI()
        self.setup_tray_icon()

    def initUI(self):
        self.setWindowTitle('Facebook Auto-Post Manager PRO (MVC Fully Refactored)')
        self.resize(1400, 850) 
        self.root_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        
        # 1. Nhúng các Tab vào MainWindow
        self.tab_dashboard = TabDashboard(self)
        self.tab_post_manager = TabPostManager() # <--- THÊM DÒNG NÀY
        self.tab_guide = TabGuide()
        self.tab_history = TabHistory()
        self.tab_settings = TabSettings()
        
        self.tab_widget.addTab(self.tab_dashboard, "Bảng Điều Khiển")
        self.tab_widget.addTab(self.tab_post_manager, "Quản lý Facebook")
        self.tab_widget.addTab(self.tab_guide, "Hướng Dẫn")
        self.tab_widget.addTab(self.tab_history, "Lịch sử Đăng")
        self.tab_widget.addTab(self.tab_settings, "Thiết Lập")

        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.root_layout.addWidget(self.tab_widget)
        
        self.status_label = QLabel(" Trạng thái: 🟢 Ready.")
        self.root_layout.addWidget(self.status_label)

    def on_tab_changed(self, index):
        if index == 4: # Tab Cài đặt
            password, ok = QInputDialog.getText(self, "Quản trị", "Mật khẩu: (admin)", QLineEdit.EchoMode.Password)
            if not ok or password != ADMIN_PASSWORD:
                self.tab_widget.setCurrentIndex(0) 

    # --- CÁC HÀM TIỆN ÍCH CHUNG (Sử dụng bởi Controller) ---
    def show_notification(self, title, message, is_error=False):
        if self.tray_icon.isVisible() and self.isHidden():
            icon = QSystemTrayIcon.MessageIcon.Critical if is_error else QSystemTrayIcon.MessageIcon.Information
            self.tray_icon.showMessage(title, message, icon, 3500)
        else:
            CustomToast(self, title, message, is_error)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.tray_icon.show() 

    def closeEvent(self, event):
        event.accept()