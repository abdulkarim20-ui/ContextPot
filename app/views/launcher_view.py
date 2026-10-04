import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget
from app.widgets.action_button import PrimaryActionButton
from app.widgets.drop_zone import DropZoneCard
from app.widgets.recent_bar import RecentBar
from app.widgets.title_bar import HeaderToolBar

class LauncherView(QWidget):
    """
    Main Launcher View hosting:
    - Header toolbar (Back/Forward navigation on left, Settings gear on right).
    - Drop zone card (Empty or Loaded state with centered chip).
    - Recent projects bar.
    - "Scan folder" primary action button (hidden/integrated).
    """
    settings_requested = Signal()
    back_requested = Signal()
    forward_requested = Signal()
    folder_selected = Signal(str, dict)
    folder_cleared = Signal()
    scan_requested = Signal()
    open_explorer_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 1. Header Toolbar (Back / Forward on Left, Settings on Right)
        self.header_toolbar = HeaderToolBar(parent=self)
        self.header_toolbar.settings_clicked.connect(self.settings_requested.emit)
        self.header_toolbar.back_clicked.connect(self.back_requested.emit)
        self.header_toolbar.forward_clicked.connect(self.forward_requested.emit)
        layout.addWidget(self.header_toolbar)

        # 2. Main Drop Zone (Maintains consistent 198px dashed canvas)
        self.drop_zone = DropZoneCard(parent=self)
        self.drop_zone.folder_selected.connect(self._on_folder_selected)
        self.drop_zone.folder_cleared.connect(self._on_folder_cleared)
        self.drop_zone.open_explorer_clicked.connect(self.open_explorer_clicked.emit)
        layout.addWidget(self.drop_zone)

        # 3. Dynamic Recent Projects Bar
        self.recent_bar = RecentBar(parent=self)
        self.recent_bar.recent_selected.connect(self._on_recent_selected)
        layout.addWidget(self.recent_bar)

        # 4. Primary Action Button (compatibility placeholder, kept hidden)
        self.scan_btn = PrimaryActionButton("Scan folder", parent=self)
        self.scan_btn.clicked.connect(self.scan_requested.emit)
        self.scan_btn.hide()
        layout.addWidget(self.scan_btn)

    def _on_folder_selected(self, path: str, data: dict):
        self.recent_bar.refresh()
        is_analyzing = data.get("status", "").startswith("Analyzing")
        self.scan_btn.set_active(not is_analyzing)
        self.folder_selected.emit(path, data)

    def _on_folder_cleared(self):
        self.scan_btn.hide()
        self.header_toolbar.set_forward_enabled(False)
        self.folder_cleared.emit()

    def _on_recent_selected(self, path: str):
        if os.path.exists(path):
            self.drop_zone.set_folder(path)
