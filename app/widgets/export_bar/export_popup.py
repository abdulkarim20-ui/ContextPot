from typing import List
from PySide6.QtCore import QEvent, QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)
from app.config.theme import (
    BG_PRIMARY,
    BORDER_LIGHT,
    FS_LABEL,
    FW_BOLD,
    SP_1,
    SP_2,
    TEXT_DIM,
)
from app.widgets.export_bar.export_option_card import ExportOptionCard

EXPORT_MODES = [
    {
        "id": "Whole code + Tree",
        "title": "Whole code + Tree",
        "icon": "file_code"
    },
    {
        "id": "Tree Only",
        "title": "Tree Only",
        "icon": "binary-tree"
    }
]

class ExportModePopup(QFrame):
    """
    Floating Export Mode selection popup card.
    Contains 'EXPORT MODE' eyebrow header and compact option cards.
    """
    mode_selected = Signal(str)
    closed = Signal()

    def __init__(self, current_mode: str = "Whole code + Tree", parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setObjectName("ExportModePopup")
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self.current_mode = current_mode
        self._cards: List[ExportOptionCard] = []

        self.setStyleSheet(f"""
            QFrame#ExportModePopup {{
                background-color: {BG_PRIMARY};
                border: 1px solid {BORDER_LIGHT};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        # 1. Header Label (EXPORT MODE)
        self.header_lbl = QLabel("EXPORT MODE", self)
        self.header_lbl.setStyleSheet(f"""
            color: {TEXT_DIM};
            font-size: {FS_LABEL}px;
            font-weight: {FW_BOLD};
            letter-spacing: 0.8px;
            padding-left: 8px;
            padding-top: 2px;
            padding-bottom: 2px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.header_lbl)

        # 2. Options
        for mode in EXPORT_MODES:
            card = ExportOptionCard(
                mode_id=mode["id"],
                title=mode["title"],
                subtitle="",
                icon_name=mode["icon"],
                is_selected=(mode["id"] == self.current_mode),
                parent=self
            )
            card.clicked.connect(self._on_option_clicked)
            self._cards.append(card)
            layout.addWidget(card)

    def set_current_mode(self, mode_id: str):
        self.current_mode = mode_id
        for card in self._cards:
            card.set_selected(card.mode_id == mode_id)

    def _on_option_clicked(self, mode_id: str):
        self.set_current_mode(mode_id)
        self.mode_selected.emit(mode_id)
        self.close()

    def show_above_widget(self, target_widget):
        """Position the popup smoothly above the target widget."""
        target_geo = target_widget.rect()
        global_pos = target_widget.mapToGlobal(QPoint(0, 0))

        # Size the popup to align cleanly with the dropdown pill button
        self.adjustSize()
        popup_width = max(target_widget.width(), 200)
        popup_height = self.sizeHint().height()
        self.setFixedSize(popup_width, popup_height)

        # Calculate position: above the pill button with 6px gap
        popup_x = global_pos.x()
        popup_y = global_pos.y() - popup_height - 6

        self.move(popup_x, popup_y)
        self.show()

    def hideEvent(self, event):
        self.closed.emit()
        super().hideEvent(event)
