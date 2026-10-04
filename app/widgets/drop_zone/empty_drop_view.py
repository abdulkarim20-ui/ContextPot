from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from app.config.theme import (
    BORDER_LIGHT,
    FONT_PRIMARY,
    FS_BODY_L,
    FS_BODY_M,
    FS_CAPTION,
    FW_MEDIUM,
    FW_SEMIBOLD,
    PRIMARY,
    PRIMARY_HOVER,
    TEXT_MUTED,
    TEXT_PRIMARY,
)
from app.core.icons import load_icon
from app.core.tooltip import attach_tooltip
from app.widgets.drop_zone.folder_icon_box import ZoomableFolderIconBox

class EmptyDropView(QWidget):
    """Initial empty dropzone view with icon box, title, divider, and browse button."""
    select_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 4)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        # 1. Folder Drop Icon in Box with Smooth Zoom
        self.icon_box = ZoomableFolderIconBox(self)
        icon_container = QWidget()
        icon_container.setStyleSheet("background: transparent;")
        ic_lay = QHBoxLayout(icon_container)
        ic_lay.setContentsMargins(0, 0, 0, 0)
        ic_lay.setAlignment(Qt.AlignCenter)
        ic_lay.addWidget(self.icon_box)
        layout.addWidget(icon_container)

        # 2. Main Title Text
        self.title_lbl = QLabel("Drop a repository or project folder\nhere to get started.")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setStyleSheet(f"""
            background: transparent;
            border: none;
            color: {TEXT_PRIMARY};
            font-family: "{FONT_PRIMARY}";
            font-size: {FS_BODY_L}px;
            font-weight: {FW_SEMIBOLD};
            line-height: 20px;
        """)
        layout.addWidget(self.title_lbl)

        # 3. 'or' Divider
        divider_widget = QWidget()
        divider_widget.setStyleSheet("background: transparent;")
        div_lay = QHBoxLayout(divider_widget)
        div_lay.setContentsMargins(18, 0, 18, 0)
        div_lay.setSpacing(10)

        line_left = QFrame()
        line_left.setFrameShape(QFrame.HLine)
        line_left.setStyleSheet(f"background-color: {BORDER_LIGHT}; border: none; max-height: 1px;")
        div_lay.addWidget(line_left, 1)

        or_lbl = QLabel("or")
        or_lbl.setStyleSheet(f"""
            background: transparent;
            border: none;
            color: {TEXT_MUTED};
            font-family: "{FONT_PRIMARY}";
            font-size: {FS_CAPTION}px;
            font-weight: {FW_MEDIUM};
        """)
        or_lbl.setAlignment(Qt.AlignCenter)
        div_lay.addWidget(or_lbl)

        line_right = QFrame()
        line_right.setFrameShape(QFrame.HLine)
        line_right.setStyleSheet(f"background-color: {BORDER_LIGHT}; border: none; max-height: 1px;")
        div_lay.addWidget(line_right, 1)

        layout.addWidget(divider_widget)

        # 4. 'Select folder' Button
        self.select_btn = QPushButton("Select folder")
        self.select_btn.setCursor(Qt.PointingHandCursor)
        self.select_btn.setFixedSize(136, 32)
        self.select_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY};
                color: #ffffff;
                font-family: "{FONT_PRIMARY}";
                font-size: {FS_BODY_M}px;
                font-weight: {FW_SEMIBOLD};
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #1e40af;
            }}
        """)
        attach_tooltip(self.select_btn, "Browse folder on computer")
        self.select_btn.clicked.connect(self.select_clicked.emit)

        btn_container = QWidget()
        btn_container.setStyleSheet("background: transparent;")
        btn_lay = QHBoxLayout(btn_container)
        btn_lay.setContentsMargins(0, 0, 0, 0)
        btn_lay.setAlignment(Qt.AlignCenter)
        btn_lay.addWidget(self.select_btn)
        layout.addWidget(btn_container)

    def set_hovered(self, hovered: bool):
        self.icon_box.set_hovered(hovered)
