import json
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QLineEdit, QCheckBox, QComboBox,
                               QMessageBox, QFrame, QSlider, QFileDialog,
                               QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from auto_start import set_auto_start
from theme import Theme
from title_bar import TitleBar


class SettingsWindow(QWidget):
    def __init__(self, config, pet_window):
        super().__init__()
        self.config = config
        self.pet_window = pet_window
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("设置")
        self.setFixedSize(400, 580)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("SettingsWindow { border: 1px solid #2c2c2c; }")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = TitleBar("设置", self)
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

        scroll_area = QScrollArea(body)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
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

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(16, 16, 16, 16)
        scroll_layout.setSpacing(16)

        api_card, api_inner = self._create_section_card("🔑 API 配置")

        api_inner.addWidget(self._create_label("API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("输入 DeepSeek API Key")
        self.api_key_input.setText(self.config.get("api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setStyleSheet(self._input_style())
        api_inner.addWidget(self.api_key_input)

        api_inner.addWidget(self._create_label("模型名称:"))
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("deepseek-v4-flash")
        self.model_input.setText(self.config.get("model_name", "deepseek-v4-flash"))
        self.model_input.setStyleSheet(self._input_style())
        api_inner.addWidget(self.model_input)

        scroll_layout.addWidget(api_card)

        display_card, display_inner = self._create_section_card("🖥️ 显示设置")

        self.top_check = QCheckBox("窗口置顶")
        self.top_check.setChecked(self.config.get("always_on_top", True))
        self.top_check.setStyleSheet(self._checkbox_style())
        display_inner.addWidget(self.top_check)

        self.auto_start_check = QCheckBox("开机自启动")
        self.auto_start_check.setChecked(self.config.get("auto_start", False))
        self.auto_start_check.setStyleSheet(self._checkbox_style())
        display_inner.addWidget(self.auto_start_check)

        size_layout = QHBoxLayout()
        size_layout.setSpacing(10)
        size_label = self._create_label("宠物大小:")
        size_label.setFixedWidth(70)
        size_layout.addWidget(size_label)

        current_size = self.config.get("pet_size", 300)
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(150, 400)
        self.size_slider.setValue(current_size)
        self.size_slider.setTickPosition(QSlider.TicksBelow)
        self.size_slider.setTickInterval(50)
        self.size_slider.setStyleSheet(f"""
            QSlider {{
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: {Theme.BORDER};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {Theme.ACCENT};
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: {Theme.ACCENT};
                border-radius: 3px;
            }}
        """)
        self.size_slider.valueChanged.connect(self._update_size_label)
        size_layout.addWidget(self.size_slider)

        self.size_value_label = QLabel(f"{current_size}px")
        self.size_value_label.setFixedWidth(50)
        self.size_value_label.setStyleSheet(f"color: {Theme.ACCENT}; font-size: {Theme.FONT_SIZE_MD}; font-weight: bold; background: transparent;")
        size_layout.addWidget(self.size_value_label)

        display_inner.addLayout(size_layout)

        self.user_avatar_path = self.config.get("user_avatar_path", "")
        avatar_row1 = QHBoxLayout()
        avatar_row1.setSpacing(10)
        avatar_label1 = self._create_label("你的头像:")
        avatar_label1.setFixedWidth(70)
        avatar_row1.addWidget(avatar_label1)

        self.user_avatar_preview = QLabel()
        self.user_avatar_preview.setFixedSize(40, 40)
        self._set_avatar_preview(self.user_avatar_preview, self.user_avatar_path, Theme.ACCENT, "你")
        avatar_row1.addWidget(self.user_avatar_preview)

        user_avatar_btn = QPushButton("选择图片")
        user_avatar_btn.setStyleSheet(self._small_btn_style())
        user_avatar_btn.clicked.connect(lambda: self._pick_avatar("user"))
        avatar_row1.addWidget(user_avatar_btn)

        clear_user_btn = QPushButton("清除")
        clear_user_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_MUTED};
                border: 1px solid {Theme.DANGER};
                border-radius: {Theme.RADIUS_SM};
                padding: 4px 10px;
                font-size: {Theme.FONT_SIZE_XS};
            }}
            QPushButton:hover {{
                background-color: {Theme.DANGER};
                color: #fff;
            }}
        """)
        clear_user_btn.clicked.connect(lambda: self._clear_avatar("user"))
        avatar_row1.addWidget(clear_user_btn)

        avatar_row1.addStretch()
        display_inner.addLayout(avatar_row1)

        self.pet_avatar_path = self.config.get("pet_avatar_path", "")
        avatar_row2 = QHBoxLayout()
        avatar_row2.setSpacing(10)
        avatar_label2 = self._create_label("小小耀头像:")
        avatar_label2.setFixedWidth(70)
        avatar_row2.addWidget(avatar_label2)

        self.pet_avatar_preview = QLabel()
        self.pet_avatar_preview.setFixedSize(40, 40)
        self._set_avatar_preview(self.pet_avatar_preview, self.pet_avatar_path, Theme.BG_SURFACE, "耀")
        avatar_row2.addWidget(self.pet_avatar_preview)

        pet_avatar_btn = QPushButton("选择图片")
        pet_avatar_btn.setStyleSheet(self._small_btn_style())
        pet_avatar_btn.clicked.connect(lambda: self._pick_avatar("pet"))
        avatar_row2.addWidget(pet_avatar_btn)

        clear_pet_btn = QPushButton("清除")
        clear_pet_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_MUTED};
                border: 1px solid {Theme.DANGER};
                border-radius: {Theme.RADIUS_SM};
                padding: 4px 10px;
                font-size: {Theme.FONT_SIZE_XS};
            }}
            QPushButton:hover {{
                background-color: {Theme.DANGER};
                color: #fff;
            }}
        """)
        clear_pet_btn.clicked.connect(lambda: self._clear_avatar("pet"))
        avatar_row2.addWidget(clear_pet_btn)

        avatar_row2.addStretch()
        display_inner.addLayout(avatar_row2)

        scroll_layout.addWidget(display_card)

        ai_card, ai_inner = self._create_section_card("🤖 AI 设置")

        self.mimic_check = QCheckBox("模仿你的说话风格")
        self.mimic_check.setChecked(self.config.get("mimic_mode", True))
        self.mimic_check.setToolTip("基于你的微信聊天记录，让AI模仿你的说话风格回复")
        self.mimic_check.setStyleSheet(self._checkbox_style())
        ai_inner.addWidget(self.mimic_check)

        scroll_layout.addWidget(ai_card)

        scroll_layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        save_btn = QPushButton("保存设置")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: #ffffff;
                border: none;
                border-radius: {Theme.RADIUS_MD};
                padding: 10px 0;
                font-size: {Theme.FONT_SIZE_LG};
                font-weight: bold;
                font-family: {Theme.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_HOVER};
            }}
        """)
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_MUTED};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_MD};
                padding: 10px 0;
                font-size: {Theme.FONT_SIZE_LG};
                font-family: {Theme.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        cancel_btn.clicked.connect(self._cancel_settings)
        btn_layout.addWidget(cancel_btn)

        scroll_layout.addLayout(btn_layout)

        scroll_area.setWidget(scroll_content)

        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.addWidget(scroll_area)

        main_layout.addWidget(body)

    def _create_section_card(self, title):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_XL};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel(title)
        header.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT};
                font-size: {Theme.FONT_SIZE_TITLE};
                font-weight: bold;
                font-family: {Theme.FONT_FAMILY};
                padding: 12px 14px 4px 14px;
                background: transparent;
            }}
        """)
        layout.addWidget(header)

        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {Theme.BORDER}; margin: 0 14px;")
        layout.addWidget(separator)

        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(14, 10, 14, 12)
        inner_layout.setSpacing(10)
        layout.addLayout(inner_layout)

        return card, inner_layout

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_MUTED};
                font-size: {Theme.FONT_SIZE_MD};
                font-family: {Theme.FONT_FAMILY};
                background: transparent;
            }}
        """)
        return label

    def _input_style(self):
        return f"""
            QLineEdit {{
                background-color: {Theme.INPUT_BG};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_MD};
                padding: 8px 12px;
                font-size: {Theme.FONT_SIZE_LG};
                font-family: {Theme.FONT_FAMILY};
            }}
            QLineEdit:focus {{
                border-color: {Theme.ACCENT};
            }}
        """

    def _checkbox_style(self):
        return f"""
            QCheckBox {{
                font-size: {Theme.FONT_SIZE_LG};
                font-family: {Theme.FONT_FAMILY};
                spacing: 10px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: {Theme.RADIUS_SM};
                border: 2px solid {Theme.BORDER};
                background-color: {Theme.INPUT_BG};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Theme.ACCENT};
                border-color: {Theme.ACCENT};
            }}
            QCheckBox::indicator:hover {{
                border-color: {Theme.ACCENT};
            }}
        """

    def _small_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_SM};
                padding: 4px 10px;
                font-size: {Theme.FONT_SIZE_XS};
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT};
                border-color: {Theme.ACCENT};
            }}
        """

    def _set_avatar_preview(self, label, path, fallback_color, text):
        from theme import Theme as T
        if path and os.path.exists(path):
            pixmap = T.create_circular_pixmap(path, 40)
            if pixmap and not pixmap.isNull():
                label.setPixmap(pixmap)
                return
        label.setText(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            QLabel {{
                background-color: {fallback_color};
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                border-radius: 20px;
                font-family: {Theme.FONT_FAMILY};
            }}
        """)

    def _pick_avatar(self, which):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择头像图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if path:
            if which == "user":
                self.user_avatar_path = path
                self._set_avatar_preview(self.user_avatar_preview, path, Theme.ACCENT, "你")
            else:
                self.pet_avatar_path = path
                self._set_avatar_preview(self.pet_avatar_preview, path, Theme.BG_SURFACE, "耀")

    def _clear_avatar(self, which):
        if which == "user":
            self.user_avatar_path = ""
            self._set_avatar_preview(self.user_avatar_preview, "", Theme.ACCENT, "你")
        else:
            self.pet_avatar_path = ""
            self._set_avatar_preview(self.pet_avatar_preview, "", Theme.BG_SURFACE, "耀")

    def _update_size_label(self, value):
        self.size_value_label.setText(f"{value}px")

    def save_settings(self):
        api_key = self.api_key_input.text().strip()
        model = self.model_input.text().strip() or "deepseek-v4-flash"

        self.config["api_key"] = api_key
        self.config["model_name"] = model
        self.config["always_on_top"] = self.top_check.isChecked()
        self.config["auto_start"] = self.auto_start_check.isChecked()
        self.config["mimic_mode"] = self.mimic_check.isChecked()
        self.config["pet_size"] = self.size_slider.value()
        self.config["user_avatar_path"] = self.user_avatar_path
        self.config["pet_avatar_path"] = self.pet_avatar_path

        try:
            set_auto_start(self.auto_start_check.isChecked())
        except Exception:
            pass

        self.pet_window.save_config()

        try:
            self.pet_window.apply_config()
        except Exception:
            pass

        QMessageBox.information(self, "保存成功", "设置已保存！")
        self.close()

    def _cancel_settings(self):
        self.close()