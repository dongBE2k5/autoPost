# main.py
import sys
from PyQt6.QtWidgets import QApplication

# Import các thành phần từ kiến trúc MVC
from config.settings import setup_ffmpeg
from config.settings_manager import SettingsManager
from ui.main_window import MainWindow
from controllers.main_controller import MainController

def main():
    # 1. Setup môi trường hệ thống
    setup_ffmpeg()

    # 2. Khởi tạo Application của PyQt
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 

    # 3. Khởi tạo Database / Cấu hình (Model)
    settings_manager = SettingsManager()

    # 4. Khởi tạo Giao diện (View)
    view = MainWindow()

    # 5. Khởi tạo "Não bộ" điều phối (Controller) và gắn nó vào View & Model
    controller = MainController(view=view, settings_manager=settings_manager)

    # 6. Hiển thị giao diện và chạy vòng lặp sự kiện
    view.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()