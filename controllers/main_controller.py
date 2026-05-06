# controllers/main_controller.py
import datetime
from PySide6.QtCore import QObject, Slot, QThread, Signal,QTimer
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
    log_signal = Signal(str)
    finished_signal = Signal(list, str) 

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._is_stopped = False

    def stop(self):
        self._is_stopped = True

    def run(self):
        try:
            tiktok_svc = TikTokService(self.config.get('tiktok_api', ''))
            ai_svc = AIService(self.config.get('gemini_key', ''))

            self.log_signal.emit("Bắt đầu quy trình Pipeline...")

            def check_stop():
                return self._is_stopped

            use_tiktok = self.config.get('use_tiktok', True)

            if use_tiktok:
                self.log_signal.emit("📡 Chế độ TikTok: Đang cào video trending...")
                videos_data = tiktok_svc.fetch_trending_videos(
                    keyword=self.config.get('custom_trend'),
                    max_videos=self.config.get('max_videos', 1),
                    log_cb=self.log_signal.emit,
                    stop_cb=check_stop,
                    search_queries=self.config.get('search_queries') or None,
                    hashtags=self.config.get('hashtags') or None
                )
            else:
                self.log_signal.emit("🤖 Chế độ Gemini Only: Bỏ qua TikTok, dùng tài liệu sản phẩm trực tiếp.")
                videos_data = []  # Không có video → ai_service sẽ dùng tài liệu sản phẩm

            final_posts_data = []
            for step_result in ai_svc.process_content_pipeline(videos_data, self.config, log_cb=self.log_signal.emit, stop_cb=check_stop):
                if self._is_stopped:
                    self.log_signal.emit("🛑 Pipeline đã bị dừng bởi người dùng.")
                    self.finished_signal.emit([], "Stopped")
                    return
                
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
            if str(e) == "Stopped":
                self.log_signal.emit("🛑 Pipeline đã bị dừng bởi người dùng.")
                self.finished_signal.emit([], "Stopped")
            else:
                self.log_signal.emit(f"❌ Pipeline Lỗi: {str(e)}")
                self.finished_signal.emit([], str(e))


class MainController(QObject):
    """Controller chính điều phối luồng dữ liệu"""
    def __init__(self, view, settings_manager):
        super().__init__()
        self.view = view
        self.settings = settings_manager 
        self.pipeline_thread = None
        
        self.bot_timer = QTimer(self)
        self.bot_timer.timeout.connect(self.check_schedule_and_post)
        
        self.load_data_to_view()
        self.connect_signals()
        self.view.tab_dashboard.load_config(self.settings.get_config())

        # Tự động lưu cấu hình khi tắt ứng dụng
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self.save_settings_on_quit)

    def connect_signals(self):
        """Gắn 'dây điện' cho toàn bộ nút bấm trên UI (Trỏ sâu vào từng Tab)"""
        
        # 1. Nút ở Tab Thiết Lập (Settings)
        self.view.tab_settings.btn_save_config.clicked.connect(self.save_settings)
        self.view.tab_settings.btn_open_cookie.clicked.connect(lambda: self.view.show_notification("Cookie", "Mở file cookies.txt"))
        
        
        
        # 2. Nút ở Tab Dashboard
        # self.view.tab_dashboard.btn_browse_file.clicked.connect(self.browse_document)
        self.view.tab_dashboard.btn_auto_pipeline.clicked.connect(self.handle_run_pipeline)
        
        self.view.tab_dashboard.btn_logo_settings.clicked.connect(self.open_logo_dialog)
        self.view.tab_dashboard.btn_video_settings.clicked.connect(self.open_video_dialog)
        self.view.tab_dashboard.btn_open_schedule.clicked.connect(self.open_schedule_dialog)
        self.view.tab_dashboard.btn_open_drafts.clicked.connect(self.open_drafts_dialog)
        self.view.tab_dashboard.btn_open_queue.clicked.connect(self.open_queue_dialog)
        
        self.view.tab_dashboard.btn_start_bot.clicked.connect(self.handle_toggle_bot)
        
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

    @Slot()
    def save_settings(self):
        cfg = self.settings.get_config() 
        ui_settings = self.view.tab_settings.get_settings_data() # Lấy data từ TabSettings
        cfg.update(ui_settings)
        
        # --- BỔ SUNG LƯU DỮ LIỆU TỪ TAB DASHBOARD ---
        ui_config = self.view.tab_dashboard.get_pipeline_config()
        cfg.update({
            'dash_use_tiktok': str(ui_config.get('use_tiktok', False)),
            'dash_keyword': '\n'.join(ui_config.get('search_queries', [ui_config.get('custom_trend', '')])),
            'dash_max_videos': ui_config['max_videos'],
            'dash_ai_count': ui_config['count'],
            'dash_topics': ui_config['target_topics'],
            'dash_hashtags': '\n'.join(ui_config.get('hashtags', [])),
            'dash_search_queries': '\n'.join(ui_config.get('search_queries', [])),
            'dash_doc_file': __import__('json').dumps(ui_config.get('doc_file_paths', [])),
            'dash_custom_prompt': ui_config['custom_prompt'],
            'dash_ignore': ui_config['ignore_keywords'],
            'dash_word_limit': ui_config['word_limit'],
            'dash_gen_image': str(ui_config['gen_image']), 
            'dash_gen_video': str(ui_config['gen_video'])
        })

        self.settings.save_config(cfg)
        self.view.show_notification("Lưu thành công! 💾", "Cấu hình đã được cập nhật.")

    @Slot()
    def save_settings_on_quit(self):
        """Lưu tự động cấu hình khi đóng ứng dụng mà không cần hiển thị thông báo"""
        cfg = self.settings.get_config() 
        ui_settings = self.view.tab_settings.get_settings_data()
        cfg.update(ui_settings)
        
        ui_config = self.view.tab_dashboard.get_pipeline_config()
        cfg.update({
            'dash_use_tiktok': str(ui_config.get('use_tiktok', False)),
            'dash_keyword': '\n'.join(ui_config.get('search_queries', [ui_config.get('custom_trend', '')])),
            'dash_max_videos': ui_config['max_videos'],
            'dash_ai_count': ui_config['count'],
            'dash_topics': ui_config['target_topics'],
            'dash_hashtags': '\n'.join(ui_config.get('hashtags', [])),
            'dash_search_queries': '\n'.join(ui_config.get('search_queries', [])),
            'dash_doc_file': __import__('json').dumps(ui_config.get('doc_file_paths', [])),
            'dash_custom_prompt': ui_config['custom_prompt'],
            'dash_ignore': ui_config['ignore_keywords'],
            'dash_word_limit': ui_config['word_limit'],
            'dash_gen_image': str(ui_config['gen_image']), 
            'dash_gen_video': str(ui_config['gen_video'])
        })
        self.settings.save_config(cfg)

    @Slot()
    def browse_document(self):
        """Đã được thay thế bởi browse_doc_file trong TabDashboard."""
        pass

    # ==========================================
    # CÁC HÀM XỬ LÝ MỞ DIALOG (POPUP)
    # ==========================================
    @Slot()
    def open_logo_dialog(self):
        cfg = self.settings.get_config()
        dialog = LogoSettingsDialog(cfg['logo_path'], cfg['logo_pos'], cfg['logo_opacity'], cfg['logo_scale'], self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            path, pos, opacity, scale = dialog.get_settings()
            cfg.update({'logo_path': path, 'logo_pos': pos, 'logo_opacity': opacity, 'logo_scale': scale})
            self.settings.save_config(cfg)
            self.view.show_notification("Thành công 🖼️", "Đã lưu cài đặt Logo.")

    @Slot()
    def open_video_dialog(self):
        cfg = self.settings.get_config()
        dialog = VideoSettingsDialog(cfg['veo_model'], cfg['veo_aspect'], cfg['veo_res'], cfg['veo_duration'], cfg['veo_negative'], cfg['veo_style'],cfg['veo_camera'],cfg['veo_ref_image'],self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            model, aspect, res, duration, negative = dialog.get_settings()
            cfg.update({'veo_model': model, 'veo_aspect': aspect, 'veo_res': res, 'veo_duration': duration, 'veo_negative': negative})
            self.settings.save_config(cfg)
            self.view.show_notification("Thành công 🎬", "Đã lưu cài đặt Video AI.")

    @Slot()
    def open_schedule_dialog(self):
        cfg = self.settings.get_config()
        dialog = ScheduleDialog(cfg['auto_az_times'], self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cfg['auto_az_times'] = dialog.get_schedule_string()
            self.settings.save_config(cfg)
            self.view.show_notification("Cập nhật Lịch! 📅", "Đã lưu khung giờ chạy Bot.")

    @Slot()
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

    @Slot()
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
    @Slot()
    def handle_run_pipeline(self):
        # Nếu đang chạy thì thực hiện DỪNG
        if self.pipeline_thread and self.pipeline_thread.isRunning():
            self.pipeline_thread.stop()
            self.view.tab_dashboard.add_log("⏹️ Đang gửi yêu cầu dừng Pipeline...")
            self.view.tab_dashboard.btn_auto_pipeline.setEnabled(False) # Chờ nó dừng hẳn
            return

        # 1. Lấy Config từ UI Dashboard
        ui_config = self.view.tab_dashboard.get_pipeline_config()
        
        # --- BẮT ĐẦU: LƯU LẠI CÁC THÔNG SỐ NÀY VÀO DATABASE ---
        current_cfg = self.settings.get_config()
        current_cfg.update({
            'dash_use_tiktok': str(ui_config.get('use_tiktok', False)),
            'dash_keyword': '\n'.join(ui_config.get('search_queries', [ui_config.get('custom_trend', '')])),
            'dash_max_videos': ui_config['max_videos'],
            'dash_ai_count': ui_config['count'],
            'dash_topics': ui_config['target_topics'],
            'dash_hashtags': '\n'.join(ui_config.get('hashtags', [])),
            'dash_search_queries': '\n'.join(ui_config.get('search_queries', [])),
            'dash_doc_file': __import__('json').dumps(ui_config.get('doc_file_paths', [])),
            'dash_custom_prompt': ui_config['custom_prompt'],
            'dash_ignore': ui_config['ignore_keywords'],
            'dash_word_limit': ui_config['word_limit'],
            'dash_gen_image': str(ui_config['gen_image']), # Ép kiểu bool thành chuỗi
            'dash_gen_video': str(ui_config['gen_video'])
        })
        self.settings.save_config(current_cfg)
        # --- KẾT THÚC LƯU DATABASE ---
        
        # 2. Lấy Config từ UI Settings (Bao gồm cả AI Model)
        settings_config = self.view.tab_settings.get_settings_data()
        
        # 3. Lấy Config ngầm từ Database (Logo, Video...)
        db_config = self.settings.get_config()
        
        # 4. GỘP TẤT CẢ LẠI (Ưu tiên giao diện đè lên DB nếu có trùng)
        full_config = {**db_config, **settings_config, **ui_config}

        # Đảm bảo doc_file_paths luôn là list (parse lại từ JSON nếu bị lưu dạng string)
        import json as _json
        if not full_config.get('doc_file_paths'):
            raw = full_config.get('dash_doc_file', '')
            try:
                parsed = _json.loads(raw) if raw and raw.startswith('[') else ([raw] if raw else [])
            except Exception:
                parsed = [raw] if raw else []
            full_config['doc_file_paths'] = [p for p in parsed if p]
            full_config['doc_file_path'] = full_config['doc_file_paths'][0] if full_config['doc_file_paths'] else ''
        
        # --- FIX LỖI Ở ĐÂY ---
        full_config['ai_model'] = full_config.get('gemini_model', 'gemini-2.5-flash')
        
        if not full_config.get('tiktok_api') or not full_config.get('gemini_key'):
            self.view.show_notification("Thiếu API Key ❌", "Vui lòng nhập API ở tab Thiết Lập!", True)
            return

        self.view.tab_dashboard.set_analysis_state(True)
        self.view.tab_dashboard.set_ui_locked(True)
        self.view.tab_dashboard.add_log("⚡ Đang chuẩn bị chạy Pipeline MVC...")

        self.pipeline_thread = PipelineWorker(full_config)
        self.pipeline_thread.log_signal.connect(self.view.tab_dashboard.add_log)
        self.pipeline_thread.finished_signal.connect(self.on_pipeline_finished)
        self.pipeline_thread.start()
    @Slot(list, str)
    def on_pipeline_finished(self, drafts, error_msg):
        self.view.tab_dashboard.set_analysis_state(False)
        
        is_bot_running = "TẮT BOT" in self.view.tab_dashboard.btn_start_bot.text()
        if is_bot_running:
            self.view.tab_dashboard.btn_auto_pipeline.setEnabled(False)
        else:
            self.view.tab_dashboard.set_ui_locked(False)

        if error_msg:
            if error_msg != "Stopped":
                self.view.show_notification("Lỗi Pipeline ❌", error_msg, True)
            return

        if drafts:
            # 1. Vẫn lưu vào kho nháp để làm backup (như cũ)
            old_drafts = self.settings.get_drafts()
            old_drafts.extend(drafts)
            self.settings.save_drafts(old_drafts)
            
            # --- 2. LOGIC MỚI BỔ SUNG CHO CHẾ ĐỘ AUTO A-Z ---
            # Kiểm tra xem Bot có đang bật và đang ở chế độ A-Z không?
            is_bot_running = "TẮT BOT" in self.view.tab_dashboard.btn_start_bot.text() 
            is_az_mode = self.view.tab_dashboard.radio_mode_az.isChecked()
            
            if is_bot_running and is_az_mode:
                self.view.tab_dashboard.add_log(f"⚡ [AUTO A-Z] Đã đẻ xong {len(drafts)} bài! Đang lấy bài xuất sắc nhất đem đi đăng...")
                
                # Lấy bài viết đầu tiên (xuất sắc nhất) vừa đẻ ra đem đăng ngay lập tức
                post_to_publish = drafts[0]
                self.handle_post_now(post_to_publish, "00:00", True) # Tham số True báo hiệu đây là Bot chạy
            else:
                # Nếu chạy bằng tay (Thủ công) thì chỉ thông báo thôi
                self.view.show_notification("Thành công! 🎉", f"Đã đẩy {len(drafts)} bài vào Kho Content.")


    # ==========================================
    # QUẢN LÝ FACEBOOK (GRAPH API)
    # ==========================================
    @Slot()
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

    @Slot(str)
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
    @Slot(object, str, bool)
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
    @Slot()
    def handle_toggle_bot(self):
        """Xử lý giao diện và logic khi bấm nút Bật/Tắt Bot"""
        # Lấy chữ hiện tại trên nút để xác định trạng thái
        current_text = self.view.tab_dashboard.btn_start_bot.text()

        if "BẬT" in current_text:
            # 1. Đổi UI sang trạng thái ĐANG CHẠY (Nút đỏ, chữ Tắt)
            self.view.tab_dashboard.btn_start_bot.setText("⏹️ TẮT BOT")
            self.view.tab_dashboard.btn_start_bot.setStyleSheet("background-color: #ef4444; color: white; min-height: 50px; font-weight: bold;")
            
            self.view.tab_dashboard.lbl_bot_status.setText("🟢 ĐANG CHẠY")
            self.view.tab_dashboard.lbl_bot_status.setStyleSheet("color: #22c55e; font-weight: bold; font-size: 14px;")
            
            self.view.tab_dashboard.add_log("🤖 [HỆ THỐNG] Bot đã được BẬT. Bắt đầu giám sát tiến trình...")
            
            # --- KIỂM TRA ĐIỀU KIỆN TRƯỚC KHI CHẠY ---
            if self.view.tab_dashboard.radio_mode_queue.isChecked():
                if not self.settings.get_queue():
                    self.view.tab_dashboard.add_log("⚠️ [CẢNH BÁO] Hàng đợi đang rỗng! Bot sẽ không đăng bài cho đến khi có bài mới.")
            elif self.view.tab_dashboard.radio_mode_az.isChecked():
                cfg = self.settings.get_config()
                if not cfg.get('auto_az_times', '').strip():
                    self.view.tab_dashboard.add_log("⚠️ [CẢNH BÁO] Chưa cài đặt khung giờ Auto A-Z! Bot sẽ không tự chạy.")

            # --- KHÓA LỰA CHỌN CHẾ ĐỘ VÀ GIAO DIỆN ---
            self.view.tab_dashboard.radio_mode_queue.setEnabled(False)
            self.view.tab_dashboard.radio_mode_az.setEnabled(False)
            self.view.tab_dashboard.btn_auto_pipeline.setEnabled(False)
            self.view.tab_dashboard.set_ui_locked(True)
            
            # Khởi động Timer: 60000 ms = 60 giây = 1 phút quét 1 lần
            self.bot_timer.start(60000) 
            
            # Chạy quét ngay lập tức 1 lần (không cần đợi 1 phút)
            self.check_schedule_and_post()

        else:
            # 2. Đổi UI về trạng thái ĐÃ TẮT (Nút xanh, chữ Bật)
            self.view.tab_dashboard.btn_start_bot.setText("🤖 BẬT BOT")
            self.view.tab_dashboard.btn_start_bot.setStyleSheet("background-color: #16a34a; color: white; min-height: 50px; font-weight: bold;")
            
            self.view.tab_dashboard.lbl_bot_status.setText("🔴 ĐANG TẮT")
            self.view.tab_dashboard.lbl_bot_status.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")
            
            self.view.tab_dashboard.add_log("⏹️ [HỆ THỐNG] Bot đã được TẮT.")
            
            # --- MỞ KHÓA LỰA CHỌN CHẾ ĐỘ VÀ GIAO DIỆN TRỞ LẠI ---
            self.view.tab_dashboard.radio_mode_queue.setEnabled(True)
            self.view.tab_dashboard.radio_mode_az.setEnabled(True)
            self.view.tab_dashboard.btn_auto_pipeline.setEnabled(True)
            self.view.tab_dashboard.set_ui_locked(False)
            
            # Tắt Timer
            self.bot_timer.stop()

            # --- DỪNG LUÔN PIPELINE NẾU ĐANG CHẠY ---
            if self.pipeline_thread and self.pipeline_thread.isRunning():
                self.pipeline_thread.stop()
                self.view.tab_dashboard.add_log("⏹️ [HỆ THỐNG] Đang dừng tác vụ phân tích hiện tại...")


    @Slot()
    def check_schedule_and_post(self):
        """Hàm này được QTimer gọi mỗi 1 phút để quét lịch"""
        current_time_str = datetime.datetime.now().strftime("%H:%M")
        
        is_queue_mode = self.view.tab_dashboard.radio_mode_queue.isChecked()
        is_az_mode = self.view.tab_dashboard.radio_mode_az.isChecked()
        
        # ==========================================
        # CHẾ ĐỘ 1: BỐC TỪ HÀNG ĐỢI (Đã làm ở bước trước)
        # ==========================================
        if is_queue_mode:
            queue = self.settings.get_queue()
            if not queue: return 
            
            top_post = queue[0]
            # Sửa lỗi: dùng <= để nếu trễ 1 vài phút bot vẫn đăng thay vì bỏ qua luôn
            if top_post.time_queue <= current_time_str or (top_post.time_queue > "23:00" and current_time_str < "01:00"):
                self.view.tab_dashboard.add_log(f"⏰ [HÀNG ĐỢI] Tới giờ {top_post.time_queue}! Đang lấy bài ra đăng...")
                self.handle_post_now(top_post, "00:00", True)
                queue.pop(0)
                self.settings.save_queue(queue)

        # ==========================================
        # CHẾ ĐỘ 2: AUTO A-Z (Vũ khí tối thượng)
        # ==========================================
        elif is_az_mode:
            cfg = self.settings.get_config()
            az_times_str = cfg.get('auto_az_times', '') # VD: "08:00, 12:00, 19:30"
            
            # Tách chuỗi thành danh sách các khung giờ và đảm bảo format HH:MM (zero-padded)
            import re
            az_times_list = []
            az_times_counts = {}
            for t in az_times_str.split(','):
                match = re.search(r"(\d{1,2}):(\d{1,2})", t)
                if match:
                    try:
                        formatted_time = f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"
                        az_times_list.append(formatted_time)
                        
                        count_match = re.search(r"\(x(\d+)\)", t)
                        if count_match:
                            az_times_counts[formatted_time] = int(count_match.group(1))
                    except: pass
            
            # Nếu giờ hiện tại trùng với giờ cài đặt & Pipeline chưa chạy
            is_pipeline_running = self.pipeline_thread is not None and self.pipeline_thread.isRunning()
            if current_time_str in az_times_list and not is_pipeline_running:
                # Cập nhật số lượng bài viết nếu có cấu hình (xN)
                if current_time_str in az_times_counts:
                    self.view.tab_dashboard.spin_ai_count.setValue(az_times_counts[current_time_str])
                    
                self.view.tab_dashboard.add_log(f"🚀 [AUTO A-Z] Tới giờ vàng {current_time_str}! Bot đang kích hoạt chuỗi Pipeline...")
                
                # Ra lệnh cho phần mềm tự động chạy Pipeline y như có người bấm nút!
                self.handle_run_pipeline()