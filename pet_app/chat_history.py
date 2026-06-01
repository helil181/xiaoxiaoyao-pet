from datetime import datetime
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QFrame, QLineEdit,
                               QMessageBox, QToolTip, QGridLayout, QSizePolicy,
                               QButtonGroup, QApplication)
from PySide6.QtCore import Qt, QDate, QTimer, Signal, QPoint, QEvent
from PySide6.QtGui import QFont, QIcon

from local_cache import (get_all_messages, get_messages_by_date, delete_message,
                         delete_messages_by_date, get_dates_with_messages,
                         get_favorites, remove_favorite, get_all_tags)
from theme import Theme
from title_bar import TitleBar
from app_paths import get_app_dir

import calendar


class DateCell(QWidget):
    clicked = Signal(str)

    def __init__(self, date_str, has_messages):
        super().__init__()
        self.date_str = date_str
        self.has_messages = has_messages
        self.tooltip_timer = QTimer(self)
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(QToolTip.hideText)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        day = str(int(date_str.split('-')[-1]))

        self.btn = QPushButton(day)
        self.btn.setFixedSize(46, 32)
        self.btn.setCursor(Qt.PointingHandCursor if has_messages else Qt.ArrowCursor)

        if has_messages:
            self.btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: #ffffff;
                    border: none;
                    border-radius: {Theme.RADIUS_SM};
                    font-size: {Theme.FONT_SIZE_MD};
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.BG_CARD};
                }}
            """)
            self.btn.clicked.connect(self._emit_clicked)
        else:
            self.btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {Theme.TEXT_DIM};
                    border: none;
                    border-radius: {Theme.RADIUS_SM};
                    font-size: {Theme.FONT_SIZE_MD};
                    padding: 0px;
                }}
            """)

        layout.addWidget(self.btn, alignment=Qt.AlignCenter)

        if has_messages:
            dot = QLabel("•")
            dot.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 10px; background: transparent;")
            dot.setAlignment(Qt.AlignCenter)
            dot.setFixedHeight(8)
            layout.addWidget(dot, alignment=Qt.AlignCenter)
        else:
            spacer = QWidget()
            spacer.setFixedHeight(8)
            layout.addWidget(spacer)

        self.btn.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.btn and not self.has_messages:
            if event.type() == QEvent.Enter:
                pos = self.btn.mapToGlobal(QPoint(0, self.btn.height()))
                QToolTip.showText(pos, "那天你没理我～")
                self.tooltip_timer.start(3000)
            elif event.type() == QEvent.Leave:
                QToolTip.hideText()
                self.tooltip_timer.stop()
        return super().eventFilter(obj, event)

    def _emit_clicked(self):
        self.clicked.emit(self.date_str)


class PickerCell(QWidget):
    clicked = Signal(int)

    def __init__(self, text, value, has_messages, is_current=False):
        super().__init__()
        self.value = value
        self.has_messages = has_messages
        self.is_current = is_current
        self.tooltip_timer = QTimer(self)
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(QToolTip.hideText)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn = QPushButton(text)
        self.btn.setFixedSize(72, 30)
        self.btn.setCursor(Qt.PointingHandCursor if (has_messages or is_current) else Qt.ArrowCursor)

        if is_current:
            self.btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.ACCENT};
                    color: #ffffff;
                    border: none;
                    border-radius: {Theme.RADIUS_SM};
                    font-size: {Theme.FONT_SIZE_LG};
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.ACCENT_HOVER};
                }}
            """)
            self.btn.clicked.connect(self._emit_clicked)
        elif has_messages:
            self.btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: #ffffff;
                    border: none;
                    border-radius: {Theme.RADIUS_SM};
                    font-size: {Theme.FONT_SIZE_LG};
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.BG_CARD};
                }}
            """)
            self.btn.clicked.connect(self._emit_clicked)
        else:
            self.btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {Theme.TEXT_DIM};
                    border: none;
                    border-radius: {Theme.RADIUS_SM};
                    font-size: {Theme.FONT_SIZE_LG};
                    padding: 0px;
                }}
            """)

        layout.addWidget(self.btn, alignment=Qt.AlignCenter)

        if has_messages:
            dot = QLabel("•")
            dot.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 10px; background: transparent;")
            dot.setAlignment(Qt.AlignCenter)
            dot.setFixedHeight(8)
            layout.addWidget(dot, alignment=Qt.AlignCenter)
        else:
            spacer = QWidget()
            spacer.setFixedHeight(8)
            layout.addWidget(spacer)

        self.btn.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.btn and not self.has_messages and not self.is_current:
            if event.type() == QEvent.Enter:
                pos = self.btn.mapToGlobal(QPoint(0, self.btn.height()))
                QToolTip.showText(pos, "那天你没理我～")
                self.tooltip_timer.start(3000)
            elif event.type() == QEvent.Leave:
                QToolTip.hideText()
                self.tooltip_timer.stop()
        return super().eventFilter(obj, event)

    def _emit_clicked(self):
        self.clicked.emit(self.value)


class CalendarPanel(QFrame):
    date_selected = Signal(str)

    def __init__(self, dates_with_messages, parent=None):
        super().__init__(parent)
        self.dates_with_messages = dates_with_messages
        self.current_year = QDate.currentDate().year()
        self.current_month = QDate.currentDate().month()
        self.mode = "calendar"
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"""
            CalendarPanel {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_XL};
            }}
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(4)

        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(30, 24)
        self.prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #ffffff;
                border: none;
                border-radius: {Theme.RADIUS_SM};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_CARD};
            }}
        """)
        self.prev_btn.clicked.connect(self.on_prev)

        self.year_btn = QPushButton()
        self.year_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #ffffff;
                border: none;
                border-radius: {Theme.RADIUS_SM};
                font-size: 14px;
                font-weight: bold;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_CARD};
            }}
        """)
        self.year_btn.clicked.connect(self.switch_to_year_mode)

        year_label = QLabel("年")
        year_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; background: transparent;")

        self.month_btn = QPushButton()
        self.month_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #ffffff;
                border: none;
                border-radius: {Theme.RADIUS_SM};
                font-size: 14px;
                font-weight: bold;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_CARD};
            }}
        """)
        self.month_btn.clicked.connect(self.switch_to_month_mode)

        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(30, 24)
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #ffffff;
                border: none;
                border-radius: {Theme.RADIUS_SM};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_CARD};
            }}
        """)
        self.next_btn.clicked.connect(self.on_next)

        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.year_btn)
        nav_layout.addWidget(year_label)
        nav_layout.addWidget(self.month_btn)
        nav_layout.addWidget(self.next_btn)
        main_layout.addLayout(nav_layout)

        today_btn = QPushButton("今天")
        today_btn.setFixedSize(60, 24)
        today_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: #ffffff;
                border: none;
                border-radius: {Theme.RADIUS_SM};
                font-size: {Theme.FONT_SIZE_SM};
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_HOVER};
            }}
        """)
        today_btn.clicked.connect(self.go_today)
        self.today_btn = today_btn
        main_layout.addWidget(today_btn, alignment=Qt.AlignCenter)

        self.headers_widget = QWidget()
        self.headers_widget.setStyleSheet("background: transparent;")
        headers_layout = QHBoxLayout(self.headers_widget)
        headers_layout.setContentsMargins(0, 0, 0, 0)
        headers_layout.setSpacing(2)
        for day_name in ["日", "一", "二", "三", "四", "五", "六"]:
            label = QLabel(day_name)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedSize(46, 20)
            label.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: {Theme.FONT_SIZE_SM}; background: transparent;")
            headers_layout.addWidget(label)
        main_layout.addWidget(self.headers_widget)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(2)
        main_layout.addLayout(self.grid_layout)

        self.rebuild_content()

    def update_nav_labels(self):
        self.year_btn.setText(f"{self.current_year} ▼")
        self.month_btn.setText(f"{self.current_month}月 ▼")

    def rebuild_content(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.update_nav_labels()

        if self.mode == "calendar":
            self.headers_widget.show()
            self.build_calendar_grid()
        elif self.mode == "year":
            self.headers_widget.hide()
            self.build_year_grid()
        elif self.mode == "month":
            self.headers_widget.hide()
            self.build_month_grid()

    def build_calendar_grid(self):
        first_day, num_days = calendar.monthrange(self.current_year, self.current_month)
        row = 0
        for day in range(1, num_days + 1):
            col = (first_day + day - 1) % 7
            date_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
            has_messages = date_str in self.dates_with_messages
            cell = DateCell(date_str, has_messages)
            cell.clicked.connect(self._on_date_clicked)
            self.grid_layout.addWidget(cell, row, col)
            if col == 6:
                row += 1

    def build_year_grid(self):
        start_year = self.current_year - 5
        for i in range(12):
            year = start_year + i
            has_messages = any(d.startswith(str(year)) for d in self.dates_with_messages)
            cell = PickerCell(str(year), year, has_messages, is_current=(year == self.current_year))
            cell.clicked.connect(self.select_year)
            row = i // 4
            col = i % 4
            self.grid_layout.addWidget(cell, row, col)

    def build_month_grid(self):
        for m in range(1, 13):
            has_messages = any(d.startswith(f"{self.current_year}-{m:02d}") for d in self.dates_with_messages)
            cell = PickerCell(f"{m}月", m, has_messages, is_current=(m == self.current_month))
            cell.clicked.connect(self.select_month)
            row = (m - 1) // 4
            col = (m - 1) % 4
            self.grid_layout.addWidget(cell, row, col)

    def select_year(self, year):
        self.current_year = year
        self.mode = "calendar"
        self.rebuild_content()

    def select_month(self, month):
        self.current_month = month
        self.mode = "calendar"
        self.rebuild_content()

    def switch_to_year_mode(self):
        self.mode = "year"
        self.rebuild_content()

    def switch_to_month_mode(self):
        self.mode = "month"
        self.rebuild_content()

    def on_prev(self):
        if self.mode == "calendar":
            self.prev_month()
        elif self.mode == "year":
            self.current_year -= 12
            self.rebuild_content()
        elif self.mode == "month":
            self.current_year -= 1
            self.rebuild_content()

    def on_next(self):
        if self.mode == "calendar":
            self.next_month()
        elif self.mode == "year":
            self.current_year += 12
            self.rebuild_content()
        elif self.mode == "month":
            self.current_year += 1
            self.rebuild_content()

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.rebuild_content()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.rebuild_content()

    def _on_date_clicked(self, date_str):
        self.date_selected.emit(date_str)
        self.close()

    def go_today(self):
        today = QDate.currentDate()
        self.current_year = today.year()
        self.current_month = today.month()
        self.mode = "calendar"
        self.rebuild_content()
        self.date_selected.emit(today.toString("yyyy-MM-dd"))
        self.close()


class ChatHistoryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.current_date_str = QDate.currentDate().toString("yyyy-MM-dd")
        self._message_frames = {}
        self._highlight_id = None
        self.is_searching = False
        self._chat_history_loaded = False
        self.init_ui()
        QTimer.singleShot(50, self.load_history)

    def init_ui(self):
        self.setWindowTitle("聊天记录")
        self.setFixedSize(440, 580)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("ChatHistoryWindow { border: 1px solid #2c2c2c; }")

        icon_path = os.path.join(get_app_dir(), "sprites", "idle_frames", "frame_0002.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = TitleBar("聊天记录", self)
        title_bar.close_clicked.connect(self.close)
        title_bar.minimize_clicked.connect(self.showMinimized)
        main_layout.addWidget(title_bar)

        tab_bar = QHBoxLayout()
        tab_bar.setContentsMargins(14, 8, 14, 4)
        tab_bar.setSpacing(4)

        self._chat_tab_btn = self._create_tab_btn("💬 聊天记录")
        self._chat_tab_btn.clicked.connect(self._show_chat_tab)
        tab_bar.addWidget(self._chat_tab_btn)

        self._fav_tab_btn = self._create_tab_btn("⭐ 收藏")
        self._fav_tab_btn.clicked.connect(self._show_fav_tab)
        tab_bar.addWidget(self._fav_tab_btn)

        tab_bar.addStretch()
        main_layout.addLayout(tab_bar)

        self._chat_panel = QWidget()
        self._fav_panel = QWidget()

        self._build_chat_panel()
        self._build_fav_panel()

        main_layout.addWidget(self._chat_panel)
        main_layout.addWidget(self._fav_panel)
        self._fav_panel.hide()
        self._chat_tab_btn.setStyleSheet(self._tab_btn_style(active=True))
        self._fav_tab_btn.setStyleSheet(self._tab_btn_style(active=False))

    def _create_tab_btn(self, text):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._tab_btn_style(active=False))
        return btn

    def _tab_btn_style(self, active=False):
        if active:
            return f"""
                QPushButton {{
                    background-color: {Theme.ACCENT};
                    color: #ffffff;
                    border: none;
                    border-radius: {Theme.RADIUS_MD};
                    padding: 6px 14px;
                    font-size: {Theme.FONT_SIZE_MD};
                    font-weight: bold;
                    font-family: {Theme.FONT_FAMILY};
                }}
            """
        return f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_MUTED};
                border: none;
                border-radius: {Theme.RADIUS_MD};
                padding: 6px 14px;
                font-size: {Theme.FONT_SIZE_MD};
                font-family: {Theme.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Theme.BORDER};
                color: {Theme.TEXT_PRIMARY};
            }}
        """

    def _show_chat_tab(self):
        self._fav_panel.hide()
        self._chat_panel.show()
        self._chat_tab_btn.setStyleSheet(self._tab_btn_style(active=True))
        self._fav_tab_btn.setStyleSheet(self._tab_btn_style(active=False))
        if not self._chat_history_loaded:
            self.load_history()

    def _show_fav_tab(self):
        self._chat_panel.hide()
        self._fav_panel.show()
        self._chat_tab_btn.setStyleSheet(self._tab_btn_style(active=False))
        self._fav_tab_btn.setStyleSheet(self._tab_btn_style(active=True))
        self._load_favorites()

    def _build_chat_panel(self):
        panel = self._chat_panel
        panel.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.BG_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                font-family: {Theme.FONT_FAMILY};
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        search_layout = QHBoxLayout()
        search_layout.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索关键词...")
        self.search_input.returnPressed.connect(self.search_messages)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.INPUT_BG};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_MD};
                padding: 7px 12px;
                font-size: {Theme.FONT_SIZE_MD};
                font-family: {Theme.FONT_FAMILY};
            }}
            QLineEdit:focus {{
                border-color: {Theme.ACCENT};
            }}
        """)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("搜索")
        search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: #ffffff;
                border: none;
                border-radius: {Theme.RADIUS_MD};
                padding: 7px 16px;
                font-size: {Theme.FONT_SIZE_MD};
                font-family: {Theme.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_HOVER};
            }}
        """)
        search_btn.clicked.connect(self.search_messages)
        search_layout.addWidget(search_btn)

        clear_search_btn = QPushButton("清除")
        clear_search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_MUTED};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_MD};
                padding: 7px 16px;
                font-size: {Theme.FONT_SIZE_MD};
                font-family: {Theme.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Theme.BORDER};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_search_btn)

        layout.addLayout(search_layout)

        self.search_results_widget = QWidget()
        self.search_results_layout = QVBoxLayout(self.search_results_widget)
        self.search_results_layout.setAlignment(Qt.AlignTop)
        self.search_results_layout.setSpacing(2)
        self.search_results_layout.setContentsMargins(0, 0, 0, 0)
        results_scroll = QScrollArea(panel)
        results_scroll.setWidgetResizable(True)
        results_scroll.setWidget(self.search_results_widget)
        results_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_XL};
                background-color: {Theme.BG_SECONDARY};
            }}
        """)
        results_scroll.hide()
        self.search_results_scroll = results_scroll
        layout.addWidget(results_scroll)

        date_layout = QHBoxLayout()
        date_layout.setSpacing(6)

        self.date_button = QPushButton("📅 " + QDate.currentDate().toString("yyyy-MM-dd") + "  ▼")
        self.date_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: #ffffff;
                border: none;
                border-radius: {Theme.RADIUS_MD};
                padding: 7px 14px;
                font-size: {Theme.FONT_SIZE_MD};
                font-family: {Theme.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_HOVER};
            }}
        """)
        self.date_button.clicked.connect(self.show_calendar)
        date_layout.addWidget(self.date_button)

        delete_day_btn = QPushButton("删除当日")
        delete_day_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.DANGER};
                color: #fff;
                border: none;
                border-radius: {Theme.RADIUS_MD};
                padding: 7px 14px;
                font-size: {Theme.FONT_SIZE_MD};
                font-family: {Theme.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Theme.DANGER_HOVER};
            }}
        """)
        delete_day_btn.clicked.connect(self.delete_current_day)
        date_layout.addWidget(delete_day_btn)

        layout.addLayout(date_layout)

        scroll = QScrollArea(panel)
        scroll.setWidgetResizable(True)
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

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(4)
        self.content_layout.setContentsMargins(8, 8, 8, 8)

        scroll.setWidget(self.content_widget)
        self.scroll = scroll
        layout.addWidget(scroll)

    def _build_fav_panel(self):
         panel = self._fav_panel
         panel.setStyleSheet(f"""
             QWidget {{
                 background-color: {Theme.BG_PRIMARY};
                 color: {Theme.TEXT_PRIMARY};
                 font-family: {Theme.FONT_FAMILY};
             }}
         """)
         layout = QVBoxLayout(panel)
         layout.setContentsMargins(14, 14, 14, 14)
         layout.setSpacing(8)

         tag_bar = QHBoxLayout()
         tag_bar.setSpacing(4)

         all_btn = QPushButton("全部")
         all_btn.setCheckable(True)
         all_btn.setChecked(True)
         all_btn.setCursor(Qt.PointingHandCursor)
         all_btn.setStyleSheet(self._tag_btn_style(active=True))
         all_btn.clicked.connect(lambda: self._filter_fav_by_tag(None))
         tag_bar.addWidget(all_btn)
         self._fav_all_btn = all_btn

         self._fav_tag_buttons = []

         fav_scroll = QScrollArea(panel)
         fav_scroll.setWidgetResizable(True)
         fav_scroll.setStyleSheet(f"""
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

         self._fav_content = QWidget()
         self._fav_content.setStyleSheet("background: transparent;")
         self._fav_content_layout = QVBoxLayout(self._fav_content)
         self._fav_content_layout.setAlignment(Qt.AlignTop)
         self._fav_content_layout.setSpacing(4)
         self._fav_content_layout.setContentsMargins(8, 8, 8, 8)

         fav_scroll.setWidget(self._fav_content)
         self._fav_scroll = fav_scroll

         self._fav_sort_combo = QHBoxLayout()
         sort_label = QLabel("排序：")
         sort_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: {Theme.FONT_SIZE_SM}; background: transparent;")
         self._fav_sort_combo.addWidget(sort_label)

         sort_time_btn = QPushButton("收藏时间")
         sort_time_btn.setCheckable(True)
         sort_time_btn.setChecked(True)
         sort_time_btn.setCursor(Qt.PointingHandCursor)
         sort_time_btn.setStyleSheet(self._tag_btn_style(active=True))
         sort_time_btn.clicked.connect(lambda: self._set_fav_sort("time"))
         self._fav_sort_time_btn = sort_time_btn
         self._fav_sort_combo.addWidget(sort_time_btn)

         sort_msg_btn = QPushButton("消息时间")
         sort_msg_btn.setCheckable(True)
         sort_msg_btn.setCursor(Qt.PointingHandCursor)
         sort_msg_btn.setStyleSheet(self._tag_btn_style(active=False))
         sort_msg_btn.clicked.connect(lambda: self._set_fav_sort("msg"))
         self._fav_sort_msg_btn = sort_msg_btn
         self._fav_sort_combo.addWidget(sort_msg_btn)

         self._fav_sort_combo.addStretch()

         layout.addLayout(tag_bar)
         layout.addLayout(self._fav_sort_combo)
         layout.addWidget(fav_scroll)

    def _tag_btn_style(self, active=False):
        if active:
            return f"""
                QPushButton {{
                    background-color: {Theme.ACCENT};
                    color: #ffffff;
                    border: none;
                    border-radius: {Theme.RADIUS_SM};
                    padding: 4px 10px;
                    font-size: {Theme.FONT_SIZE_SM};
                    font-family: {Theme.FONT_FAMILY};
                }}
            """
        return f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_MUTED};
                border: none;
                border-radius: {Theme.RADIUS_SM};
                padding: 4px 10px;
                font-size: {Theme.FONT_SIZE_SM};
                font-family: {Theme.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Theme.BORDER};
                color: {Theme.TEXT_PRIMARY};
            }}
        """

    def _set_fav_sort(self, mode):
        self._fav_sort_mode = mode
        self._fav_sort_time_btn.setStyleSheet(self._tag_btn_style(active=(mode == "time")))
        self._fav_sort_msg_btn.setStyleSheet(self._tag_btn_style(active=(mode == "msg")))
        self._load_favorites()

    def _load_favorites(self):
        self._clear_fav_content()
        tag = getattr(self, '_current_fav_tag', None)
        favs = get_favorites(tag=tag)

        sort_mode = getattr(self, '_fav_sort_mode', 'time')
        if sort_mode == "msg":
            favs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        self._rebuild_tag_buttons()

        if not favs:
            empty = QLabel("暂无收藏的消息")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: {Theme.FONT_SIZE_LG}; padding: 30px; font-family: {Theme.FONT_FAMILY};")
            self._fav_content_layout.addWidget(empty)
            return

        for fav in favs:
            self._add_fav_card(fav)

    def _rebuild_tag_buttons(self):
        for btn in self._fav_tag_buttons:
            btn.setParent(None)
            btn.deleteLater()
        self._fav_tag_buttons.clear()

        tags = get_all_tags()
        for tag_name in tags:
            btn = QPushButton(tag_name)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            current_tag = getattr(self, '_current_fav_tag', None)
            btn.setStyleSheet(self._tag_btn_style(active=(tag_name == current_tag)))
            btn.clicked.connect(lambda checked, t=tag_name: self._filter_fav_by_tag(t))
            self._fav_tag_buttons.append(btn)

            tag_bar = self._fav_panel.layout().itemAt(0).layout()
            tag_bar.insertWidget(tag_bar.count() - 1, btn)

    def _filter_fav_by_tag(self, tag):
        self._current_fav_tag = tag
        self._fav_all_btn.setStyleSheet(self._tag_btn_style(active=(tag is None)))
        for btn in self._fav_tag_buttons:
            btn.setStyleSheet(self._tag_btn_style(active=(btn.text() == tag)))
        self._load_favorites()

    def _clear_fav_content(self):
        while self._fav_content_layout.count():
            item = self._fav_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add_fav_card(self, fav):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_MD};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(3)

        sender = "你" if fav["role"] == "user" else "小小耀"
        sender_color = Theme.ACCENT if fav["role"] == "user" else Theme.BG_SURFACE
        tag_text = f" <span style='color: {Theme.ACCENT}; background-color: rgba(233,69,96,0.15); padding: 1px 6px; border-radius: 3px; font-size: 10px;'>{fav['tag']}</span>" if fav.get("tag") else ""

        try:
            msg_date = fav["timestamp"][:10]
            msg_time = fav["timestamp"][11:19]
        except:
            msg_date = "未知"
            msg_time = ""

        meta = QLabel(f"<span style='color: {sender_color}; font-weight: bold;'>{sender}</span>"
                      f"<span style='color: {Theme.TEXT_DIM}; font-size: 11px;'>  {msg_date} {msg_time}</span>"
                      f"{tag_text}"
                      f"<span style='color: {Theme.TEXT_DIM}; font-size: 10px;'>  收藏于 {fav['created_at'][:19]}</span>")
        meta.setStyleSheet("background: transparent;")
        card_layout.addWidget(meta)

        content_label = QLabel(fav["content"])
        content_label.setWordWrap(True)
        content_label.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: {Theme.FONT_SIZE_MD}; background: transparent; font-family: {Theme.FONT_FAMILY};")
        card_layout.addWidget(content_label)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 2, 0, 0)
        delete_btn = QPushButton("取消收藏")
        delete_btn.setFixedSize(70, 22)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.DANGER};
                color: #fff;
                border: none;
                border-radius: {Theme.RADIUS_SM};
                font-size: {Theme.FONT_SIZE_XS};
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                background-color: {Theme.DANGER_HOVER};
            }}
        """)
        delete_btn.clicked.connect(lambda: self._remove_fav(fav["id"]))
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)

        self._fav_content_layout.addWidget(card)

    def _remove_fav(self, fav_id):
        remove_favorite(fav_id)
        self._load_favorites()

    def scroll_to_bottom(self):
        QTimer.singleShot(0, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))

    def show_calendar(self):
        if hasattr(self, 'calendar_panel') and self.calendar_panel.isVisible():
            self.calendar_panel.close()
            return
        dates_with_messages = get_dates_with_messages()
        self.calendar_panel = CalendarPanel(dates_with_messages, self)
        self.calendar_panel.date_selected.connect(self.on_date_selected)
        btn_pos = self.date_button.mapToGlobal(QPoint(0, self.date_button.height() + 2))
        self.calendar_panel.move(btn_pos)
        self.calendar_panel.show()

    def on_date_selected(self, date_str):
        self.current_date_str = date_str
        self.date_button.setText("📅 " + date_str + "  ▼")
        self.search_input.clear()
        self.clear_content()
        self.is_searching = False
        self.search_results_scroll.hide()
        self.scroll.show()
        messages = get_messages_by_date(date_str)
        if not messages:
            self.add_center_text("该日暂无聊天记录")
        else:
            self.display_messages(messages)
        self.scroll_to_bottom()

    def load_history(self):
        self.clear_content()
        self.is_searching = False
        self.search_results_scroll.hide()
        self.scroll.show()
        self.date_button.setText("📅 " + QDate.currentDate().toString("yyyy-MM-dd") + "  ▼")
        self.current_date_str = QDate.currentDate().toString("yyyy-MM-dd")
        self.search_input.clear()
        self._highlight_id = None
        self._chat_history_loaded = True
        messages = get_all_messages()
        self.display_messages(messages)
        self.scroll_to_bottom()

    def clear_search(self):
        self.search_input.clear()
        self.is_searching = False
        self.clear_search_results()
        self.search_results_scroll.hide()
        self.scroll.show()
        self.load_history()

    def search_messages(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            self.clear_search()
            return

        self.clear_content()
        self.clear_search_results()
        self.is_searching = True
        self.scroll.hide()
        self.search_results_scroll.show()

        messages = get_all_messages()
        filtered = [m for m in messages if keyword.lower() in m["content"].lower()]

        if not filtered:
            no_result = QLabel("没有找到相关聊天记录")
            no_result.setAlignment(Qt.AlignCenter)
            no_result.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: {Theme.FONT_SIZE_LG}; padding: 30px; font-family: {Theme.FONT_FAMILY};")
            self.search_results_layout.addWidget(no_result)
            return

        result_count = QLabel(f"找到 {len(filtered)} 条相关记录")
        result_count.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: {Theme.FONT_SIZE_SM}; padding: 4px 8px; font-family: {Theme.FONT_FAMILY};")
        self.search_results_layout.addWidget(result_count)

        for msg in filtered:
            self._add_search_result_card(msg, keyword)

    def _make_snippet(self, text, keyword):
        idx = text.lower().find(keyword.lower())
        if idx == -1:
            s = text[:60]
            return s + ("..." if len(text) > 60 else "")

        ctx = 18
        start = max(0, idx - ctx)
        end = min(len(text), idx + len(keyword) + ctx)

        prefix = "…" if start > 0 else ""
        suffix = "…" if end < len(text) else ""

        before = text[start:idx]
        kw = text[idx:idx + len(keyword)]
        after = text[idx + len(keyword):end]

        html = f"{prefix}{before}<span style='background-color: {Theme.ACCENT}; color: #ffffff; font-weight: bold; padding: 1px 3px; border-radius: 2px;'>{kw}</span>{after}{suffix}"
        return html

    def _add_search_result_card(self, msg, keyword):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_MD};
                padding: 6px 8px;
            }}
            QFrame:hover {{
                background-color: {Theme.BORDER};
                border-color: {Theme.ACCENT};
            }}
        """)
        card.setCursor(Qt.PointingHandCursor)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(4)

        try:
            msg_date = msg["timestamp"][:10]
            msg_time = msg["timestamp"][11:19]
        except:
            msg_date = "未知日期"
            msg_time = ""

        sender = "你" if msg["role"] == "user" else "小小耀"
        sender_color = Theme.ACCENT if msg["role"] == "user" else Theme.BG_SURFACE

        meta = QLabel(f"<span style='color: {Theme.TEXT_DIM}; font-size: 11px;'>{msg_date} {msg_time}</span>  "
                      f"<span style='color: {sender_color}; font-size: 11px; font-weight: bold;'>{sender}</span>")
        meta.setStyleSheet("background: transparent;")
        card_layout.addWidget(meta)

        snippet = QLabel(self._make_snippet(msg["content"], keyword))
        snippet.setWordWrap(True)
        snippet.setTextFormat(Qt.RichText)
        snippet.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: {Theme.FONT_SIZE_MD}; background: transparent;")
        snippet.setMaximumHeight(48)
        card_layout.addWidget(snippet)

        def make_handler(m):
            return lambda: self._navigate_to_message(m)
        card.mousePressEvent = make_handler(msg)

        self.search_results_layout.addWidget(card)

    def clear_search_results(self):
        while self.search_results_layout.count():
            item = self.search_results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _navigate_to_message(self, msg):
        try:
            msg_date = msg["timestamp"][:10]
        except:
            return

        self.current_date_str = msg_date
        self.date_button.setText("📅 全部记录  ▼")
        self.search_input.clear()
        self.clear_search_results()
        self.is_searching = False
        self.search_results_scroll.hide()
        self.scroll.show()

        self.clear_content()
        self._highlight_id = msg["id"]
        messages = get_all_messages()
        self.display_messages(messages, highlight_id=msg["id"])

    def delete_current_day(self):
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除 {self.current_date_str} 的所有聊天记录吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_messages_by_date(self.current_date_str)
            self._chat_history_loaded = False
            self.on_date_selected(self.current_date_str)
            self._refresh_calendar_dots()

    def clear_content(self):
        self._message_frames.clear()
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def add_center_text(self, text):
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: {Theme.FONT_SIZE_LG}; padding: 20px; font-family: {Theme.FONT_FAMILY};")
        self.content_layout.addWidget(label)

    def display_messages(self, messages, highlight_id=None):
        if not messages:
            self.add_center_text("暂无聊天记录")
            return

        current_date = ""
        count = 0
        for msg in messages:
            try:
                msg_date = msg["timestamp"][:10]
            except:
                msg_date = "未知日期"

            if msg_date != current_date:
                current_date = msg_date
                date_label = QLabel(f"── {current_date} ──")
                date_label.setAlignment(Qt.AlignCenter)
                date_label.setStyleSheet(f"""
                    color: {Theme.ACCENT};
                    font-size: {Theme.FONT_SIZE_SM};
                    font-weight: bold;
                    font-family: {Theme.FONT_FAMILY};
                    padding: 10px 0 6px 0;
                    background: transparent;
                """)
                self.content_layout.addWidget(date_label)

            sender = "你" if msg["role"] == "user" else "小小耀"
            bg_color = Theme.ACCENT if msg["role"] == "user" else Theme.BG_CARD
            is_highlight = (highlight_id is not None and msg["id"] == highlight_id)

            msg_frame = QFrame()
            highlight_border = f"border: 2px solid {Theme.ACCENT};" if is_highlight else ""
            msg_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border-radius: {Theme.RADIUS_LG};
                    padding: 6px 10px;
                    margin: 2px 0;
                    {highlight_border}
                }}
            """)

            msg_layout = QVBoxLayout(msg_frame)
            msg_layout.setContentsMargins(10, 6, 10, 6)
            msg_layout.setSpacing(3)

            header = QLabel(f"<b>{sender}</b>  {msg['timestamp'][11:19]}")
            header_color = "rgba(0,0,0,0.7)" if is_highlight else "rgba(255,255,255,0.7)"
            header.setStyleSheet(f"color: {header_color}; font-size: {Theme.FONT_SIZE_XS}; background: transparent;")
            msg_layout.addWidget(header)

            content = QLabel(msg["content"])
            content.setWordWrap(True)
            content_color = "#1e1e2e" if is_highlight else "#fff"
            content.setStyleSheet(f"color: {content_color}; font-size: {Theme.FONT_SIZE_MD}; background: transparent; font-family: {Theme.FONT_FAMILY};")
            content.setTextInteractionFlags(Qt.TextSelectableByMouse)
            msg_layout.addWidget(content)

            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 2, 0, 0)

            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(50, 24)
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.DANGER};
                    color: #fff;
                    border: none;
                    border-radius: {Theme.RADIUS_SM};
                    font-size: {Theme.FONT_SIZE_XS};
                    padding: 2px 6px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.DANGER_HOVER};
                }}
            """)
            msg_id = msg["id"]
            delete_btn.clicked.connect(lambda checked, mid=msg_id: self.delete_single_message(mid))
            btn_layout.addWidget(delete_btn)
            btn_layout.addStretch()
            msg_layout.addLayout(btn_layout)

            self._message_frames[msg["id"]] = msg_frame
            self.content_layout.addWidget(msg_frame)

            count += 1
            if count % 15 == 0:
                QApplication.instance().processEvents()

        if highlight_id is not None:
            QTimer.singleShot(200, lambda: self._scroll_to_message(highlight_id))

    def _scroll_to_message(self, msg_id):
        frame = self._message_frames.get(msg_id)
        if not frame:
            return

        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        pos_y = frame.mapTo(self.content_widget, QPoint(0, 0)).y()
        view_h = self.scroll.viewport().height()
        target = max(0, pos_y - view_h // 3)
        self.scroll.verticalScrollBar().setValue(target)

        def restore_style():
            try:
                frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {Theme.BG_CARD};
                        border-radius: {Theme.RADIUS_LG};
                        padding: 6px 10px;
                        margin: 2px 0;
                    }}
                """)
            except:
                pass

        QTimer.singleShot(1800, restore_style)

    def delete_single_message(self, msg_id):
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这条消息吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_message(msg_id)
            self.load_history()
            self._refresh_calendar_dots()

    def _refresh_calendar_dots(self):
        if hasattr(self, 'calendar_panel') and self.calendar_panel and self.calendar_panel.isVisible():
            self.calendar_panel.dates_with_messages = get_dates_with_messages()
            self.calendar_panel.rebuild_content()