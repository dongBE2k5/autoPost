# main.py
import sys
from PySide6.QtWidgets import QApplication

# Import các thành phần từ kiến trúc MVC
from config.settings import setup_ffmpeg
from config.settings_manager import SettingsManager, DB_FILE
from config.token_history_manager import DEFAULT_DB_PATH as TOKEN_DB_FILE
from PySide6.QtSql import QSqlDatabase
from ui.main_window import MainWindow
from controllers.main_controller import MainController

# Import Services for Dependency Injection
from services.facebook_service import FacebookService
from services.scrapers import TikTokScraper
from services.ai_service import AIService

def main():
    # 1. Setup môi trường hệ thống
    setup_ffmpeg()

    # 2. Khởi tạo Application của PyQt
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 

    # 3. Khởi tạo kết nối QSqlDatabase toàn cục cho kiến trúc Model/View
    db_settings = QSqlDatabase.addDatabase("QSQLITE", "SettingsDB")
    db_settings.setDatabaseName(DB_FILE)
    if not db_settings.open():
        print(f"Lỗi không thể mở {DB_FILE}")

    db_tokens = QSqlDatabase.addDatabase("QSQLITE", "TokenDB")
    db_tokens.setDatabaseName(TOKEN_DB_FILE)
    if not db_tokens.open():
        print(f"Lỗi không thể mở {TOKEN_DB_FILE}")

    # 4. Khởi tạo Database / Cấu hình (Model)
    settings_manager = SettingsManager()

    # 4. Khởi tạo Giao diện (View)
    view = MainWindow()

    # 5. Dependency Injection: Chuẩn bị Factory/Instance của các Services
    # Đảo ngược phụ thuộc (D trong SOLID): Controller không tự tạo Service, nó được tiêm từ ngoài.
    
    # Factory cho TikTok (sẽ tạo TikTokScraper thay vì TikTokService cũ)
    def tiktok_svc_factory(config):
        return TikTokScraper(config.get('tiktok_api', ''))

    # Factory cho AI
    def ai_svc_factory(config):
        return AIService(config.get('gemini_key', ''))

    # Factory cho Facebook
    def fb_svc_factory(fb_id, fb_token):
        return FacebookService(fb_id, fb_token)

    # 6. Khởi tạo "Não bộ" điều phối (Controller) và gắn nó vào View & Model & Services
    controller = MainController(
        view=view, 
        settings_manager=settings_manager,
        tiktok_svc_factory=tiktok_svc_factory,
        ai_svc_factory=ai_svc_factory,
        fb_svc_factory=fb_svc_factory
    )

    # 7. Hiển thị giao diện và chạy vòng lặp sự kiện
    view.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()