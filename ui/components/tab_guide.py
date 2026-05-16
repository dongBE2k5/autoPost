# ui/components/tab_guide.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class TabGuide(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        guide_content = QTextEdit()
        guide_content.setReadOnly(True)
        guide_content.setStyleSheet("background-color: #ffffff; padding: 25px; font-size: 15px; line-height: 1.8;")
        guide_content.setHtml("""
        <h2 style='color: #2563eb;'>🚀 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG AUTO-POST PRO</h2>
        <p>Phần mềm giúp bạn tự động hóa quy trình sáng tạo nội dung Facebook dựa trên Tài liệu có sẵn hoặc Phân tích Trend TikTok bằng AI (Gemini), có hỗ trợ tạo Ảnh & Video minh họa tự động.</p>
        
        <h3 style='color: #f59e0b;'>🟢 CHẾ ĐỘ 1: BỐC BÀI TỪ HÀNG ĐỢI (BÁN TỰ ĐỘNG)</h3>
        <p><i>Phù hợp khi bạn muốn tự tay duyệt hoặc chỉnh sửa từng bài viết trước khi đăng tải.</i></p>
        <ol>
            <li><b>Bước 1 (Chuẩn bị Dữ liệu):</b> 
                <ul>
                    <li><i>Cách 1 (Dùng Tài liệu):</i> Tải lên các File tài liệu (TXT, PDF, DOCX) ở mục <b>Tài liệu sản phẩm</b>.</li>
                    <li><i>Cách 2 (Cào TikTok):</i> Tích vào <b>Search Trend TikTok</b>, nhập Chủ đề, Nguồn và Hashtag.</li>
                </ul>
            </li>
            <li><b>Bước 2 (Sinh Nội Dung):</b> Tích chọn tạo Ảnh/Video nếu cần. Sau đó bấm <b>BẮT ĐẦU CÀO & PHÂN TÍCH</b>. Tất cả bài viết AI tạo ra sẽ tự động được lưu vào Kho Content.</li>
            <li><b>Bước 3 (Kiểm duyệt):</b> Bấm <b>MỞ KHO CONTENT</b> để xem lại, sửa bài, hoặc tải lại ảnh.</li>
            <li><b>Bước 4 (Xếp lịch):</b> Tại Kho Content, tích chọn các bài muốn đăng -> Cài đặt giờ -> Bấm <b>Chuyển vào Hàng đợi</b>.</li>
            <li><b>Bước 5 (Chạy Bot):</b> Quay lại Bảng điều khiển -> Mục Thiết lập Chế độ Bot: Chọn <b>Bốc bài từ Hàng Đợi</b> -> Bấm <b>BẬT BOT</b>.</li>
        </ol>

        <h3 style='color: #16a34a;'>🚀 CHẾ ĐỘ 2: AUTO A-Z (TỰ ĐỘNG HOÀN TOÀN)</h3>
        <p><i>Phù hợp khi bạn muốn bot tự động lên mạng tìm kiếm, phân tích, viết bài, sinh media và đăng tự động theo các khung giờ cố định.</i></p>
        <ol>
            <li><b>Bước 1 (Chuẩn bị Định hướng):</b> Nhập Tài liệu hoặc thông tin tìm kiếm TikTok, nhập các Prompt, Yêu cầu cấm và Giới hạn từ.</li>
            <li><b>Bước 2 (Lên lịch):</b> Bấm <b>CÀI ĐẶT KHUNG GIỜ</b> để thêm danh sách các mốc thời gian bạn muốn Bot tự hoạt động trong ngày.</li>
            <li><b>Bước 3 (Chạy Bot):</b> Mục Thiết lập Chế độ Bot: Chọn <b>Auto A-Z</b> -> Bấm <b>BẬT BOT</b>. 
            <br><i>Cứ đến giờ đã hẹn, Bot sẽ tự động thực hiện từ A-Z mọi quy trình và đăng thẳng lên Facebook!</i></li>
        </ol>
        """)
        layout.addWidget(guide_content)