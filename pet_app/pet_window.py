import json
import os
import random
import time
import datetime
import sys
from PySide6.QtWidgets import QWidget, QMenu, QApplication
from PySide6.QtCore import Qt, QPoint, QTimer, Signal
from PySide6.QtGui import QAction, QMouseEvent, QScreen
from character import CharacterWidget
from interactions import InteractionOverlay, REACTIONS
from chat_window import ChatWindow
from chat_history import ChatHistoryWindow
from settings_window import SettingsWindow
from theme import Theme
from app_paths import get_data_path, resolve_asset_path

CONFIG_PATH = get_data_path("config.json")

GENERAL_GREETINGS = [
    "Hi！👋", "你好呀！", "你好！", "你来啦～",
    "سالام", "ياخشىمۇ سىز",
]

TIME_GREETINGS = [
    (5, 9, [
        "早晨好☀️", "早！", "起这么早呀～", "早安！",
        "新的一天开始啦！", "今天也要加油💪", "早睡早起身体好～",
        "太阳晒屁股啦🌞",
        "خەيرلىك ئەتىگەن", "ئەتىگەنلىك سالام",
        "这么晚还没睡……", "نېمە دېگەن كېچىلىك",
    ]),
    (9, 11.5, [
        "上午好☀️", "早！", "Hi～", "美好的一天～", "精神满满呀！",
        "خەيرلىك ئەتىگەن", "ئەتىگەن خۇش",
    ]),
    (11.5, 14, [
        "中午好🌞", "吃饭了吗？", "午饭吃啥？", "肚子饿了～",
        "该吃饭啦🍚", "午休时间到～", "午饭吃饱饱！",
        "خەيرلىك چۈش", "چۈشتىن خەير", "تاماق يىدڭىزمۇ؟",
    ]),
    (14, 18, [
        "下午好🌇", "Hi～", "下午茶时间☕", "还顺利吗？",
        "忙了一下午～", "快下班啦！", "喝杯咖啡吧～",
        "بىردەم دەم ئېلىۋېلىڭ",
    ]),
    (18, 21, [
        "晚上好🌆", "今天过得怎么样？", "晚饭吃了没？",
        "看什么呢～", "夜晚真美", "该休息一下啦", "喝杯茶吧🍵",
        "خەيرلىك كەچ", "كەچلىك سالام",
    ]),
    (21, 24, [
        "这么晚还没睡😴", "还不睡呀～", "夜猫子！", "天都快亮了……",
        "خەيرلىك تۈن", "نېمە دېگەن كېچىلىك",
    ]),
    (0, 5, [
        "这么晚还没睡😴", "还不睡呀～", "夜猫子！", "天都快亮了……",
        "خەيرلىك تۈن", "نېمە دېگەن كېچىلىك",
    ]),
]

class PetWindow(QWidget):
    def __init__(self, kb=None):
        super().__init__()
        self.kb = kb
        self.config = self.load_config()
        self.drag_position = None
        self.chat_window = None
        self.chat_history_window = None
        self.settings_window = None
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint if self.config.get("always_on_top", True) else Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 360)

        self.character = CharacterWidget(self)
        self.character.setGeometry(0, 0, 300, 360)

        self.overlay = InteractionOverlay(self)
        self.overlay.setGeometry(0, 0, 300, 360)
        self.overlay.hide()

        self.double_click_times = []
        self.annoyed_stage = 0
        self.annoyed_timer = QTimer(self)
        self.annoyed_timer.setSingleShot(True)
        self.annoyed_timer.timeout.connect(self.reset_annoyed)

        self.character.escaped.connect(self.on_escaped)

        self.move_to_default_position()

        QTimer.singleShot(500, self.do_startup_greeting)

    def get_startup_greeting(self):
        hour = datetime.datetime.now().hour + datetime.datetime.now().minute / 60
        pool = []
        for start_h, end_h, msgs in TIME_GREETINGS:
            if start_h <= hour < end_h:
                pool = list(msgs)
                break
        if not pool:
            pool = ["Hi！👋"]
        greeting = random.choice(pool)
        if random.random() < 0.5:
            greeting = random.choice([greeting, random.choice(GENERAL_GREETINGS)])
        return greeting

    def do_startup_greeting(self):
        self.character.start_greeting()
        text = self.get_startup_greeting()
        self.overlay.show_text(text)

    def move_to_default_position(self):
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            x = geometry.width() - self.width() - 50
            y = geometry.height() - self.height() - 60
            self.move(x, y)

    def load_config(self):
        default = {
            "api_key": "",
            "model_name": "deepseek-v4-flash",
            "always_on_top": True,
            "auto_start": False,
            "pet_size": 300,
            "user_avatar_path": "",
            "pet_avatar_path": "",
        }
        app_dir = os.path.dirname(os.path.abspath(__file__))
        api_txt_path = os.path.join(app_dir, "..", "apikey.txt")
        if os.path.exists(api_txt_path):
            try:
                with open(api_txt_path, "r", encoding="utf-8") as f:
                    lines = f.read().strip().split("\n")
                    if len(lines) >= 1 and lines[0].strip():
                        default["api_key"] = lines[0].strip()
                    if len(lines) >= 2 and lines[1].strip():
                        default["model_name"] = lines[1].strip()
            except:
                pass
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    result = {**default, **config}
                    for key in ("user_avatar_path", "pet_avatar_path"):
                        path = result.get(key, "")
                        if path:
                            resolved = resolve_asset_path(path)
                            if resolved:
                                result[key] = resolved
                            else:
                                result[key] = ""
                    return result
            except:
                pass
        return default

    def save_config(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            if self.character.state in ("walk_away", "run_away"):
                self.annoyed_stage = 0
                self.annoyed_timer.stop()
            self.character.stop_walking()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_position = None
            if self.character.state not in ("idle", "greeting", "dancing", "speechless", "walk_away", "run_away"):
                self.character.resume_idle()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            now = time.time()
            self.double_click_times.append(now)
            self.double_click_times = [t for t in self.double_click_times if now - t <= 10]
            count = len(self.double_click_times)

            if count >= 6 and self.annoyed_stage == 0:
                self.annoyed_stage = 1
                self.character.start_speechless()
                self.overlay.show_text("点上瘾了？")
                self.annoyed_timer.start(3000)
                return
            elif self.annoyed_stage == 1:
                self.annoyed_stage = 2
                self.character.start_speechless()
                self.overlay.show_text("还点？？！")
                self.annoyed_timer.start(3000)
                return
            elif self.annoyed_stage == 2:
                self.annoyed_stage = 3
                self.character.start_walk_away()
                self.overlay.show_text("溜了……")
                self.annoyed_timer.stop()
                return
            elif self.annoyed_stage == 3:
                self.annoyed_stage = 4
                self.character.start_run_away()
                self.overlay.show_text("快跑！！~~")
                self.annoyed_timer.stop()
                return
            elif self.annoyed_stage == 4:
                self.annoyed_stage = 0
                self.annoyed_timer.stop()

            if random.random() < 0.5:
                self.character.start_greeting()
            else:
                self.character.start_dancing()
            text = random.choice(REACTIONS)
            self.overlay.show_text(text)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
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

        chat_action = QAction("打开聊天", self)
        chat_action.triggered.connect(self.open_chat)
        menu.addAction(chat_action)

        history_action = QAction("聊天记录", self)
        history_action.triggered.connect(self.open_chat_history)
        menu.addAction(history_action)

        menu.addSeparator()

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.quit_app)
        menu.addAction(exit_action)

        menu.exec_(self.mapToGlobal(pos))

    def quit_app(self):
        if self.chat_window is not None:
            self.chat_window.close()
        if self.chat_history_window is not None:
            self.chat_history_window.close()
        if self.settings_window is not None:
            self.settings_window.close()
        QApplication.quit()

    def on_escaped(self):
        if self.annoyed_stage == 3:
            self.overlay.hide_bubble()
            self.annoyed_timer.start(5000)
        elif self.annoyed_stage == 4:
            self.overlay.hide_bubble()
            self.annoyed_stage = 0

    def reset_annoyed(self):
        self.annoyed_stage = 0

    def trigger_random_interaction(self):
        self.overlay.show_interaction()

    def open_chat(self):
        if self.chat_window is None or not self.chat_window.isVisible():
            self.chat_window = ChatWindow(self.config, self.kb)
            self.chat_window.show()
        else:
            self.chat_window.raise_()
            self.chat_window.activateWindow()

    def open_chat_history(self):
        if self.chat_history_window is None or not self.chat_history_window.isVisible():
            self.chat_history_window = ChatHistoryWindow()
            self.chat_history_window.show()
        else:
            self.chat_history_window.raise_()
            self.chat_history_window.activateWindow()

    def open_settings(self):
        if self.settings_window is None or not self.settings_window.isVisible():
            self.settings_window = SettingsWindow(self.config, self)
            self.settings_window.show()
        else:
            self.settings_window.raise_()
            self.settings_window.activateWindow()

    def apply_config(self):
        self.config = self.load_config()
        new_size = self.config.get("pet_size", 300)
        old_size = self.width()
        if new_size != old_size:
            new_h = new_size + 60
            self.setFixedSize(new_size, new_h)
            self.character.setGeometry(0, 0, new_size, new_h)
            self.character.resize_pet(new_size)
            self.overlay.setGeometry(0, 0, new_size, new_h)
            screen = QApplication.primaryScreen()
            if screen:
                sg = screen.availableGeometry()
                self.move(
                    min(self.x(), sg.width() - new_size - 10),
                    min(self.y(), sg.height() - new_h - 10),
                )
        flags = Qt.FramelessWindowHint | Qt.Tool
        if self.config.get("always_on_top", True):
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()