from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from app.config.theme import BORDER, FONT_MONO, TEXT_MAIN, TEXT_MUTED
from app.core.icons import load_icon

class TagChip(QFrame):
    """
    Monospace pattern tag chip with a subtle remove (✕) button.
    e.g. 'env ✕', '*.log ✕'
    """
    removed = Signal(str)

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.text = text
        self.setObjectName("TagChip")
        self.setFixedHeight(26)
        self.setStyleSheet(f"""
            QFrame#TagChip {{
                background-color: #f1f5f9;
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
            QFrame#TagChip:hover {{
                background-color: #e2e8f0;
                border-color: #cbd5e1;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 6, 2)
        layout.setSpacing(6)

        # Tag Label
        self.label = QLabel(text)
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_MAIN};
                font-family: {FONT_MONO};
                font-size: 11px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self.label)

        # Remove 'x' Button
        self.del_btn = QPushButton()
        self.del_btn.setFixedSize(14, 14)
        self.del_btn.setCursor(Qt.PointingHandCursor)
        x_icon = load_icon("x", (10, 10), color=TEXT_MUTED)
        if x_icon:
            self.del_btn.setIcon(x_icon)
        self.del_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {{
                background: rgba(0, 0, 0, 0.08);
            }}
        """)
        self.del_btn.clicked.connect(lambda: self.removed.emit(self.text))
        layout.addWidget(self.del_btn)
