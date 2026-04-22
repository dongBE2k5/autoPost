# ui/dialogs/toast.py
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor

class CustomToast(QFrame):
    def __init__(self, parent, title, message, is_error=False):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        bg_color = "#fef2f2" if is_error else "#f0fdf4"
        border_color = "#ef4444" if is_error else "#22c55e"
        text_color = "#991b1b" if is_error else "#166534"
        title_color = "#7f1d1d" if is_error else "#14532d"
        icon_text = "❌" if is_error else "✅"

        self.setStyleSheet(f"QFrame#ToastFrame {{ background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 10px; }}")

        self.frame = QFrame(self)
        self.frame.setObjectName("ToastFrame")
        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(15, 15, 15, 15)

        title_lbl = QLabel(f"{icon_text}  {title}")
        title_lbl.setStyleSheet(f"font-weight: bold; font-size: 16px; color: {title_color};")
        layout.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(f"font-size: 14px; color: {text_color}; margin-top: 5px;")
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(self.frame)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.frame.setGraphicsEffect(shadow)

        self.adjustSize()
        
        if parent:
            parent_rect = parent.geometry()
            start_x = parent_rect.width() - self.width() - 20
            start_y = 40
            self.move(start_x, start_y - 50) 

            self.anim = QPropertyAnimation(self, b"pos")
            self.anim.setDuration(400)
            self.anim.setStartValue(QPoint(start_x, start_y - 30))
            self.anim.setEndValue(QPoint(start_x, start_y))
            self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
            self.anim.start()

        self.show()
        self.raise_()
        QTimer.singleShot(3500, self.close)