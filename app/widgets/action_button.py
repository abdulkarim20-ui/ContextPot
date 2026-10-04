from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from app.config.theme import (
    BG_TERTIARY,
    FONT_PRIMARY,
    FS_BODY_L,
    FW_SEMIBOLD,
    PRIMARY,
    PRIMARY_HOVER,
    TEXT_MUTED,
)

class PrimaryActionButton(QPushButton):
    """
    Bottom full-width primary action button ('Start Scan')
    with distinct soft disabled state and enabled brand state.
    """
    def __init__(self, text: str = "Start Scan", parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(40)
        self._is_active = False
        self.set_active(False)

    def set_active(self, active: bool):
        self._is_active = active
        self.setEnabled(active)

        if active:
            self.setCursor(Qt.PointingHandCursor)
            self.setStyleSheet(f"""
                QPushButton {{
                    font-family: "{FONT_PRIMARY}";
                    background-color: {PRIMARY};
                    color: #ffffff;
                    font-size: {FS_BODY_L}px;
                    font-weight: {FW_SEMIBOLD};
                    border: none;
                    border-radius: 9px;
                }}
                QPushButton:hover {{
                    background-color: {PRIMARY_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: #1e40af;
                }}
            """)
        else:
            self.setCursor(Qt.ArrowCursor)
            self.setStyleSheet(f"""
                QPushButton {{
                    font-family: "{FONT_PRIMARY}";
                    background-color: {BG_TERTIARY};
                    color: {TEXT_MUTED};
                    font-size: {FS_BODY_L}px;
                    font-weight: {FW_SEMIBOLD};
                    border: none;
                    border-radius: 9px;
                }}
            """)
