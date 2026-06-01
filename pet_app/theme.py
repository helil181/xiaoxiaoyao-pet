from PySide6.QtGui import QFont, QPixmap, QPainter, QBitmap, Qt


class Theme:
    BG_PRIMARY = "#1a1a2e"
    BG_SECONDARY = "#16213e"
    BG_SURFACE = "#0f3460"
    BG_CARD = "#1e2a4a"
    ACCENT = "#e94560"
    ACCENT_HOVER = "#ff6b81"
    ACCENT_DISABLED = "#555555"
    USER_BUBBLE = "#e94560"
    AI_BUBBLE = "#1e2a4a"
    AI_BUBBLE_BORDER = "#0f3460"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#eaeaea"
    TEXT_MUTED = "#8899aa"
    TEXT_DIM = "#666888"
    BORDER = "#2a3a5a"
    BORDER_LIGHT = "#3a4a6a"
    INPUT_BG = "#1e2a4a"
    DANGER = "#c0392b"
    DANGER_HOVER = "#e74c3c"
    SCROLLBAR_BG = "transparent"
    SCROLLBAR_HANDLE = "#3a4a6a"
    SUCCESS = "#27ae60"
    TITLE_BAR_BG = "#12122a"
    TITLE_BAR_BTN_HOVER = "#2a2a4a"
    TITLE_BAR_CLOSE_HOVER = "#e94560"
    OVERLAY_BG = "rgba(0, 0, 0, 0.5)"
    AVATAR_SIZE = 32

    FONT_FAMILY = '"Microsoft YaHei", "PingFang SC", "Segoe UI", Arial, sans-serif'
    FONT_SIZE_XS = "11px"
    FONT_SIZE_SM = "12px"
    FONT_SIZE_MD = "13px"
    FONT_SIZE_LG = "14px"
    FONT_SIZE_XL = "15px"
    FONT_SIZE_TITLE = "16px"

    RADIUS_SM = "4px"
    RADIUS_MD = "6px"
    RADIUS_LG = "8px"
    RADIUS_XL = "12px"
    RADIUS_XXL = "16px"

    SPACING_XS = 2
    SPACING_SM = 4
    SPACING_MD = 8
    SPACING_LG = 12
    SPACING_XL = 16
    SPACING_XXL = 24

    @classmethod
    def create_circular_pixmap(cls, image_path, size=None):
        if not image_path:
            return None
        size = size or cls.AVATAR_SIZE
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return None
        pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        mask = QBitmap(size, size)
        mask.fill(Qt.color0)
        painter = QPainter(mask)
        painter.setBrush(Qt.color1)
        painter.setPen(Qt.color1)
        painter.drawEllipse(0, 0, size, size)
        painter.end()
        pixmap.setMask(mask)
        return pixmap

    @classmethod
    def font_style(cls, size=None, weight="normal", color=None):
        parts = [f"font-family: {cls.FONT_FAMILY}"]
        if size:
            parts.append(f"font-size: {size}")
        if weight:
            parts.append(f"font-weight: {weight}")
        if color:
            parts.append(f"color: {color}")
        return "; ".join(parts)

    @classmethod
    def scrollbar_style(cls, bg=None, handle=None, radius=None):
        bg = bg or cls.SCROLLBAR_BG
        handle = handle or cls.SCROLLBAR_HANDLE
        radius = radius or cls.RADIUS_SM
        return f"""
            QScrollBar:vertical {{
                background: {bg};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {handle};
                border-radius: {radius};
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background: {bg};
                height: 8px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background: {handle};
                border-radius: {radius};
                min-width: 30px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
        """