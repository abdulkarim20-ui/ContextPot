import time
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
)
from app.config.theme import BORDER, TEXT_MAIN, TEXT_MUTED
from app.core.icons import load_icon
from app.widgets.export_bar.export_popup import ExportModePopup

class ExportDropdownPill(QFrame):
    """
    Rounded dropdown trigger pill matching the exact design:
    - Left icon representing active mode
    - Mode name label
    - Animated rotating chevron arrow
    - Active dark border (1.5px solid #0f172a) when popup is open
    - Clean toggle: click once to open, click again to close
    """
    mode_changed = Signal(str)

    def __init__(self, default_mode: str = "Whole code + Tree", parent=None):
        super().__init__(parent)
        self.setObjectName("ExportDropdownPill")
        self.setFixedHeight(32)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

        self._current_mode = default_mode
        self._is_open = False
        self._is_hovered = False
        self._last_close_time = 0.0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(7)
        layout.setAlignment(Qt.AlignVCenter)

        # 1. Left Mode Icon
        self.mode_icon_lbl = QLabel(self)
        self.mode_icon_lbl.setFixedSize(16, 16)
        self.mode_icon_lbl.setAlignment(Qt.AlignCenter)
        self.mode_icon_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.mode_icon_lbl)

        # 2. Mode Title Label
        self.mode_title_lbl = QLabel(self._current_mode, self)
        self.mode_title_lbl.setStyleSheet(f"""
            color: {TEXT_MAIN};
            font-size: 12px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.mode_title_lbl)

        layout.addStretch(1)

        # 3. Right Chevron Arrow
        self.chevron_lbl = QLabel(self)
        self.chevron_lbl.setFixedSize(14, 14)
        self.chevron_lbl.setAlignment(Qt.AlignCenter)
        self.chevron_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.chevron_lbl)

        # Popup card
        self._popup = ExportModePopup(current_mode=self._current_mode, parent=self)
        self._popup.mode_selected.connect(self._on_mode_selected)
        self._popup.closed.connect(self._on_popup_closed)

        self._update_appearance()

    def get_mode(self) -> str:
        return self._current_mode

    def set_mode(self, mode: str):
        self._current_mode = mode
        self.mode_title_lbl.setText(mode)
        self._popup.set_current_mode(mode)
        self._update_appearance()
        self.mode_changed.emit(mode)

    def _on_mode_selected(self, mode: str):
        self.set_mode(mode)
        self._is_open = False
        self._update_appearance()

    def _on_popup_closed(self):
        self._last_close_time = time.time()
        self._is_open = False
        self._update_appearance()

    def _update_appearance(self):
        # 1. Border and background
        if self._is_open:
            # Active open state: Dark stroke border #0f172a
            self.setStyleSheet("""
                QFrame#ExportDropdownPill {
                    background-color: #ffffff;
                    border: 1.5px solid #0f172a;
                    border-radius: 16px;
                }
            """)
        elif self._is_hovered:
            self.setStyleSheet("""
                QFrame#ExportDropdownPill {
                    background-color: #f8fafc;
                    border: 1px solid #cbd5e1;
                    border-radius: 16px;
                }
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#ExportDropdownPill {{
                    background-color: #ffffff;
                    border: 1px solid {BORDER};
                    border-radius: 16px;
                }}
            """)

        # 2. Left icon
        icon_name = "file_code" if "code" in self._current_mode.lower() else "binary-tree"
        mode_ic = load_icon(icon_name, (14, 14), color="#64748b")
        if mode_ic:
            self.mode_icon_lbl.setPixmap(mode_ic.pixmap(QSize(14, 14)))

        # 3. Chevron arrow
        chev_name = "chevron-up" if self._is_open else "chevron-down"
        chev_ic = load_icon(chev_name, (12, 12), color="#64748b")
        if chev_ic:
            self.chevron_lbl.setPixmap(chev_ic.pixmap(QSize(12, 12)))

    def enterEvent(self, event):
        self._is_hovered = True
        self._update_appearance()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self._update_appearance()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            now = time.time()
            if now - self._last_close_time < 0.25:
                # Pill click just caused the popup to dismiss, keep it closed
                event.accept()
                return

            if self._is_open:
                self._popup.close()
                self._is_open = False
            else:
                self._is_open = True
                self._popup.show_above_widget(self)
            self._update_appearance()
        super().mousePressEvent(event)

