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

# --- GIAO DIỆN (MODERN STYLE) ---
MODERN_STYLE = (
    "QWidget { font-family: 'Segoe UI', -apple-system, sans-serif; font-size: 14px; color: #334155; }\n"
    "AutoPostApp { background-color: #f8fafc; }\n"
    "QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 8px; background: #ffffff; }\n"
    "QTabBar::tab { background: #f1f5f9; border: 1px solid #e2e8f0; border-bottom-color: #e2e8f0; border-top-left-radius: 8px; border-top-right-radius: 8px; padding: 12px 24px; margin-right: 4px; font-weight: 600; font-size: 14px; color: #64748b; }\n"
    "QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; color: #2563eb; }\n"
    "QTabBar::tab:hover:!selected { background: #e2e8f0; color: #0f172a; }\n"
    "QGroupBox { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 15px; padding-top: 20px; font-weight: bold; }\n"
    "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 15px; padding: 0 5px; color: #1e293b; font-size: 15px; background-color: transparent; }\n"
    "QLineEdit, QTextEdit, QTimeEdit, QSpinBox, QComboBox { border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; background-color: #ffffff; color: #0f172a; font-size: 14px; min-height: 24px; }\n"
    "QLineEdit:focus, QTextEdit:focus, QTimeEdit:focus, QSpinBox:focus, QComboBox:focus { border: 1px solid #3b82f6; }\n"
    "QPushButton { border-radius: 6px; padding: 10px 16px; font-weight: bold; border: none; font-size: 14px; }\n"
    "QPushButton:hover { opacity: 0.9; }\n"
    "QPushButton:disabled { background-color: #cbd5e1; color: #94a3b8; }\n"
    "QTableWidget { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; gridline-color: #f1f5f9; selection-background-color: #eff6ff; selection-color: #1e40af; }\n"
    "QHeaderView::section { background-color: #f8fafc; padding: 10px; border: none; border-bottom: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; font-weight: bold; color: #475569; }\n"
    "QRadioButton { font-weight: bold; color: #1e293b; padding: 12px 15px; border: 2px solid #e2e8f0; border-radius: 8px; background-color: #f8fafc; }\n"
    "QRadioButton:hover { border-color: #cbd5e1; background-color: #f1f5f9; }\n"
    "QRadioButton:checked { border-color: #3b82f6; background-color: #eff6ff; color: #1d4ed8; }\n"
    "QRadioButton::indicator { width: 18px; height: 18px; }\n"
    "QCheckBox { font-weight: bold; color: #1e293b; padding: 5px; }\n"
    "QFrame#MediaFrame { background-color: #0f172a; border-radius: 8px; } QFrame#MediaFrame QLabel { color: #f1f5f9; font-weight: bold; }\n"
)