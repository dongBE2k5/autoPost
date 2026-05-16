from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QLabel, QScrollArea, QWidget, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

class ReviewDialog(QDialog):
    def __init__(self, posts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 Duyệt Nội Dung Trước Khi Tạo Media")
        self.setMinimumSize(800, 600)
        
        # Lưu các QTextEdit để lấy lại nội dung sau khi sửa
        self.text_edits = []
        
        self.init_ui(posts)

    def init_ui(self, posts):
        main_layout = QVBoxLayout(self)
        
        # Header
        lbl_title = QLabel("Bạn có thể chỉnh sửa nội dung, thêm emoji tùy thích trước khi tạo ảnh/video.")
        lbl_title.setStyleSheet("color: #475569; font-style: italic; margin-bottom: 10px;")
        main_layout.addWidget(lbl_title)
        
        # Scroll Area chứa các bài đăng
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        for i, post_content in enumerate(posts, 1):
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background: white;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                }
            """)
            frame_layout = QVBoxLayout(frame)
            
            lbl_post = QLabel(f"<b>Bài {i}</b>")
            lbl_post.setStyleSheet("color: #1e293b; font-size: 14px; border: none;")
            frame_layout.addWidget(lbl_post)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(post_content)
            text_edit.setMinimumHeight(150)
            text_edit.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 14px;
                    background: #f8fafc;
                }
                QTextEdit:focus {
                    border: 1px solid #3b82f6;
                    background: white;
                }
            """)
            frame_layout.addWidget(text_edit)
            
            self.text_edits.append(text_edit)
            scroll_layout.addWidget(frame)
            
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_cancel = QPushButton("❌ Hủy bỏ (Dừng Pipeline)")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #ef4444; color: white; padding: 10px 20px;
                border-radius: 6px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #dc2626; }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        btn_approve = QPushButton("✅ Duyệt & Bắt Đầu Tạo Media")
        btn_approve.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_approve.setStyleSheet("""
            QPushButton {
                background-color: #10b981; color: white; padding: 10px 20px;
                border-radius: 6px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        btn_approve.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_approve)
        
        main_layout.addLayout(btn_layout)

    def get_edited_posts(self):
        return [edit.toPlainText().strip() for edit in self.text_edits if edit.toPlainText().strip()]
