import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from app.config.theme import ACCENT, ACCENT_HOVER, BORDER, TEXT_MAIN, TEXT_MUTED
from app.core.fonts import FONT_UI_FAMILY, make_font
from app.core.icons import load_icon
from app.core.smart_destination_manager import get_smart_destination_manager
from app.core.settings_manager import SettingsManager
from app.widgets.toggle_switch import ToggleSwitch

class PreferenceRow(QWidget):
    """A single settings preference row with title, description, and toggle switch."""
    toggled = Signal(bool)

    def __init__(self, title: str, description: str, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        # Text Column
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(2)

        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(make_font(FONT_UI_FAMILY, 13, QFont.Weight.DemiBold))
        self.title_lbl.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        col.addWidget(self.title_lbl)

        self.desc_lbl = QLabel(description)
        self.desc_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 400; background: transparent; border: none;")
        self.desc_lbl.setWordWrap(True)
        col.addWidget(self.desc_lbl)

        layout.addLayout(col, 1)

        # Toggle Switch
        self.toggle = ToggleSwitch(checked=checked, parent=self)
        self.toggle.toggled.connect(self.toggled.emit)
        layout.addWidget(self.toggle)

    def setChecked(self, checked: bool):
        self.toggle.setChecked(checked)

    def isChecked(self) -> bool:
        return self.toggle.isChecked()


class PreferencesCard(QFrame):
    """
    Card 2: Preferences card with 'Always on Top', 'Show Export Notification',
    'Smart Destination Selection', and 'Global Fixed Destination' (Light Mode).
    """
    always_on_top_changed = Signal(bool)
    export_notify_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PrefsCard")
        self.setStyleSheet(f"""
            QFrame#PrefsCard {{
                background-color: #ffffff;
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)

        self.smart_mgr = get_smart_destination_manager()
        self.settings = SettingsManager()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # 1. Always on Top
        self.row_top = PreferenceRow(
            title="Always on Top",
            description="Keep ContextPot above other application windows",
            checked=False,
            parent=self
        )
        self.row_top.toggled.connect(self.always_on_top_changed.emit)
        layout.addWidget(self.row_top)

        layout.addWidget(self._create_separator())

        # 2. Show Export Notification
        self.row_export = PreferenceRow(
            title="Show Export Notification",
            description="Display feedback alert when files are exported",
            checked=True,
            parent=self
        )
        self.row_export.toggled.connect(self.export_notify_changed.emit)
        layout.addWidget(self.row_export)

        layout.addWidget(self._create_separator())

        # 4. Smart Destination Selection
        self.row_smart = PreferenceRow(
            title="Smart Destination",
            description="Remember default destination folder per project after 3 exports",
            checked=self.smart_mgr.is_smart_enabled(),
            parent=self
        )
        self.row_smart.toggled.connect(self._on_smart_toggled)
        layout.addWidget(self.row_smart)

        layout.addWidget(self._create_separator())

        # 5. Global Fixed Destination (Advanced Option)
        self.row_global_fixed = PreferenceRow(
            title="Export all to single location",
            description="Always export files directly to one specific destination folder",
            checked=self.smart_mgr.is_global_fixed_enabled(),
            parent=self
        )
        self.row_global_fixed.toggled.connect(self._on_global_fixed_toggled)
        layout.addWidget(self.row_global_fixed)

        # Path input container for Global Fixed Destination
        self.path_container = QWidget(self)
        self.path_container.setStyleSheet("background: transparent;")
        path_layout = QHBoxLayout(self.path_container)
        path_layout.setContentsMargins(0, 2, 0, 4)
        path_layout.setSpacing(6)

        self.path_input = QLineEdit(self.path_container)
        self.path_input.setPlaceholderText("Select or enter export directory...")
        self.path_input.setText(self.smart_mgr.get_global_fixed_path())
        self.path_input.setFixedHeight(28)
        self.path_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #f8fafc;
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 0px 8px;
                font-size: 11px;
                color: {TEXT_MAIN};
            }}
            QLineEdit:focus {{
                border-color: {ACCENT};
                background-color: #ffffff;
            }}
        """)
        self.path_input.textChanged.connect(self._on_path_text_changed)
        path_layout.addWidget(self.path_input, 1)

        self.btn_browse = QPushButton("Browse", self.path_container)
        self.btn_browse.setFixedHeight(28)
        self.btn_browse.setCursor(Qt.PointingHandCursor)
        self.btn_browse.setStyleSheet(f"""
            QPushButton {{
                background-color: #f1f5f9;
                border: 1px solid {BORDER};
                border-radius: 6px;
                color: {TEXT_MAIN};
                font-size: 11px;
                font-weight: 600;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background-color: #e2e8f0;
            }}
        """)
        self.btn_browse.clicked.connect(self._on_browse_clicked)
        path_layout.addWidget(self.btn_browse)

        layout.addWidget(self.path_container)
        self.path_container.setVisible(self.smart_mgr.is_global_fixed_enabled())

    def _create_separator(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {BORDER}; border: none; max-height: 1px;")
        return sep

    def _on_smart_toggled(self, checked: bool):
        if checked:
            # Vice versa: if Smart Destination is turned ON, turn OFF Global Fixed Destination
            self.row_global_fixed.setChecked(False)
            self.path_container.setVisible(False)
            self.smart_mgr.set_smart_enabled(True)
        else:
            self.smart_mgr.set_smart_enabled(False)

    def _on_global_fixed_toggled(self, checked: bool):
        self.path_container.setVisible(checked)
        if checked:
            # Vice versa: if Global Fixed Destination is turned ON, turn OFF Smart Destination
            self.row_smart.setChecked(False)
            self.smart_mgr.set_global_fixed_enabled(True)
        else:
            self.smart_mgr.set_global_fixed_enabled(False)

    def _on_browse_clicked(self):
        current_dir = self.path_input.text().strip() or os.path.expanduser("~")
        chosen = QFileDialog.getExistingDirectory(self, "Select Global Export Folder", current_dir)
        if chosen:
            self.path_input.setText(chosen)
            self.smart_mgr.set_global_fixed_path(chosen)

    def _on_path_text_changed(self, text: str):
        self.smart_mgr.set_global_fixed_path(text)


