from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from app.config.theme import (
    BG_MAIN,
    TEXT_MAIN,
    TEXT_MUTED,
    TITLEBAR_BORDER,
    TITLEBAR_GRADIENT_QSS,
)
from app.core.icons import load_icon
from app.core.tooltip import attach_tooltip
from app.views.settings.about_card import AboutCard
from app.views.settings.ignore_patterns_card import IgnorePatternsCard
from app.views.settings.preferences_card import PreferencesCard

class SettingsView(QWidget):
    """
    Full Settings View with Back Header navigation, Ignore Patterns card,
    Preferences card, and About collapsible card with slim scrollbars (Light Mode).
    """
    back_clicked = Signal()
    always_on_top_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG_MAIN};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # 1. Top Header Bar (Back Button + Title)
        header_bar = QWidget()
        header_bar.setFixedHeight(26)
        header_bar.setStyleSheet("background: transparent; border: none;")
        h_lay = QHBoxLayout(header_bar)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(8)

        # Back Arrow Button
        self.back_btn = QPushButton()
        self.back_btn.setFixedSize(24, 24)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        back_icon = load_icon("arrow-left", (14, 14), color=TEXT_MAIN)
        if back_icon:
            self.back_btn.setIcon(back_icon)
            self.back_btn.setIconSize(QSize(14, 14))
        self.back_btn.setStyleSheet("""
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
        attach_tooltip(self.back_btn, "Back to Launcher")
        self.back_btn.clicked.connect(self._on_back_clicked)
        h_lay.addWidget(self.back_btn)

        # Settings Title
        self.title_lbl = QLabel("Settings")
        self.title_lbl.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 13px; font-weight: 700; background: transparent; border: none; padding-left: 2px;")
        h_lay.addWidget(self.title_lbl)
        h_lay.addStretch(1)

        main_layout.addWidget(header_bar)

        # 2. Main Scroll Area for Settings Content Cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 4px;
                margin: 0px 1px 0px 0px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                min-height: 20px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        def _create_section_header(title: str) -> QLabel:
            lbl = QLabel(title)
            lbl.setStyleSheet(f"""
                color: {TEXT_MUTED};
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.8px;
                background: transparent;
                border: none;
                padding-left: 2px;
                padding-top: 2px;
            """)
            return lbl

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        c_lay = QVBoxLayout(container)
        c_lay.setContentsMargins(0, 0, 4, 10)
        c_lay.setSpacing(6)

        # Card 1: Ignore Patterns
        self.ignore_card = IgnorePatternsCard(parent=self)
        c_lay.addWidget(self.ignore_card)

        c_lay.addSpacing(4)

        # Section 2: Preferences
        c_lay.addWidget(_create_section_header("PREFERENCES"))
        self.prefs_card = PreferencesCard(parent=self)
        self.prefs_card.always_on_top_changed.connect(self.always_on_top_toggled.emit)
        c_lay.addWidget(self.prefs_card)

        c_lay.addSpacing(4)

        # Section 3: About
        c_lay.addWidget(_create_section_header("ABOUT"))
        self.about_card = AboutCard(parent=self)
        c_lay.addWidget(self.about_card)

        c_lay.addStretch(1)

        self.scroll_area.setWidget(container)
        main_layout.addWidget(self.scroll_area, 1)

    def _on_back_clicked(self):
        self.reset_search()
        self.back_clicked.emit()

    def reset_search(self):
        """Clean up search input when user leaves settings view."""
        self.ignore_card.reset_search()

    def hideEvent(self, event):
        self.reset_search()
        super().hideEvent(event)



