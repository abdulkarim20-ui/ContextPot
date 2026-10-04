from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget
from app.config.theme import (
    TEXT_MAIN,
    TEXT_MUTED,
    TITLEBAR_BORDER,
    TITLEBAR_GRADIENT_QSS,
)
from app.core.icons import load_icon
from app.core.tooltip import attach_tooltip

class HeaderToolBar(QWidget):
    """
    Header toolbar placed below the native title bar,
    containing forward/backward navigation buttons on the left
    and the settings gear button on the right with a clean transparent background.
    """
    settings_clicked = Signal()
    back_clicked = Signal()
    forward_clicked = Signal()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 1. Back Navigation Button (arrow-left)
        self.back_btn = QPushButton(self)
        self.back_btn.setFixedSize(24, 24)
        self._setup_nav_button(self.back_btn, "arrow-left", "Back")
        self.back_btn.clicked.connect(self.back_clicked.emit)
        self.set_back_enabled(False)
        layout.addWidget(self.back_btn)

        # 2. Forward Navigation Button (arrow-right)
        self.forward_btn = QPushButton(self)
        self.forward_btn.setFixedSize(24, 24)
        self._setup_nav_button(self.forward_btn, "arrow-right", "Forward to Explorer")
        self.forward_btn.clicked.connect(self.forward_clicked.emit)
        self.set_forward_enabled(False)
        layout.addWidget(self.forward_btn)

        layout.addStretch(1)

        # 3. Settings Button (Gear)
        self.settings_btn = QPushButton(self)
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        settings_icon = load_icon("settings", (16, 16), color=TEXT_MUTED)
        if settings_icon:
            self.settings_btn.setIcon(settings_icon)
            self.settings_btn.setIconSize(QSize(16, 16))
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #f1f5f9;
            }
            QPushButton:pressed {
                background: #e2e8f0;
            }
        """)
        attach_tooltip(self.settings_btn, "Settings")
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.settings_btn)

    def _setup_nav_button(self, btn: QPushButton, icon_name: str, tooltip_text: str):
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover:!disabled {
                background: #f1f5f9;
            }
            QPushButton:pressed:!disabled {
                background: #e2e8f0;
            }
            QPushButton:disabled {
                background: transparent;
            }
        """)
        attach_tooltip(btn, tooltip_text)

    def set_back_enabled(self, enabled: bool):
        self.back_btn.setEnabled(enabled)
        self.back_btn.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        color = TEXT_MAIN if enabled else "#cbd5e1"
        icon = load_icon("arrow-left", (14, 14), color=color)
        if icon:
            self.back_btn.setIcon(icon)
            self.back_btn.setIconSize(QSize(14, 14))

    def set_forward_enabled(self, enabled: bool):
        self.forward_btn.setEnabled(enabled)
        self.forward_btn.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        color = TEXT_MAIN if enabled else "#cbd5e1"
        icon = load_icon("arrow-right", (14, 14), color=color)
        if icon:
            self.forward_btn.setIcon(icon)
            self.forward_btn.setIconSize(QSize(14, 14))

# Backwards compatibility alias
WindowTitleBar = HeaderToolBar
