from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)
from app.config.theme import (
    ACCENT,
    BG_SECONDARY,
    FS_BODY_L,
    FS_BODY_M,
    FW_REGULAR,
    FW_SEMIBOLD,
    PRIMARY,
    PRIMARY_LIGHT,
    TEXT_MUTED,
    TEXT_PRIMARY,
)
from app.core.icons import load_icon, render_pixmap

class ExportOptionCard(QFrame):
    """
    Rich interactive option item inside the Export Mode popup menu.
    Displays:
    - Left icon (file_code or tree_branch)
    - Center text: Title + Subtitle
    - Right icon: Checkmark (when selected)
    """
    clicked = Signal(str)

    def __init__(
        self,
        mode_id: str,
        title: str,
        subtitle: str = "",
        icon_name: str = "",
        is_selected: bool = False,
        parent=None
    ):
        super().__init__(parent)
        self.mode_id = mode_id
        self.title_text = title
        self.subtitle_text = subtitle
        self.icon_name = icon_name
        self._is_selected = is_selected
        self._is_hovered = False

        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(9)
        layout.setAlignment(Qt.AlignVCenter)

        # 1. Left Icon
        self.icon_lbl = QLabel(self)
        self.icon_lbl.setFixedSize(18, 18)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.icon_lbl)

        # 2. Option Title
        self.title_lbl = QLabel(self.title_text, self)
        self.title_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.title_lbl, 1)

        # 3. Right Checkmark
        self.check_lbl = QLabel(self)
        self.check_lbl.setFixedSize(16, 16)
        self.check_lbl.setAlignment(Qt.AlignCenter)
        self.check_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.check_lbl)

        self._update_style()

    def set_selected(self, selected: bool):
        self._is_selected = selected
        self._update_style()

    def _update_style(self):
        if self._is_selected:
            # Active selected styling (Soft blue pill with vibrant blue text and checkmark)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {PRIMARY_LIGHT};
                    border: none;
                    border-radius: 7px;
                }}
            """)
            icon_color = PRIMARY

            # Title: Body-M with semibold
            self.title_lbl.setStyleSheet(f"""
                color: {PRIMARY};
                font-size: {FS_BODY_M}px;
                font-weight: {FW_SEMIBOLD};
                background: transparent;
                border: none;
            """)

            chk_icon = load_icon("check", (13, 13), color=PRIMARY)
            if chk_icon:
                self.check_lbl.setPixmap(chk_icon.pixmap(QSize(13, 13)))
            self.check_lbl.show()
        else:
            # Unselected styling
            bg = BG_SECONDARY if self._is_hovered else "transparent"
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg};
                    border: none;
                    border-radius: 7px;
                }}
            """)
            icon_color = TEXT_MUTED

            # Title: Body-M with semibold
            self.title_lbl.setStyleSheet(f"""
                color: {TEXT_PRIMARY};
                font-size: {FS_BODY_M}px;
                font-weight: {FW_SEMIBOLD};
                background: transparent;
                border: none;
            """)
            self.check_lbl.clear()
            self.check_lbl.hide()

        # Update left icon with proper color
        ic = load_icon(self.icon_name, (18, 18), color=icon_color)
        if ic:
            self.icon_lbl.setPixmap(ic.pixmap(QSize(18, 18)))

    def enterEvent(self, event):
        self._is_hovered = True
        self._update_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self._update_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.mode_id)
        super().mousePressEvent(event)
