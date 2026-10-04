import os
from typing import Optional
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFontMetrics
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from app.config.theme import ACCENT, ACCENT_HOVER, BORDER, TEXT_MAIN, TEXT_MUTED
from app.core.icons import load_icon

class SmartDestinationDialog(QDialog):
    """
    Modern modal dialog prompting to save a 3-time consecutive export directory as default.
    """
    def __init__(self, target_path: str, project_name: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.target_path = target_path
        self.project_name = project_name
        self.remember = False

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedWidth(330)

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)

        # Main Card container
        card = QFrame(self)
        card.setObjectName("SmartCard")
        card.setStyleSheet(f"""
            QFrame#SmartCard {{
                background-color: #ffffff;
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header: Icon + Title
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        icon_lbl = QLabel(card)
        icon_lbl.setFixedSize(18, 18)
        dest_ic = load_icon("folder", (16, 16), color=ACCENT)
        if dest_ic:
            icon_lbl.setPixmap(dest_ic.pixmap(QSize(16, 16)))
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        header.addWidget(icon_lbl)

        title = QLabel("Smart Destination", card)
        title.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 700;
            color: {TEXT_MAIN};
            background: transparent;
            border: none;
        """)
        header.addWidget(title)
        header.addStretch(1)
        layout.addLayout(header)

        # Description
        proj_str = f" for <b>{self.project_name}</b>" if self.project_name else ""
        msg = QLabel(
            f"You've exported to this location <b>3 times in a row</b>.{proj_str}<br>"
            "Set this as your <b>default export location</b>?",
            card
        )
        msg.setWordWrap(True)
        msg.setStyleSheet(f"""
            font-size: 12px;
            color: {TEXT_MAIN};
            line-height: 1.4;
            background: transparent;
            border: none;
        """)
        layout.addWidget(msg)

        # Path Badge Box
        path_box = QFrame(card)
        path_box.setStyleSheet(f"""
            background-color: #f8fafc;
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 4px 6px;
        """)
        path_layout = QHBoxLayout(path_box)
        path_layout.setContentsMargins(4, 2, 4, 2)
        
        # Elide long path if necessary
        fm = QFontMetrics(self.font())
        display_path = fm.elidedText(self.target_path, Qt.ElideMiddle, 260)
        
        path_lbl = QLabel(display_path, path_box)
        path_lbl.setToolTip(self.target_path)
        path_lbl.setStyleSheet(f"""
            color: {TEXT_MUTED};
            font-size: 11px;
            font-family: monospace;
            background: transparent;
            border: none;
        """)
        path_layout.addWidget(path_lbl)
        layout.addWidget(path_box)

        layout.addSpacing(4)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        btn_no = QPushButton("Not now", card)
        btn_no.setCursor(Qt.PointingHandCursor)
        btn_no.setFixedHeight(28)
        btn_no.setStyleSheet(f"""
            QPushButton {{
                background-color: #f1f5f9;
                color: {TEXT_MUTED};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: #e2e8f0;
                color: {TEXT_MAIN};
            }}
        """)
        btn_no.clicked.connect(self.reject)

        btn_yes = QPushButton("Set Default", card)
        btn_yes.setCursor(Qt.PointingHandCursor)
        btn_yes.setFixedHeight(28)
        btn_yes.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
            }}
        """)
        btn_yes.clicked.connect(self.on_yes)

        btn_layout.addStretch(1)
        btn_layout.addWidget(btn_no)
        btn_layout.addWidget(btn_yes)

        layout.addLayout(btn_layout)
        root.addWidget(card)

    def on_yes(self):
        self.remember = True
        self.accept()
