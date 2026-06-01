import sys
import os
import ctypes

if sys.platform == "win32":
    ctypes.windll.kernel32.FreeConsole()

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QAction, QPainter, QColor
from PySide6.QtCore import Qt
from pet_window import PetWindow
from knowledge_base import KnowledgeBase
import cloud_db
from theme import Theme
from app_paths import get_app_dir


def _get_app_icon():
    script_dir = get_app_dir()
    icon_path = os.path.join(script_dir, "sprites", "idle_frames", "frame_0002.png")
    if os.path.exists(icon_path):
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            return QIcon(pixmap), pixmap

    fallback = QPixmap(32, 32)
    fallback.fill(Qt.transparent)
    painter = QPainter(fallback)
    painter.setBrush(QColor(Theme.ACCENT))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, 28, 28)
    painter.setPen(QColor("#ffffff"))
    painter.drawText(fallback.rect(), Qt.AlignCenter, "耀")
    painter.end()
    return QIcon(fallback), fallback


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")

    icon, pixmap = _get_app_icon()
    app.setWindowIcon(icon)

    kb = KnowledgeBase()
    window = PetWindow(kb)
    window.setWindowIcon(icon)
    window.show()

    tray_icon = QSystemTrayIcon(icon, app)

    tray_menu = QMenu()
    tray_menu.setStyleSheet(f"""
        QMenu {{
            background-color: {Theme.BG_CARD};
            color: {Theme.TEXT_PRIMARY};
            border: 1px solid {Theme.BORDER};
            border-radius: {Theme.RADIUS_MD};
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 24px;
            border-radius: {Theme.RADIUS_SM};
        }}
        QMenu::item:selected {{
            background-color: {Theme.ACCENT};
        }}
        QMenu::separator {{
            height: 1px;
            background: {Theme.BORDER};
            margin: 4px 8px;
        }}
    """)

    show_action = QAction("显示/隐藏小小耀")
    show_action.triggered.connect(lambda: toggle_window(window))
    tray_menu.addAction(show_action)

    chat_action = QAction("打开聊天")
    chat_action.triggered.connect(window.open_chat)
    tray_menu.addAction(chat_action)

    settings_action = QAction("设置")
    settings_action.triggered.connect(window.open_settings)
    tray_menu.addAction(settings_action)

    tray_menu.addSeparator()

    quit_action = QAction("退出")
    quit_action.triggered.connect(window.quit_app)
    tray_menu.addAction(quit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.activated.connect(lambda reason: handle_tray_activation(reason, window))
    tray_icon.show()

    sys.exit(app.exec())

def toggle_window(window):
    if window.isVisible():
        window.hide()
    else:
        window.show()
        window.raise_()
        window.activateWindow()

def handle_tray_activation(reason, window):
    if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
        toggle_window(window)

if __name__ == "__main__":
    main()