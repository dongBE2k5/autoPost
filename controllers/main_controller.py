# controllers/main_controller.py
import datetime
from PySide6.QtCore import QObject, pyqtSlot, QThread, pyqtSignal
from PySide6.QtWidgets import QFileDialog, QDialog

# Import Services & Models
from services.facebook_service import FacebookService
from services.tiktok_service import TikTokService
from services.ai_service import AIService
from models.post import ContentDraft

# --- ĐÃ SỬA LỖI IMPORT Ở ĐÂY ---
# Trỏ đúng vị trí các Dialog trong kiến trúc thư mục mới
from ui.dialogs.media_settings import LogoSettingsDialog, VideoSettingsDialog
from ui.dialogs.schedule_settings import ScheduleDialog
from ui.dialogs.post_manager import DraftsDialog, QueueDialog


class PipelineWorker(QThread):
    """Worker chạy ngầm để không làm đơ UI khi gọi API"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(list, str) 

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            tiktok_svc = TikTokService(self.config.get('tiktok_api', ''))
            ai_svc = AIService(self.config.get('gemini_key', ''))

            self.log_signal.emit("Bắt đầu quy trình Pipeline...")
            videos_data = tiktok_svc.fetch_trending_videos(
                keyword=self.config.get('custom_trend'),
                max_videos=self.config.get('max_videos', 1),
                log_cb=self.log_signal.emit
            )

            final_posts_data = []
            for step_result in ai_svc.process_content_pipeline(videos_data, self.config):
                if step_result['type'] == 'log':
                    self.log_signal.emit(step_result['message'])
                elif step_result['type'] == 'error':
                    self.log_signal.emit(f"❌ Lỗi AI: {step_result['message']}")
                    self.finished_signal.emit([], step_result['message'])
                    return
                elif step_result['type'] == 'success':
                    final_posts_data = step_result['data']

            drafts = []
            current_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            keyword_used = self.config.get('custom_trend') or "viral"
            
            for post_dict in final_posts_data:
                drafts.append(ContentDraft(
                    keyword=keyword_used,
                    content=post_dict.get('content', ''),
                    image_path=post_dict.get('image_path', ''),
                    video_path=post_dict.get('video_path', ''),
                    timestamp=current_time
                ))

            self.finished_signal.emit(drafts, "")

        except Exception as e:
            self.log_signal.emit(f"❌ Pipeline Lỗi: {str(e)}")
            self.finished_signal.emit([], str(e))


class MainController(QObject):
    """Controller chính điều phối luồng dữ liệu"""
    def __init__(self, view, settings_manager):
        super().__init__()
        self.view = view
        self.settings = settings_manager 
        self.pipeline_thread = None
        
        self.load_data_to_view()
        self.connect_signals()

    def connect_signals(self):
        """Gắn 'dây điện' cho toàn bộ nút bấm trên UI (Trỏ sâu vào từng Tab)"""
        
        # 1. Nút ở Tab Thiết Lập (Settings)
        self.view.tab_settings.btn_save_config.clicked.connect(self.save_settings)
        self.view.tab_settings.btn_open_cookie.clicked.connect(lambda: self.view.show_notification("Cookie", "Mở file cookies.txt"))
        
        
        
        # 2. Nút ở Tab Dashboard
        self.view.tab_dashboard.btn_browse_file.clicked.connect(self.browse_document)
        self.view.tab_dashboard.btn_auto_pipeline.clicked.connect(self.handle_run_pipeline)
        
        self.view.tab_dashboard.btn_logo_settings.clicked.connect(self.open_logo_dialog)
        self.view.tab_dashboard.btn_video_settings.clicked.connect(self.open_video_dialog)
        self.view.tab_dashboard.btn_open_schedule.clicked.connect(self.open_schedule_dialog)
        self.view.tab_dashboard.btn_open_drafts.clicked.connect(self.open_drafts_dialog)
        self.view.tab_dashboard.btn_open_queue.clicked.connect(self.open_queue_dialog)
        
        # 3. Nút ở Tab Quản lý Facebook
        self.view.tab_post_manager.refresh_requested.connect(self.handle_refresh_fb_posts)
        self.view.tab_post_manager.delete_requested.connect(self.handle_delete_fb_post)
        
    def load_data_to_view(self):
        """Nạp dữ liệu từ DB lên UI lúc mở app"""
        # Nạp dữ liệu cấu hình vào Tab Settings
        cfg = self.settings.get_config()
        self.view.tab_settings.set_settings_data(cfg)
        
        # Nạp lịch sử vào Tab History
        history_data = self.settings.get_history()
        self.view.tab_history.refresh_table(history_data)

    @pyqtSlot()
    def save_settings(self):
        cfg = self.settings.get_config() 
        ui_settings = self.view.tab_settings.get_settings_data() # Lấy data từ TabSettings
        cfg.update(ui_settings)
        self.settings.save_config(cfg)
        self.view.show_notification("Lưu thành công! 💾", "Cấu hình đã được cập nhật.")

    @pyqtSlot()
    def browse_document(self):
        file_path, _ = QFileDialog.getOpenFileName(self.view, "Chọn file SP", "", "Docs (*.txt *.docx *.csv)")
        if file_path:
            self.view.tab_dashboard.input_doc_file.setText(file_path)

    # ==========================================
    # CÁC HÀM XỬ LÝ MỞ DIALOG (POPUP)
    # ==========================================
    @pyqtSlot()
    def open_logo_dialog(self):
        cfg = self.settings.get_config()
        dialog = LogoSettingsDialog(cfg['logo_path'], cfg['logo_pos'], cfg['logo_opacity'], cfg['logo_scale'], self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            path, pos, opacity, scale = dialog.get_settings()
            cfg.update({'logo_path': path, 'logo_pos': pos, 'logo_opacity': opacity, 'logo_scale': scale})
            self.settings.save_config(cfg)
            self.view.show_notification("Thành công 🖼️", "Đã lưu cài đặt Logo.")

    @pyqtSlot()
    def open_video_dialog(self):
        cfg = self.settings.get_config()
        dialog = VideoSettingsDialog(cfg['veo_model'], cfg['veo_aspect'], cfg['veo_res'], cfg['veo_duration'], cfg['veo_negative'], cfg['veo_style'],cfg['veo_camera'],cfg['veo_ref_image'],self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            model, aspect, res, duration, negative = dialog.get_settings()
            cfg.update({'veo_model': model, 'veo_aspect': aspect, 'veo_res': res, 'veo_duration': duration, 'veo_negative': negative})
            self.settings.save_config(cfg)
            self.view.show_notification("Thành công 🎬", "Đã lưu cài đặt Video AI.")

    @pyqtSlot()
    def open_schedule_dialog(self):
        cfg = self.settings.get_config()
        dialog = ScheduleDialog(cfg['auto_az_times'], self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cfg['auto_az_times'] = dialog.get_schedule_string()
            self.settings.save_config(cfg)
            self.view.show_notification("Cập nhật Lịch! 📅", "Đã lưu khung giờ chạy Bot.")

    @pyqtSlot()
    def open_drafts_dialog(self):
        drafts_list_dicts = [d.to_dict() for d in self.settings.get_drafts()]
        dialog = DraftsDialog(drafts_list_dicts, self.view)
        
        # Bắt tín hiệu từ Dialog gửi về Controller
        dialog.post_now_requested.connect(
            lambda d: self.handle_post_now(
                ContentDraft(
                    keyword=d.get('keyword', ''),
                    content=d.get('content', ''),
                    image_path=d.get('image_path', ''),
                    video_path=d.get('video_path', '')
                ), 
                "00:00", 
                False
            )
        )
        
        # Lấy queue list hiện tại
        queue_list_dicts = [q.to_dict() for q in self.settings.get_queue()]
        dialog.queue_requested.connect(lambda d, t: queue_list_dicts.append({"time": t, **d}))
        
        dialog.exec()
        
        # Lưu lại DB sau khi đóng cửa sổ
        updated_drafts = [
            ContentDraft(
                keyword=d.get('keyword', ''), 
                content=d.get('content', ''), 
                timestamp=d.get('timestamp', ''),
                image_path=d.get('image_path', ''), 
                video_path=d.get('video_path', '')
            ) for d in dialog.drafts_list
        ]
        self.settings.save_drafts(updated_drafts)
        
        def dict_to_queue_obj(q):
            return ContentDraft(time_queue=q.get('time',''), keyword=q.get('keyword',''), 
                                content=q.get('content',''), image_path=q.get('image_path',''), video_path=q.get('video_path',''))
        self.settings.save_queue([dict_to_queue_obj(q) for q in queue_list_dicts])

    @pyqtSlot()
    def open_queue_dialog(self):
        queue_list_dicts = [q.to_dict() for q in self.settings.get_queue()]
        dialog = QueueDialog(queue_list_dicts, self.view)
        dialog.exec()
        
        def dict_to_queue_obj(q):
            return ContentDraft(time_queue=q.get('time',''), keyword=q.get('keyword',''), 
                                content=q.get('content',''), image_path=q.get('image_path',''), video_path=q.get('video_path',''))
        self.settings.save_queue([dict_to_queue_obj(q) for q in dialog.queue_list])

    # ==========================================
    # CÁC HÀM XỬ LÝ NGHIỆP VỤ CHÍNH
    # ==========================================
    @pyqtSlot()
    def handle_run_pipeline(self):
        # 1. Lấy Config từ UI Dashboard
        ui_config = self.view.tab_dashboard.get_pipeline_config()
        
        # 2. Lấy Config từ UI Settings (Bao gồm cả AI Model)
        settings_config = self.view.tab_settings.get_settings_data()
        
        # 3. Lấy Config ngầm từ Database (Logo, Video...)
        db_config = self.settings.get_config()
        
        # 4. GỘP TẤT CẢ LẠI (Ưu tiên giao diện đè lên DB nếu có trùng)
        full_config = {**db_config, **settings_config, **ui_config} 
        
        # --- FIX LỖI Ở ĐÂY ---
        # ApiPipelineWorker đang tìm key 'ai_model', nhưng ở settings ta lưu là 'gemini_model'
        # Nên ta phải map (gán) nó sang cho đúng tên
        full_config['ai_model'] = full_config.get('gemini_model', 'gemini-2.5-flash')
        
        if not full_config.get('tiktok_api') or not full_config.get('gemini_key'):
            self.view.show_notification("Thiếu API Key ❌", "Vui lòng nhập API ở tab Thiết Lập!", True)
            return

        self.view.tab_dashboard.btn_auto_pipeline.setEnabled(False)
        self.view.tab_dashboard.add_log("⚡ Đang chuẩn bị chạy Pipeline MVC...")

        self.pipeline_thread = PipelineWorker(full_config)
        self.pipeline_thread.log_signal.connect(self.view.tab_dashboard.add_log)
        self.pipeline_thread.finished_signal.connect(self.on_pipeline_finished)
        self.pipeline_thread.start()
    @pyqtSlot(list, str)
    def on_pipeline_finished(self, drafts, error_msg):
        self.view.tab_dashboard.btn_auto_pipeline.setEnabled(True)
        if error_msg:
            self.view.show_notification("Lỗi Pipeline ❌", error_msg, True)
            return

        if drafts:
            old_drafts = self.settings.get_drafts()
            old_drafts.extend(drafts)
            self.settings.save_drafts(old_drafts)
            self.view.show_notification("Thành công! 🎉", f"Đã đẩy {len(drafts)} bài vào Kho Content.")

    @pyqtSlot(object, str, bool)
    def handle_post_now(self, draft_obj, time_str, is_auto):
        """Xử lý nút Đăng Ngay lên FB"""
        config = self.settings.get_config()
        fb_service = FacebookService(config.get('fb_id'), config.get('fb_token'))
        mode_name = "Auto Bot" if is_auto else "Thủ công"
        
        self.view.tab_dashboard.add_log(f"[{mode_name.upper()}] Đang gửi dữ liệu lên Facebook...")
        try:
            success = fb_service.post_content(
                content=draft_obj.content,
                image_path=draft_obj.image_path,
                video_path=draft_obj.video_path,
                schedule_time_str=None,
                log_cb=self.view.tab_dashboard.add_log
            )
            if success:
                self.view.show_notification("Đăng thành công! 🚀", "Đã đẩy bài lên Fanpage.")
                now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                self.settings.add_history_record(now_str, draft_obj.keyword, draft_obj.content, mode_name, draft_obj.image_path, draft_obj.video_path)
                
                self.view.tab_history.refresh_table(self.settings.get_history())
                
        except Exception as e:
            self.view.show_notification("Lỗi Facebook ❌", str(e), True)
    # ==========================================
    # QUẢN LÝ FACEBOOK (GRAPH API)
    # ==========================================
    @pyqtSlot()
    def handle_refresh_fb_posts(self):
        """Xử lý nút tải lại danh sách bài viết từ FB"""
        config = self.settings.get_config()
        if not config.get('fb_id') or not config.get('fb_token'):
            self.view.show_notification("Lỗi Facebook ❌", "Vui lòng nhập ID và Token Fanpage ở tab Thiết Lập trước!", True)
            return

        self.view.tab_post_manager.set_loading_state()
        
        # Tạm thời dùng QTimer để UI kịp render trạng thái Loading
        import PySide6.QtCore as QtCore
        QTimer = QtCore.QTimer
        
        def fetch_worker():
            try:
                fb_service = FacebookService(config.get('fb_id'), config.get('fb_token'))
                posts = fb_service.get_published_posts(limit=50) # Lấy 50 bài mới nhất
                self.view.tab_post_manager.populate_table(posts)
                self.view.show_notification("Tải hoàn tất 🔄", f"Lấy thành công {len(posts)} bài viết.")
            except Exception as e:
                self.view.show_notification("Lỗi Facebook API ❌", str(e), True)
                self.view.tab_post_manager.lbl_status.setText(f"Lỗi: {str(e)}")
            finally:
                self.view.tab_post_manager.reset_loading_state()

        QTimer.singleShot(100, fetch_worker)

    @pyqtSlot(str)
    def handle_delete_fb_post(self, post_id):
        """Xử lý nút Xóa bài viết trên FB"""
        from PySide6.QtWidgets import QMessageBox
        
        # Cảnh báo an toàn
        reply = QMessageBox.warning(self.view, 'Cảnh báo nguy hiểm', 
                                    f'Bạn có CHẮC CHẮN muốn xóa vĩnh viễn bài viết này khỏi Fanpage không?\nID: {post_id}',
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                    QMessageBox.StandardButton.No)
                                    
        if reply == QMessageBox.StandardButton.Yes:
            config = self.settings.get_config()
            try:
                fb_service = FacebookService(config.get('fb_id'), config.get('fb_token'))
                if fb_service.delete_post(post_id):
                    self.view.show_notification("Đã Xóa 🗑️", "Bài viết đã bị bốc hơi khỏi Fanpage!")
                    # Tải lại danh sách ngay lập tức để cập nhật UI
                    self.handle_refresh_fb_posts()
            except Exception as e:
                self.view.show_notification("Lỗi xóa bài ❌", str(e), True)
    @pyqtSlot(object, str, bool)
    def handle_post_now(self, draft_obj, time_str, is_auto):
        """Xử lý nút Đăng Ngay lên FB"""
        config = self.settings.get_config()
        fb_service = FacebookService(config.get('fb_id'), config.get('fb_token'))
        mode_name = "Auto Bot" if is_auto else "Thủ công"
        
        # Kiểm tra xem có đang chạy từ Queue (Hàng đợi) không.
        # Nếu Hàng đợi gọi post (nghĩa là đăng ngay), nhưng user lại cấu hình publish_immediately=False, 
        # thì nó sẽ Lên lịch.
        is_publish_now = config.get('publish_immediately', True)
        
        self.view.tab_dashboard.add_log(f"[{mode_name.upper()}] Đang gửi dữ liệu lên Facebook...")
        try:
            success = fb_service.post_content(
                content=draft_obj.content,
                image_path=draft_obj.image_path,
                video_path=draft_obj.video_path,
                schedule_time_str=None if time_str == "00:00" else time_str, 
                publish_immediately=is_publish_now, # <--- TRUYỀN VÀO SERVICE
                log_cb=self.view.tab_dashboard.add_log
            )
            
            if success:
                # Sửa thông báo tùy theo chế độ
                msg = "Đã đẩy bài lên Fanpage thành công!" if is_publish_now else "Đã đẩy lên kho Lên Lịch của Fanpage!"
                self.view.show_notification("Facebook API 🚀", msg)
                
                now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                self.settings.add_history_record(now_str, draft_obj.keyword, draft_obj.content, mode_name, draft_obj.image_path, draft_obj.video_path)
                
                self.view.tab_history.refresh_table(self.settings.get_history())
                
        except Exception as e:
            self.view.show_notification("Lỗi Facebook ❌", str(e), True)