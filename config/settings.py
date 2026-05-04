# config/settings.py
import os
import platform
import imageio_ffmpeg
import shutil

# --- DATABASE ---
DB_FILE = 'data/autopost_database.db' # Chuyển DB vào thư mục data
ADMIN_PASSWORD = "admin"

# --- FFMPEG (Tự động cấu hình đa nền tảng) ---
def setup_ffmpeg():
    ffmpeg_hidden_path = imageio_ffmpeg.get_ffmpeg_exe()
    ext = ".exe" if platform.system() == "Windows" else ""
    ffmpeg_local_path = os.path.join(os.getcwd(), f"ffmpeg{ext}")

    if not os.path.exists(ffmpeg_local_path):
        try:
            shutil.copy(ffmpeg_hidden_path, ffmpeg_local_path)
            if platform.system() != "Windows":
                os.chmod(ffmpeg_local_path, 0o755)
        except Exception as e:
            print(f"Lỗi khởi tạo FFmpeg: {e}")

# --- GIAO DIỆN (MODERN PREMIUM STYLE) ---
MODERN_STYLE = (
    "QWidget { font-family: 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; font-size: 14px; color: #1e293b; }\n"
    "AutoPostApp, QDialog { background-color: #f1f5f9; }\n"
    
    "QTabWidget::pane { border: 1px solid #cbd5e1; border-radius: 12px; background: #ffffff; }\n"
    "QTabBar::tab { background: transparent; border: none; border-bottom: 3px solid transparent; padding: 10px 20px; margin-right: 4px; font-weight: 700; font-size: 14px; color: #64748b; }\n"
    "QTabBar::tab:selected { background: transparent; border-bottom: 3px solid #2563eb; color: #1d4ed8; }\n"
    "QTabBar::tab:hover:!selected { color: #0f172a; border-bottom: 3px solid #cbd5e1; }\n"
    
    "QGroupBox { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; margin-top: 20px; padding-top: 20px; font-weight: 700; }\n"
    "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 20px; top: 0px; padding: 0 5px; color: #2563eb; font-size: 14px; font-weight: 800; background-color: transparent; }\n"
    
    "QLineEdit, QTextEdit, QTimeEdit, QSpinBox, QComboBox { border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; background-color: #f8fafc; color: #0f172a; font-size: 14px; }\n"
    "QLineEdit:focus, QTextEdit:focus, QTimeEdit:focus, QSpinBox:focus, QComboBox:focus { border: 1.5px solid #3b82f6; background-color: #ffffff; }\n"
    
    "QPushButton { border-radius: 6px; padding: 8px 16px; font-weight: bold; border: none; font-size: 14px; }\n"
    "QPushButton:disabled { background-color: #e2e8f0; color: #94a3b8; }\n"
    
    "QTableWidget { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; gridline-color: #f1f5f9; selection-background-color: #eff6ff; selection-color: #1e40af; }\n"
    "QHeaderView::section { background-color: #f8fafc; padding: 10px; border: none; border-bottom: 1.5px solid #e2e8f0; border-right: 1px solid #e2e8f0; font-weight: 800; color: #334155; font-size: 13px; }\n"
    
    "QRadioButton { font-weight: bold; color: #334155; padding: 8px 12px; border: 2px solid #e2e8f0; border-radius: 8px; background-color: #f8fafc; }\n"
    "QRadioButton:hover { border-color: #cbd5e1; background-color: #f1f5f9; }\n"
    "QRadioButton:checked { border-color: #2563eb; background-color: #eff6ff; color: #1d4ed8; }\n"
    "QRadioButton::indicator { width: 18px; height: 18px; }\n"
    
    "QCheckBox { font-weight: 600; color: #334155; padding: 6px; }\n"
    "QCheckBox::indicator { width: 20px; height: 20px; border: 1.5px solid #cbd5e1; border-radius: 4px; background-color: #f8fafc; }\n"
    "QCheckBox::indicator:checked { background-color: #2563eb; border-color: #2563eb; image: url(check.png); }\n"
    
    "QFrame#MediaFrame { background-color: #0f172a; border-radius: 12px; } QFrame#MediaFrame QLabel { color: #f8fafc; font-weight: bold; }\n"
    
    "QScrollBar:vertical { border: none; background: #f1f5f9; width: 10px; border-radius: 5px; }\n"
    "QScrollBar::handle:vertical { background: #cbd5e1; min-height: 20px; border-radius: 5px; }\n"
    "QScrollBar::handle:vertical:hover { background: #94a3b8; }\n"
    "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }\n"
)