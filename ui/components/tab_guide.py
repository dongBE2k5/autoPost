# ui/components/tab_guide.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class TabGuide(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        guide_content = QTextEdit()
        guide_content.setReadOnly(True)
        guide_content.setStyleSheet("background-color: #ffffff; padding: 25px; font-size: 15px; line-height: 1.8;")
        guide_content.setHtml("""
        <h2 style='color: #2563eb;'>🚀 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG AUTO-POST PRO</h2>
        <p>Phần mềm giúp bạn tự động hóa quy trình tìm kiếm nội dung TikTok, dùng AI (Gemini) để viết lại thành bài đăng Facebook và tự động lên lịch đăng tải.</p>
        
        <h3 style='color: #f59e0b;'>🟢 CHẾ ĐỘ 1: BỐC BÀI TỪ HÀNG ĐỢI (BÁN TỰ ĐỘNG)</h3>
        <p><i>Phù hợp khi bạn muốn tự tay duyệt từng bài viết trước khi đăng.</i></p>
        <ol>
            <li><b>Bước 1 (Tìm & Viết bài):</b> Nhập từ khóa Trend và Ngữ cảnh -> Bấm <b>BẮT ĐẦU CÀO & PHÂN TÍCH</b>. Tất cả bài AI tạo ra sẽ tự động được lưu vào Kho Content.</li>
            <li><b>Bước 2 (Kiểm duyệt):</b> Bấm <b>MỞ KHO CONTENT ĐÃ TẠO</b> để xem lại, sửa bài.</li>
            <li><b>Bước 3 (Xếp lịch):</b> Tích chọn các bài muốn đăng -> Cài đặt giờ -> Bấm <b>Chuyển vào Hàng đợi</b>.</li>
            <li><b>Bước 4 (Chạy Bot):</b> Quay lại Bảng điều khiển -> Chọn Chế độ 1 -> Bấm <b>BẬT BOT TỰ ĐỘNG</b>.</li>
        </ol>

        <h3 style='color: #16a34a;'>🚀 CHẾ ĐỘ 2: AUTO A-Z (TỰ ĐỘNG HOÀN TOÀN)</h3>
        <p><i>Phù hợp khi bạn muốn bot tự động làm mọi thứ theo giờ đã định.</i></p>
        <ol>
            <li><b>Bước 1 (Chuẩn bị):</b> Nhập từ khóa Trend và Ngữ cảnh bổ sung.</li>
            <li><b>Bước 2 (Lên lịch):</b> Bấm <b>CÀI ĐẶT KHUNG GIỜ</b> để thêm các giờ bạn muốn Bot chạy.</li>
            <li><b>Bước 3 (Chạy Bot):</b> Chọn Chế độ 2 -> Bấm <b>BẬT BOT TỰ ĐỘNG</b>. Cứ đến giờ, Bot sẽ tự động đi tìm video mới, tự dịch, tự viết bài và đăng thẳng lên Facebook!</li>
        </ol>
        """)
        layout.addWidget(guide_content)