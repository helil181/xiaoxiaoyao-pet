import random
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont

from theme import Theme

REACTIONS = [
    "嘿嘿~ 摸摸头！",
    "今天也开心~",
    "你好呀！",
    "嘻嘻~",
    "晃悠晃悠~",
    "想你了~",
    "抱抱！",
    "好无聊哦..."
]

class InteractionOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        self.bubble = QLabel(self)
        self.bubble.setAlignment(Qt.AlignCenter)
        self.bubble.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, 220);
            color: #333333;
            border: 2px solid #ff99cc;
            border-radius: 12px;
            padding: 6px 12px;
            font-size: 14px;
            font-weight: bold;
            font-family: {Theme.FONT_FAMILY};
        """)
        self.bubble.setVisible(False)

        self.bounce_anim = QPropertyAnimation(self, b"geometry")
        self.bounce_anim.setDuration(400)
        self.bounce_anim.setEasingCurve(QEasingCurve.OutBounce)
        self.bounce_anim.finished.connect(self.on_bounce_finished)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.fade_out)

    def show_interaction(self):
        text = random.choice(REACTIONS)
        self.bubble.setText(text)
        self.bubble.adjustSize()
        bw = min(self.bubble.width() + 24, self.width() - 10)
        bh = self.bubble.height() + 12
        bx = (self.width() - bw) // 2
        by = 16
        self.bubble.setGeometry(bx, by, bw, bh)
        self.bubble.setVisible(True)
        self.bubble.raise_()

        orig = self.geometry()
        self.bounce_anim.setStartValue(QRect(orig.x(), orig.y() - 15, orig.width(), orig.height()))
        self.bounce_anim.setEndValue(orig)
        self.bounce_anim.start()

        self.show()
        self.raise_()
        self.hide_timer.start(2500)

    def show_text(self, text):
        self.bubble.setText(text)
        self.bubble.adjustSize()
        bw = min(self.bubble.width() + 24, self.width() - 10)
        bh = self.bubble.height() + 12
        bx = (self.width() - bw) // 2
        by = 16
        self.bubble.setGeometry(bx, by, bw, bh)
        self.bubble.setVisible(True)
        self.bubble.raise_()

        orig = self.geometry()
        self.bounce_anim.setStartValue(QRect(orig.x(), orig.y() - 15, orig.width(), orig.height()))
        self.bounce_anim.setEndValue(orig)
        self.bounce_anim.start()

        self.show()
        self.raise_()
        self.hide_timer.start(2500)

    def on_bounce_finished(self):
        pass

    def fade_out(self):
        self.bubble.setVisible(False)
        self.hide()

    def hide_bubble(self):
        self.hide_timer.stop()
        self.bubble.setVisible(False)
        self.hide()

    def paintEvent(self, event):
        pass