import os
from typing import Any, Dict, Optional
from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QPushButton,
    QVBoxLayout,
)
from app.config.theme import ACCENT, BORDER_DASHED
from app.core.icons import load_icon
from app.core.recent_manager import add_recent_directory, load_recent_directories
from app.widgets.drop_zone.empty_drop_view import EmptyDropView
from app.widgets.drop_zone.loaded_folder_card import LoadedFolderCard

class DropZoneCard(QFrame):
    """
    Main Drop Zone Card container with clearly visible dashed border in both empty
    and loaded states, with interactive hover effects in both states.
    Uses instant non-blocking folder selection without secondary disk traversal.
    """
    folder_selected = Signal(str, dict)
    folder_cleared = Signal()
    open_explorer_clicked = Signal()

    CARD_HEIGHT = 198

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("DropZone")
        self.setFixedHeight(self.CARD_HEIGHT)
        self.setAttribute(Qt.WA_Hover, True)

        self._is_drag_active = False
        self._is_hovered = False
        self._current_path = ""
        self._current_data: Optional[Dict[str, Any]] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        # 1. Empty State View
        self.empty_view = EmptyDropView(parent=self)
        self.empty_view.select_clicked.connect(self._open_file_dialog)
        layout.addWidget(self.empty_view)

        # 2. Loaded State View (Nested chip)
        self.loaded_card = LoadedFolderCard(parent=self)
        self.loaded_card.remove_clicked.connect(self.clear_selection)
        self.loaded_card.hide()
        layout.addWidget(self.loaded_card)

        # 3. 'Open Explorer →' forward hint link (shown after scan completes / on return from explorer)
        self._explorer_link_btn = QPushButton("Open Explorer", self)
        self._explorer_link_btn.setCursor(Qt.PointingHandCursor)
        self._explorer_link_btn.setFixedHeight(20)
        _fwd_icon = load_icon("arrow-right", (12, 12), color="#2563eb")
        if _fwd_icon:
            self._explorer_link_btn.setIcon(_fwd_icon)
            self._explorer_link_btn.setIconSize(QSize(12, 12))
            self._explorer_link_btn.setLayoutDirection(Qt.RightToLeft)  # icon on right side
        self._explorer_link_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #2563eb;
                font-size: 11px;
                font-weight: 600;
                padding: 0px 2px;
                text-align: center;
            }
            QPushButton:hover {
                color: #1d4ed8;
                text-decoration: underline;
            }
            QPushButton:pressed {
                color: #1e40af;
            }
        """)
        self._explorer_link_btn.hide()
        self._explorer_link_btn.clicked.connect(self.open_explorer_clicked.emit)
        layout.addWidget(self._explorer_link_btn, 0, Qt.AlignCenter)

    def _on_child_hover(self, hovered: bool):
        self._is_hovered = hovered
        self.update()

    def enterEvent(self, event):
        self._is_hovered = True
        self.empty_view.set_hovered(True)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self.empty_view.set_hovered(False)
        self.update()
        super().leaveEvent(event)

    def _open_file_dialog(self):
        # Resolve initial directory:
        # 1. Currently loaded path if valid
        # 2. Most recent directory from recent history
        # 3. Fallback to user home directory
        start_dir = ""
        if self._current_path and os.path.isdir(self._current_path):
            start_dir = self._current_path
        else:
            recents = load_recent_directories()
            if recents and os.path.isdir(recents[0]):
                start_dir = recents[0]
            else:
                start_dir = os.path.expanduser("~")

        from app.core.window_utils import prompt_select_directory
        folder = prompt_select_directory(
            self,
            "Select Repository or Project Folder",
            start_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if folder:
            self.set_folder(folder)

    def _stop_analyzer(self):
        """No-op kept for API compatibility."""
        pass

    def set_folder(self, path: str, custom_data: Optional[Dict[str, Any]] = None):
        target_path = os.path.abspath(path) if os.path.exists(path) else path
        is_same_path = bool(self._current_path and os.path.normcase(target_path) == os.path.normcase(self._current_path))
        was_link_visible = self._explorer_link_btn.isVisible()

        self._current_path = target_path

        # Persist valid real folder to RP_recent_dir.json
        if os.path.isdir(self._current_path):
            add_recent_directory(self._current_path)

        self.empty_view.hide()
        self.loaded_card.show()
        self.update()

        # If re-selecting the same folder that is already loaded/scanned, preserve state and Open Explorer button
        if is_same_path:
            if was_link_visible:
                self._explorer_link_btn.show()
            if custom_data:
                self._current_data = custom_data
                self.loaded_card.set_data(custom_data)
            elif self._current_data:
                self.loaded_card.set_data(self._current_data)
            self.folder_selected.emit(self._current_path, self._current_data or {})
            return

        # Brand new / different folder: hide explorer button until scanned
        self._explorer_link_btn.hide()

        if custom_data:
            self._current_data = custom_data
            self.loaded_card.set_data(custom_data)
            self.folder_selected.emit(self._current_path, custom_data)
        else:
            # Immediate cheap metadata without secondary disk walk
            name = os.path.basename(self._current_path) or self._current_path
            initial_data = {
                "name": name,
                "path": self._current_path,
                "files": 0,
                "folders": 0,
                "size_str": "Ready",
                "project_identity": {
                    "name": "Detecting…",
                    "icon_file": "project",
                },
                "status": "Ready to scan",
            }
            self._current_data = initial_data
            self.loaded_card.set_data(initial_data)
            self.folder_selected.emit(self._current_path, initial_data)

    def clear_selection(self):
        self._stop_analyzer()
        self._current_path = ""
        self._current_data = None
        self.loaded_card.hide()
        self._explorer_link_btn.hide()
        self.empty_view.set_hovered(self._is_hovered)
        self.empty_view.show()
        self.update()
        self.folder_cleared.emit()

    def get_selected_path(self) -> str:
        return self._current_path

    def get_current_data(self) -> Optional[Dict[str, Any]]:
        return self._current_data

    def start_scan_progress(self):
        self._explorer_link_btn.hide()
        self.loaded_card.start_progress()

    def update_scan_progress(self, current: int, total: int, filename: str = ""):
        self.loaded_card.update_progress(current, total, filename)

    def set_scan_paused(self, paused: bool):
        self.loaded_card.set_paused(paused)

    def finish_scan_progress(self):
        self.loaded_card.finish_progress()
        # Show 'Open Explorer' hint after scan completes - scan auto-transitions,
        # but show briefly in case transition is slower
        self._explorer_link_btn.show()

    def reset_scan_progress(self, status_text: str = "Ready to scan"):
        self._explorer_link_btn.hide()
        self.loaded_card.reset_progress(status_text)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.isLocalFile() for url in urls):
                self._is_drag_active = True
                self.empty_view.set_hovered(True)
                self.update()
                event.acceptProposedAction()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._is_drag_active = False
        self.empty_view.set_hovered(self._is_hovered)
        self.update()
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self._is_drag_active = False
        self.empty_view.set_hovered(self._is_hovered)
        self.update()
        urls = event.mimeData().urls()
        for url in urls:
            if url.isLocalFile():
                local_path = url.toLocalFile()
                if os.path.isdir(local_path):
                    self.set_folder(local_path)
                    event.acceptProposedAction()
                    return
                elif os.path.isfile(local_path):
                    parent_dir = os.path.dirname(local_path)
                    self.set_folder(parent_dir)
                    event.acceptProposedAction()
                    return
        event.ignore()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        radius = 12.0

        if self._is_drag_active:
            # Active file drag over state (Light blue tint)
            painter.setBrush(QColor(37, 137, 255, 20))
            pen = QPen(QColor(ACCENT), 1.35, Qt.CustomDashLine)
            pen.setDashPattern([5, 4])
        elif self._is_hovered:
            # Mouse hover in both empty and loaded states: Soft ice-blue highlight with accent dashed border
            painter.setBrush(QColor("#eff6ff"))
            pen = QPen(QColor(ACCENT), 1.35, Qt.CustomDashLine)
            pen.setDashPattern([5, 4])
        else:
            # Normal State (both empty and loaded): Clean slate-50 canvas with crisp slate-400 dashed border
            painter.setBrush(QColor("#f8fafc"))
            pen = QPen(QColor(BORDER_DASHED), 1.25, Qt.CustomDashLine)
            pen.setDashPattern([5, 4])

        painter.setPen(pen)
        painter.drawRoundedRect(rect, radius, radius)
        painter.end()
