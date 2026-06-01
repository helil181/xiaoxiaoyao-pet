import os
import sys
import threading
import json
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                               QPushButton, QLabel, QScrollArea, QFrame,
                               QApplication, QSizePolicy, QMenu, QDialog,
                               QLineEdit, QDialogButtonBox, QToolTip, QInputDialog,
                               QSystemTrayIcon)
from PySide6.QtCore import Qt, QTimer, QObject, Signal, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QTextCursor, QClipboard, QIcon, QPixmap

from ai_chat import chat_with_deepseek, translate_text, SYSTEM_PROMPT, build_enhanced_system_prompt
from local_cache import save_message, get_all_messages, add_favorite, remove_favorite_by_message_id, is_favorite, get_all_tags
from cloud_db import trigger_sync
from knowledge_base import KnowledgeBase
from theme import Theme
from title_bar import TitleBar
from app_paths import get_data_path, get_app_dir


TRANSLATE_HISTORY_FILE = get_data_path("translate_history.json")


class ChatSignals(QObject):
    streaming = Signal(str)
    finished = Signal(str)
    error = Signal(str)


def load_translate_history():
    try:
        if os.path.exists(TRANSLATE_HISTORY_FILE):
            with open(TRANSLATE_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return []


def save_translate_history(languages):
    try:
        with open(TRANSLATE_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(languages, f, ensure_ascii=False, indent=2)
    except:
        pass


class TranslateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_language = None
        self.history = load_translate_history()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("翻译")
        self.setFixedSize(300, 280)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                font-family: {Theme.FONT_FAMILY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("选择翻译语言")
        title.setStyleSheet(f"font-size: {Theme.FONT_SIZE_XL}; font-weight: bold; color: {Theme.ACCENT};")
        layout.addWidget(title)

        if self.history:
            recent_label = QLabel("最近使用：")
            recent_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: {Theme.FONT_SIZE_SM};")
            layout.addWidget(recent_label)

            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(6)
            btn_layout.addStretch()
            for lang in self.history[-4:]:
                btn = QPushButton(lang)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Theme.BG_CARD};
                        color: {Theme.TEXT_PRIMARY};
                        border: 1px solid {Theme.BORDER};
                        border-radius: {Theme.RADIUS_MD};
                        padding: 4px 12px;
                        font-size: {Theme.FONT_SIZE_SM};
                    }}
                    QPushButton:hover {{
                        background-color: {Theme.ACCENT};
                        border-color: {Theme.ACCENT};
                    }}
                """)
                btn.clicked.connect(lambda checked, l=lang: self.select_language(l))
                btn_layout.addWidget(btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)

        custom_label = QLabel("或输入目标语言：")
        custom_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: {Theme.FONT_SIZE_SM};")
        layout.addWidget(custom_label)

        self.lang_input = QLineEdit()
        self.lang_input.setPlaceholderText("如：日语、法语、维吾尔语、文言文...")
        self.lang_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.INPUT_BG};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_MD};
                padding: 8px 12px;
                font-size: {Theme.FONT_SIZE_LG};
            }}
            QLineEdit:focus {{
                border-color: {Theme.ACCENT};
            }}
        """)
        self.lang_input.returnPressed.connect(self.confirm_custom)
        layout.addWidget(self.lang_input)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        confirm_btn = QPushButton("翻译")
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                border-radius: {Theme.RADIUS_MD};
                padding: 8px 24px;
                font-size: {Theme.FONT_SIZE_LG};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_HOVER};
            }}
        """)
        confirm_btn.clicked.connect(self.confirm_custom)
        btn_layout.addWidget(confirm_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_MUTED};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_MD};
                padding: 8px 24px;
                font-size: {Theme.FONT_SIZE_LG};
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_CARD};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def select_language(self, lang):
        self.selected_language = lang
        self.accept()

    def confirm_custom(self):
        lang = self.lang_input.text().strip()
        if lang:
            if lang not in self.history:
                self.history.append(lang)
                save_translate_history(self.history)
            self.selected_language = lang
            self.accept()


class TypingIndicator(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 4)
        layout.setSpacing(0)

        self._label = QLabel("小小耀正在输入")
        self._label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_MUTED};
                font-size: {Theme.FONT_SIZE_SM};
                font-family: {Theme.FONT_FAMILY};
                background: transparent;
                font-style: italic;
            }}
        """)
        layout.addWidget(self._label)
        layout.addStretch()

        self._tick = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(500)

    def _animate(self):
        self._tick = (self._tick + 1) % 4
        dots = "." * self._tick
        self._label.setText(f"小小耀正在输入{dots}")


class MessageBubble(QFrame):
    def __init__(self, sender, content, is_user=False, timestamp=None, avatar_path=None):
        super().__init__()
        self._sender = sender
        self._content = content
        self._is_user = is_user
        self._timestamp = timestamp or datetime.now().strftime("%H:%M")
        self._avatar_path = avatar_path

        self.setStyleSheet("background: transparent;")
        self._selected = False

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 2, 4, 4)
        main_layout.setSpacing(8)

        avatar = QLabel(sender[0])
        avatar.setFixedSize(Theme.AVATAR_SIZE, Theme.AVATAR_SIZE)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {'#e94560' if is_user else '#0f3460'};
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                border-radius: 16px;
                font-family: {Theme.FONT_FAMILY};
            }}
        """)

        if avatar_path:
            pixmap = Theme.create_circular_pixmap(avatar_path, Theme.AVATAR_SIZE)
            if pixmap and not pixmap.isNull():
                avatar.setPixmap(pixmap)
                avatar.setStyleSheet(f"""
                    QLabel {{
                        border-radius: {Theme.AVATAR_SIZE // 2}px;
                    }}
                """)

        self._avatar = avatar

        content_col = QVBoxLayout()
        content_col.setSpacing(2)
        content_col.setContentsMargins(0, 0, 0, 0)

        self.content_edit = QTextEdit()
        self.content_edit.setReadOnly(True)
        self.content_edit.setPlainText(content)
        self.content_edit.setMaximumWidth(280)
        self.content_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_edit.setFocusPolicy(Qt.NoFocus)
        self.content_edit.setCursor(Qt.ArrowCursor)
        self.content_edit.viewport().setCursor(Qt.ArrowCursor)
        self.content_edit.setStyleSheet(f"""
            QTextEdit {{
                color: #ffffff;
                font-size: 14px;
                padding: 8px 12px;
                border-radius: {Theme.RADIUS_LG};
                border: none;
                background-color: {'#e94560' if is_user else '#1e2a4a'};
                font-family: {Theme.FONT_FAMILY};
            }}
        """)
        self.content_edit.document().setDocumentMargin(0)
        self.content_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.content_edit.customContextMenuRequested.connect(self._show_context_menu)
        self.content_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        doc = self.content_edit.document()
        doc.contentsChanged.connect(self.auto_resize)
        QTimer.singleShot(0, self.auto_resize)

        time_label = QLabel(self._timestamp)
        time_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_DIM};
                font-size: {Theme.FONT_SIZE_XS};
                font-family: {Theme.FONT_FAMILY};
                background: transparent;
            }}
        """)

        if is_user:
            content_col.addWidget(self.content_edit, alignment=Qt.AlignRight)
            content_col.addWidget(time_label, alignment=Qt.AlignRight)
            main_layout.addStretch()
            main_layout.addLayout(content_col)
            main_layout.addWidget(avatar, alignment=Qt.AlignTop)
        else:
            content_col.addWidget(self.content_edit, alignment=Qt.AlignLeft)
            content_col.addWidget(time_label, alignment=Qt.AlignLeft)
            main_layout.addWidget(avatar, alignment=Qt.AlignTop)
            main_layout.addLayout(content_col)
            main_layout.addStretch()

    def mousePressEvent(self, event):
        parent = self.window()
        if hasattr(parent, '_multi_select_active') and parent._multi_select_active:
            self._selected = not self._selected
            if self._selected:
                self.setStyleSheet("MessageBubble { background: transparent; border: 2px solid #e94560; border-radius: 12px; }")
            else:
                self.setStyleSheet("background: transparent;")
            if hasattr(parent, '_update_multi_info'):
                parent._update_multi_info()

    def auto_resize(self):
        self.content_edit.document().setTextWidth(self.content_edit.viewport().width())
        height = int(self.content_edit.document().size().height()) + 16
        self.content_edit.setFixedHeight(height)

    def update_content(self, text):
        self._content = text
        self.content_edit.setPlainText(text)
        self.auto_resize()

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_MD};
                padding: 4px;
                font-family: {Theme.FONT_FAMILY};
                font-size: {Theme.FONT_SIZE_MD};
            }}
            QMenu::item {{
                padding: 6px 20px;
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

        copy_action = menu.addAction("📋 复制")
        copy_action.triggered.connect(self._copy_content)
        menu.addSeparator()
        quote_action = menu.addAction("💬 引用回复")
        quote_action.triggered.connect(self._quote_reply)
        translate_action = menu.addAction("🌐 翻译")
        translate_action.triggered.connect(self._translate)
        menu.addSeparator()
        multi_select_action = menu.addAction("☑️ 多选")
        multi_select_action.triggered.connect(self._multi_select)
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ 删除")
        delete_action.triggered.connect(self._delete_message)

        menu.addSeparator()

        parent_win = self.window()
        if hasattr(parent_win, 'message_id_map') and id(self) in parent_win.message_id_map:
            msg_id = parent_win.message_id_map[id(self)]
            if is_favorite(msg_id):
                fav_action = menu.addAction("⭐ 取消收藏")
                fav_action.triggered.connect(lambda: self._unfavorite(msg_id))
            else:
                fav_action = menu.addAction("☆ 收藏")
                fav_action.triggered.connect(lambda: self._add_favorite(msg_id))

        menu.exec_(self.content_edit.viewport().mapToGlobal(pos))

    def _copy_content(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._content)

    def _quote_reply(self):
        parent = self.window()
        if hasattr(parent, 'set_reference_message'):
            parent.set_reference_message(self._content, self._sender)

    def _translate(self):
        parent = self.window()
        if hasattr(parent, 'translate_message'):
            parent.translate_message(self._content, self)

    def _delete_message(self):
        parent = self.window()
        if hasattr(parent, 'delete_chat_message'):
            parent.delete_chat_message(self)
        else:
            self.setParent(None)
            self.deleteLater()

    def _multi_select(self):
        parent = self.window()
        if hasattr(parent, 'enter_multi_select_mode'):
            parent.enter_multi_select_mode()

    def _add_favorite(self, msg_id):
        parent = self.window()
        dlg = FavTagDialog(get_all_tags(), parent)
        if dlg.exec() == QDialog.Accepted:
            add_favorite(msg_id, dlg.tag.strip())
            if hasattr(parent, 'show_system_message'):
                parent.show_system_message("已收藏 ⭐")

    def _unfavorite(self, msg_id):
        remove_favorite_by_message_id(msg_id)
        parent = self.window()
        if hasattr(parent, 'show_system_message'):
            parent.show_system_message("已取消收藏")


class FavTagDialog(QDialog):
    def __init__(self, existing_tags, parent=None):
        super().__init__(parent)
        self.tag = ""
        self.setWindowTitle("收藏标签")
        self.setFixedSize(320, 220)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet(f"""
            FavTagDialog {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_XL};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        prompt = QLabel("输入标签名或点击已有标签快速选择：")
        prompt.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: {Theme.FONT_SIZE_MD}; background: transparent; font-family: {Theme.FONT_FAMILY};")
        layout.addWidget(prompt)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入标签名（可选）")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.INPUT_BG};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_MD};
                padding: 8px 12px;
                font-size: {Theme.FONT_SIZE_MD};
                font-family: {Theme.FONT_FAMILY};
            }}
            QLineEdit:focus {{
                border-color: {Theme.ACCENT};
            }}
        """)
        self.input_field.returnPressed.connect(self._accept)
        layout.addWidget(self.input_field)

        if existing_tags:
            tags_label = QLabel("已有标签：")
            tags_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: {Theme.FONT_SIZE_SM}; background: transparent; font-family: {Theme.FONT_FAMILY};")
            layout.addWidget(tags_label)

            tags_flow = QHBoxLayout()
            tags_flow.setSpacing(6)
            tags_flow.setContentsMargins(0, 0, 0, 0)
            for tag_name in existing_tags:
                btn = QPushButton(tag_name)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {Theme.BG_CARD};
                        color: {Theme.TEXT_PRIMARY};
                        border: 1px solid {Theme.BORDER};
                        border-radius: {Theme.RADIUS_SM};
                        padding: 4px 10px;
                        font-size: {Theme.FONT_SIZE_XS};
                        font-family: {Theme.FONT_FAMILY};
                    }}
                    QPushButton:hover {{
                        background-color: {Theme.ACCENT};
                        border-color: {Theme.ACCENT};
                        color: #ffffff;
                    }}
                """)
                btn.clicked.connect(lambda checked, t=tag_name: self._select_tag(t))
                tags_flow.addWidget(btn)
            tags_flow.addStretch()
            layout.addLayout(tags_flow)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_MUTED};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_MD};
                padding: 8px 14px;
                font-size: {Theme.FONT_SIZE_MD};
                font-family: {Theme.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: #ffffff;
                border: none;
                border-radius: {Theme.RADIUS_MD};
                padding: 8px 14px;
                font-size: {Theme.FONT_SIZE_MD};
                font-weight: bold;
                font-family: {Theme.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_HOVER};
            }}
        """)
        ok_btn.clicked.connect(self._accept)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

    def _select_tag(self, tag_name):
        self.input_field.setText(tag_name)

    def _accept(self):
        self.tag = self.input_field.text().strip()
        self.accept()


class ChatWindow(QWidget):
    def __init__(self, config, kb=None):
        super().__init__()
        self.config = config
        self.kb = kb
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.is_responding = False
        self.current_assistant_bubble = None
        self.signals = None
        self.chat_thread = None
        self._reference_msg = None
        self.message_id_map = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("和小小耀聊天")
        self.setFixedSize(420, 520)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("ChatWindow { border: 1px solid #2c2c2c; }")

        icon_path = os.path.join(get_app_dir(), "sprites", "idle_frames", "frame_0002.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = TitleBar("小小耀", self)
        title_bar.close_clicked.connect(self.close)
        title_bar.minimize_clicked.connect(self.showMinimized)
        main_layout.addWidget(title_bar)

        body = QWidget()
        body.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.BG_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                font-family: {Theme.FONT_FAMILY};
            }}
        """)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 12, 12, 12)
        body_layout.setSpacing(8)

        scroll = QScrollArea(body)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_XL};
                background-color: {Theme.BG_SECONDARY};
            }}
            QScrollBar:vertical {{
                background: {Theme.SCROLLBAR_BG};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.SCROLLBAR_HANDLE};
                border-radius: {Theme.RADIUS_SM};
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        self.message_container = QWidget()
        self.message_container.setStyleSheet("background: transparent;")
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setAlignment(Qt.AlignTop)
        self.message_layout.setSpacing(6)
        self.message_layout.setContentsMargins(8, 8, 8, 8)

        scroll.setWidget(self.message_container)
        body_layout.addWidget(scroll)

        self.ref_bar = QFrame()
        self.ref_bar.setVisible(False)
        self.ref_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border-left: 3px solid {Theme.ACCENT};
                border-radius: {Theme.RADIUS_MD};
                padding: 6px;
            }}
        """)
        ref_layout = QHBoxLayout(self.ref_bar)
        ref_layout.setContentsMargins(8, 6, 8, 6)
        ref_layout.setSpacing(6)

        ref_content = QVBoxLayout()
        ref_content.setSpacing(2)
        self.ref_sender = QLabel()
        self.ref_sender.setStyleSheet(f"color: {Theme.ACCENT}; font-size: {Theme.FONT_SIZE_SM}; font-weight: bold; background: transparent;")
        self.ref_text = QLabel()
        self.ref_text.setWordWrap(True)
        self.ref_text.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: {Theme.FONT_SIZE_MD}; background: transparent;")
        self.ref_text.setMaximumHeight(40)
        ref_content.addWidget(self.ref_sender)
        ref_content.addWidget(self.ref_text)
        ref_layout.addLayout(ref_content)

        ref_close = QPushButton("✕")
        ref_close.setFixedSize(20, 20)
        ref_close.setCursor(Qt.PointingHandCursor)
        ref_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_MUTED};
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {Theme.ACCENT};
            }}
        """)
        ref_close.clicked.connect(self.clear_reference)
        ref_layout.addWidget(ref_close, alignment=Qt.AlignTop)

        body_layout.addWidget(self.ref_bar)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)

        self.input_field = QTextEdit(body)
        self.input_field.setPlaceholderText("和我说说话吧~")
        self.input_field.setFixedHeight(54)
        self.input_field.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.INPUT_BG};
                color: {Theme.TEXT_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_LG};
                padding: 8px 12px;
                font-size: 14px;
                font-family: {Theme.FONT_FAMILY};
            }}
            QTextEdit:focus {{
                border-color: {Theme.ACCENT};
            }}
        """)
        self.input_field.document().setDocumentMargin(0)
        input_layout.addWidget(self.input_field)

        self.send_btn = QPushButton("发送", body)
        self.send_btn.setFixedSize(60, 54)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: #ffffff;
                border: none;
                border-radius: {Theme.RADIUS_LG};
                font-size: {Theme.FONT_SIZE_LG};
                font-weight: bold;
                font-family: {Theme.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {Theme.ACCENT_DISABLED};
                color: #888;
            }}
        """)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)

        body_layout.addLayout(input_layout)
        main_layout.addWidget(body)

        QTimer.singleShot(50, self._start_load_chat_history)

    def _start_load_chat_history(self):
        cached = get_all_messages()
        if not cached:
            return

        self._history_queue = cached
        self._history_index = 0
        self._history_timer = QTimer(self)
        self._history_timer.timeout.connect(self._load_chat_history_batch)
        self._history_timer.start(10)

    def _load_chat_history_batch(self):
        batch_size = 15
        for _ in range(batch_size):
            if self._history_index >= len(self._history_queue):
                self._history_timer.stop()
                self.scroll_to_bottom()
                return
            msg = self._history_queue[self._history_index]
            timestamp = msg.get("timestamp", "")
            msg_id = msg.get("id")
            try:
                t = timestamp[11:16] if len(timestamp) >= 16 else datetime.now().strftime("%H:%M")
            except:
                t = datetime.now().strftime("%H:%M")
            if msg["role"] == "user":
                bubble = self.add_message("你", msg["content"], is_user=True, timestamp=t, avatar_path=self.config.get("user_avatar_path"))
                if msg_id is not None:
                    self.message_id_map[id(bubble)] = msg_id
                self.messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                bubble = self.add_message("小小耀", msg["content"], is_user=False, timestamp=t, avatar_path=self.config.get("pet_avatar_path"))
                if msg_id is not None:
                    self.message_id_map[id(bubble)] = msg_id
                self.messages.append({"role": "assistant", "content": msg["content"]})
            self._history_index += 1
        QApplication.instance().processEvents()

    def load_chat_history(self):
        cached = get_all_messages()
        for msg in cached:
            timestamp = msg.get("timestamp", "")
            msg_id = msg.get("id")
            try:
                t = timestamp[11:16] if len(timestamp) >= 16 else datetime.now().strftime("%H:%M")
            except:
                t = datetime.now().strftime("%H:%M")
            if msg["role"] == "user":
                bubble = self.add_message("你", msg["content"], is_user=True, timestamp=t, avatar_path=self.config.get("user_avatar_path"))
                if msg_id is not None:
                    self.message_id_map[id(bubble)] = msg_id
                self.messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                bubble = self.add_message("小小耀", msg["content"], is_user=False, timestamp=t, avatar_path=self.config.get("pet_avatar_path"))
                if msg_id is not None:
                    self.message_id_map[id(bubble)] = msg_id
                self.messages.append({"role": "assistant", "content": msg["content"]})

    def scroll_to_bottom(self):
        scroll = self.findChild(QScrollArea)
        if scroll:
            scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())

    def _remove_typing_indicator(self):
        if hasattr(self, '_typing_indicator') and self._typing_indicator:
            ti = self._typing_indicator
            ti._timer.stop()
            ti.setParent(None)
            ti.deleteLater()
            self._typing_indicator = None

    def load_chat_history(self):
        cached = get_all_messages()
        for msg in cached:
            timestamp = msg.get("timestamp", "")
            msg_id = msg.get("id")
            try:
                t = timestamp[11:16] if len(timestamp) >= 16 else datetime.now().strftime("%H:%M")
            except:
                t = datetime.now().strftime("%H:%M")
            if msg["role"] == "user":
                bubble = self.add_message("你", msg["content"], is_user=True, timestamp=t, avatar_path=self.config.get("user_avatar_path"))
                if msg_id is not None:
                    self.message_id_map[id(bubble)] = msg_id
                self.messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                bubble = self.add_message("小小耀", msg["content"], is_user=False, timestamp=t, avatar_path=self.config.get("pet_avatar_path"))
                if msg_id is not None:
                    self.message_id_map[id(bubble)] = msg_id
                self.messages.append({"role": "assistant", "content": msg["content"]})

    def add_message(self, sender, content, is_user=False, timestamp=None, avatar_path=None):
        bubble = MessageBubble(sender, content, is_user, timestamp, avatar_path)
        self.message_layout.addWidget(bubble)
        self.scroll_to_bottom()
        return bubble

    def set_reference_message(self, content, sender):
        self._reference_msg = (content, sender)
        self.ref_sender.setText(f"引用 {sender} 的消息：")
        self.ref_text.setText(content[:100] + ("..." if len(content) > 100 else ""))
        self.ref_bar.setVisible(True)
        self.input_field.setFocus()

    def clear_reference(self):
        self._reference_msg = None
        self.ref_bar.setVisible(False)

    def translate_message(self, content, source_bubble):
        dialog = TranslateDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_language:
            lang = dialog.selected_language
            api_key = self.config.get("api_key", "")
            if not api_key:
                self.show_system_message("请先在设置中配置 API Key")
                return

            placeholder = self._add_translate_placeholder(source_bubble, lang)

            self._trans_pending = True
            self._trans_result = None
            self._trans_placeholder = placeholder
            self._trans_content = content
            self._trans_lang = lang
            self._trans_source_bubble = source_bubble

            def worker():
                try:
                    result = translate_text(
                        api_key,
                        self.config.get("model_name", "deepseek-v4-flash"),
                        content,
                        lang
                    )
                    self._trans_result = result
                except Exception:
                    self._trans_result = None
                finally:
                    self._trans_pending = False

            thread = threading.Thread(target=worker, daemon=True)
            thread.start()
            self._poll_translation()

    def _poll_translation(self):
        if getattr(self, '_trans_pending', False):
            QTimer.singleShot(50, self._poll_translation)
        else:
            placeholder = getattr(self, '_trans_placeholder', None)
            content = getattr(self, '_trans_content', '')
            result = getattr(self, '_trans_result', None)
            lang = getattr(self, '_trans_lang', '')
            source_bubble = getattr(self, '_trans_source_bubble', None)

            self._trans_pending = None
            self._trans_result = None
            self._trans_placeholder = None
            self._trans_content = None
            self._trans_lang = None
            self._trans_source_bubble = None

            if result:
                self._replace_translate_placeholder(placeholder, content, result, lang, source_bubble)
            else:
                self._translate_cleanup(placeholder, "翻译结果为空")

    def _translate_cleanup(self, placeholder, error=None):
        if placeholder:
            placeholder.setParent(None)
            placeholder.deleteLater()
        if error:
            self.show_system_message(f"翻译出错: {str(error)}")
        else:
            self.show_system_message("翻译失败，请重试")

    def _add_translate_placeholder(self, source_bubble, lang):
        placeholder = QLabel(f"🌐 正在翻译为 {lang}...")
        placeholder.setStyleSheet(f"color: {Theme.ACCENT}; font-size: {Theme.FONT_SIZE_XS}; padding: 2px 8px; background: transparent;")
        idx = self._find_bubble_index(source_bubble)
        if idx >= 0:
            self.message_layout.insertWidget(idx + 1, placeholder)
            self.scroll_to_bottom()
        return placeholder

    def _find_bubble_index(self, bubble):
        for i in range(self.message_layout.count()):
            w = self.message_layout.itemAt(i).widget()
            if w is bubble:
                return i
        return -1

    def _replace_translate_placeholder(self, placeholder, original, translated, lang, source_bubble):
        if placeholder:
            placeholder.setParent(None)
            placeholder.deleteLater()

        is_user = source_bubble._is_user if hasattr(source_bubble, '_is_user') else False
        idx = self._find_bubble_index(source_bubble)
        if idx < 0:
            idx = self.message_layout.count() - 1

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border: none;
                border-left: 2px solid {Theme.ACCENT};
                border-radius: {Theme.RADIUS_MD};
            }}
        """)
        card.setCursor(Qt.PointingHandCursor)
        card._translated = True
        card._original = original
        card._translated_text = translated
        card._lang = lang
        card._source_bubble = source_bubble

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(0)
        lang_label = QLabel(f"🌐 {lang}")
        lang_label.setStyleSheet(f"color: {Theme.ACCENT}; font-size: {Theme.FONT_SIZE_XS}; background: transparent;")
        header_layout.addWidget(lang_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        text_label = QLabel(translated)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: {Theme.FONT_SIZE_LG}; background: transparent;")
        layout.addWidget(text_label)

        card._text_label = text_label

        self.message_layout.insertWidget(idx + 1, card)
        self.scroll_to_bottom()

        card.setContextMenuPolicy(Qt.CustomContextMenu)
        card.customContextMenuRequested.connect(lambda pos: self._show_translate_card_menu(card, pos))

    def _show_translate_card_menu(self, card, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_MD};
                padding: 4px;
                font-family: {Theme.FONT_FAMILY};
                font-size: {Theme.FONT_SIZE_MD};
            }}
            QMenu::item {{
                padding: 6px 20px;
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

        copy_action = menu.addAction("📋 复制翻译结果")
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(card._translated_text))

        menu.addSeparator()

        change_action = menu.addAction("🔄 更换翻译语言")
        change_action.triggered.connect(lambda: self._retranslate(card))

        close_action = menu.addAction("✕ 关闭翻译")
        close_action.triggered.connect(lambda: self._close_translate_card(card))

        menu.exec_(card.mapToGlobal(pos))

    def _retranslate(self, card):
        dialog = TranslateDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_language:
            lang = dialog.selected_language
            card._text_label.setText(f"🌐 正在翻译为 {lang}...")
            api_key = self.config.get("api_key", "")
            if not api_key:
                card._text_label.setText("翻译失败：未配置 API Key")
                return

            self._retrans_card = card
            self._retrans_pending = True
            self._retrans_result = None
            self._retrans_lang = lang

            def worker():
                try:
                    result = translate_text(
                        api_key,
                        self.config.get("model_name", "deepseek-v4-flash"),
                        card._original,
                        lang
                    )
                    self._retrans_result = result
                except Exception:
                    self._retrans_result = None
                finally:
                    self._retrans_pending = False

            thread = threading.Thread(target=worker, daemon=True)
            thread.start()
            self._poll_retranslate()

    def _poll_retranslate(self):
        if getattr(self, '_retrans_pending', False):
            QTimer.singleShot(50, self._poll_retranslate)
        else:
            card = getattr(self, '_retrans_card', None)
            result = getattr(self, '_retrans_result', None)
            lang = getattr(self, '_retrans_lang', '')

            self._retrans_card = None
            self._retrans_pending = None
            self._retrans_result = None
            self._retrans_lang = None

            if card and result:
                card._translated_text = result
                card._lang = lang
                card._text_label.setText(result)
            elif card:
                card._text_label.setText("翻译失败")

    def _close_translate_card(self, card):
        card.setParent(None)
        card.deleteLater()

    def delete_chat_message(self, bubble):
        bubble.setParent(None)
        bubble.deleteLater()

    def send_message(self):
        if self.is_responding:
            return
        text = self.input_field.toPlainText().strip()
        if not text:
            return
        if not self.config.get("api_key"):
            self.show_system_message("请先在设置中配置 API Key（设置 → API Key）")
            return

        ref_content = None
        if self._reference_msg:
            ref_content = self._reference_msg[0]
            ref_sender = self._reference_msg[1]
            text_with_ref = f"[引用 {ref_sender}] {ref_content}\n\n{text}"
            self.clear_reference()
        else:
            text_with_ref = text

        self.input_field.clear()
        user_bubble = self.add_message("你", text, is_user=True, avatar_path=self.config.get("user_avatar_path"))
        msg_id, _ = save_message("user", text)
        self.message_id_map[id(user_bubble)] = msg_id
        trigger_sync()
        self.messages.append({"role": "user", "content": text_with_ref})

        self.is_responding = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText("...")

        self.current_assistant_bubble = self.add_message("小小耀", "正在思考~", is_user=False, avatar_path=self.config.get("pet_avatar_path"))

        self._typing_indicator = TypingIndicator()
        self.message_layout.addWidget(self._typing_indicator)
        self.scroll_to_bottom()

        api_key = self.config.get("api_key", "")
        model = self.config.get("model_name", "deepseek-v4-flash")

        cached = get_all_messages()
        if self.config.get("mimic_mode", True) and self.kb is not None and self.kb.is_available():
            enhanced_prompt = build_enhanced_system_prompt(self.kb)
        else:
            enhanced_prompt = SYSTEM_PROMPT
        context = [{"role": "system", "content": enhanced_prompt}]
        for msg in cached:
            context.append({"role": msg["role"], "content": msg["content"]})
        msgs = [context[0]] + context[-5:]

        self.signals = ChatSignals()
        self.signals.streaming.connect(self.on_streaming)
        self.signals.finished.connect(self.on_chat_finished)
        self.signals.error.connect(self.on_chat_error)

        def worker():
            try:
                def on_stream(text):
                    display_text = text.replace("|||", "\n\n")
                    self.signals.streaming.emit(display_text)
                result = chat_with_deepseek(api_key, model, msgs, on_stream)
                if result:
                    self.signals.finished.emit(result)
                else:
                    if self.current_assistant_bubble:
                        self.signals.error.emit("没有收到回复，请检查 API Key 和模型名称是否正确")
            except Exception as e:
                self.signals.error.emit(f"出错了: {str(e)}")

        self.chat_thread = threading.Thread(target=worker, daemon=True)
        self.chat_thread.start()

    def on_streaming(self, content):
        if self.current_assistant_bubble:
            self._remove_typing_indicator()
            self._stream_content = content
            if not hasattr(self, '_stream_timer') or self._stream_timer is None:
                self._stream_timer = QTimer()
                self._stream_timer.setSingleShot(True)
                self._stream_timer.timeout.connect(self._flush_stream)
                self._stream_timer.start(40)
        self.scroll_to_bottom()

    def _flush_stream(self):
        if hasattr(self, '_stream_content') and self.current_assistant_bubble:
            self.current_assistant_bubble.update_content(self._stream_content)
            self._stream_timer = None

    def on_chat_finished(self, result):
        self._remove_typing_indicator()
        if not result:
            self.is_responding = False
            self.send_btn.setEnabled(True)
            self.send_btn.setText("发送")
            self.scroll_to_bottom()
            return

        content = result.replace("|||", "\n\n")

        if self.current_assistant_bubble:
            self.current_assistant_bubble.update_content(content)

        msg_id, _ = save_message("assistant", content)
        if self.current_assistant_bubble:
            self.message_id_map[id(self.current_assistant_bubble)] = msg_id
        trigger_sync()
        self.messages.append({"role": "assistant", "content": content})

        self.is_responding = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")
        self.scroll_to_bottom()

        if self.windowState() & Qt.WindowMinimized or not self.isActiveWindow():
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QSystemTrayIcon):
                    widget.showMessage("小小耀", "小小耀回复你了～", QIcon(), 3000)
                    break

    def on_chat_error(self, error_msg):
        self._remove_typing_indicator()
        if self.current_assistant_bubble:
            self.current_assistant_bubble.update_content(error_msg)
        self.is_responding = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")
        self.scroll_to_bottom()

    def enter_multi_select_mode(self):
        self.show_system_message("已进入多选模式，点击任意消息即可勾选")
        self._multi_select_active = True
        self._selected_messages = []

        self._multi_bar = QFrame()
        self._multi_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.ACCENT};
                border-radius: {Theme.RADIUS_MD};
                padding: 6px;
            }}
        """)
        bar_layout = QHBoxLayout(self._multi_bar)
        bar_layout.setContentsMargins(8, 4, 8, 4)
        bar_layout.setSpacing(6)

        info_label = QLabel("☑️ 已选 0 条")
        info_label.setStyleSheet(f"color: {Theme.ACCENT}; font-size: {Theme.FONT_SIZE_SM}; background: transparent;")
        self._multi_info = info_label
        bar_layout.addWidget(info_label)

        bar_layout.addStretch()

        copy_btn = QPushButton("复制选中")
        copy_btn.setStyleSheet(self._multi_btn_style())
        copy_btn.clicked.connect(self._multi_copy)
        bar_layout.addWidget(copy_btn)

        delete_btn = QPushButton("删除选中")
        delete_btn.setStyleSheet(self._multi_btn_style())
        delete_btn.clicked.connect(self._multi_delete)
        bar_layout.addWidget(delete_btn)

        exit_btn = QPushButton("退出多选")
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.DANGER};
                color: #fff;
                border: none;
                border-radius: {Theme.RADIUS_SM};
                padding: 4px 10px;
                font-size: {Theme.FONT_SIZE_XS};
            }}
            QPushButton:hover {{
                background-color: {Theme.DANGER_HOVER};
            }}
        """)
        exit_btn.clicked.connect(self._exit_multi_select)
        bar_layout.addWidget(exit_btn)

        self.message_layout.addWidget(self._multi_bar)

    def _multi_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {Theme.BG_SURFACE};
                color: #fff;
                border: none;
                border-radius: {Theme.RADIUS_SM};
                padding: 4px 10px;
                font-size: {Theme.FONT_SIZE_XS};
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT};
            }}
        """

    def _update_multi_info(self):
        count = 0
        for i in range(self.message_layout.count()):
            w = self.message_layout.itemAt(i).widget()
            if isinstance(w, MessageBubble) and getattr(w, '_selected', False):
                count += 1
        if hasattr(self, '_multi_info') and self._multi_info:
            self._multi_info.setText(f"☑️ 已选 {count} 条")

    def _exit_multi_select(self):
        self._multi_select_active = False
        self._selected_messages = []
        if hasattr(self, '_multi_bar') and self._multi_bar:
            self._multi_bar.setParent(None)
            self._multi_bar.deleteLater()
            self._multi_bar = None
        if hasattr(self, '_multi_info'):
            self._multi_info = None
        for i in range(self.message_layout.count()):
            w = self.message_layout.itemAt(i).widget()
            if isinstance(w, MessageBubble):
                w._selected = False
                w.setStyleSheet("background: transparent;")
                w.content_edit.setStyleSheet(f"""
                    QTextEdit {{
                        color: #ffffff;
                        font-size: 14px;
                        padding: 8px 12px;
                        border-radius: {Theme.RADIUS_LG};
                        border: none;
                        background-color: {'#e94560' if w._is_user else '#1e2a4a'};
                        font-family: {Theme.FONT_FAMILY};
                    }}
                """)

    def _multi_copy(self):
        texts = []
        for i in range(self.message_layout.count()):
            w = self.message_layout.itemAt(i).widget()
            if isinstance(w, MessageBubble) and getattr(w, '_selected', False):
                texts.append(f"{w._sender}: {w._content}")
        if texts:
            QApplication.clipboard().setText("\n\n".join(texts))
            self.show_system_message(f"已复制 {len(texts)} 条消息")
        self._exit_multi_select()

    def _multi_delete(self):
        to_delete = []
        for i in range(self.message_layout.count()):
            w = self.message_layout.itemAt(i).widget()
            if isinstance(w, MessageBubble) and getattr(w, '_selected', False):
                to_delete.append(w)
        for w in to_delete:
            w.setParent(None)
            w.deleteLater()
        self._exit_multi_select()
        if to_delete:
            self.show_system_message(f"已删除 {len(to_delete)} 条消息")

    def show_system_message(self, content):
        msg = QLabel(content)
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet(f"""
            color: {Theme.ACCENT};
            font-size: {Theme.FONT_SIZE_MD};
            padding: 8px 12px;
            background-color: rgba(233, 69, 96, 0.1);
            border-radius: {Theme.RADIUS_MD};
            font-family: {Theme.FONT_FAMILY};
        """)
        self.message_layout.addWidget(msg)
        self.scroll_to_bottom()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
            self.send_message()
        else:
            super().keyPressEvent(event)