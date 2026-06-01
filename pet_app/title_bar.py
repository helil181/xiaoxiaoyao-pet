from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QMouseEvent, QFont

from theme import Theme


class TitleBar(QWidget):
    close_clicked = Signal()
    minimize_clicked = Signal()

    def __init__(self, title_text="", parent=None):
        super().__init__(parent)
        self._drag_pos = None
        self._parent = parent
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            TitleBar {{
                background-color: {Theme.TITLE_BAR_BG};
                border-top-left-radius: {Theme.RADIUS_XXL};
                border-top-right-radius: {Theme.RADIUS_XXL};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(0)

        self.icon_label = QLabel("🐱")
        self.icon_label.setFixedWidth(24)
        self.icon_label.setStyleSheet("background: transparent; font-size: 16px;")
        layout.addWidget(self.icon_label)

        self.title_label = QLabel(title_text)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: {Theme.FONT_SIZE_LG};
                font-weight: bold;
                font-family: {Theme.FONT_FAMILY};
                background: transparent;
                padding-left: 6px;
            }}
        """)
        layout.addWidget(self.title_label)

        layout.addStretch()

        self.minimize_btn = QPushButton("─")
        self.minimize_btn.setFixedSize(28, 24)
        self.minimize_btn.setCursor(Qt.PointingHandCursor)
        self.minimize_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_MUTED};
                border: none;
                border-radius: {Theme.RADIUS_SM};
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.TITLE_BAR_BTN_HOVER};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        self.minimize_btn.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self.minimize_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(28, 24)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_MUTED};
                border: none;
                border-radius: {Theme.RADIUS_SM};
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.TITLE_BAR_CLOSE_HOVER};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        self.close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.close_btn)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self._parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self._parent.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None