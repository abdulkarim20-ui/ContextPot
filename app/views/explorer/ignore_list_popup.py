import os
from typing import List, Optional
from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QCursor, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from app.config.theme import BORDER, FONT_MONO, TEXT_MAIN, TEXT_MUTED
from app.core.icon_manager import get_icon_manager
from app.core.icons import load_icon
from app.core.ignore_manager import get_ignore_manager
from app.core.tooltip import attach_tooltip

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets"))

class IgnoredItemRow(QFrame):
    """Row widget representing an excluded file or folder pattern in active Explorer."""
    removed = Signal(str)

    @staticmethod
    def _resolve_item_icon(pattern: str) -> QIcon:
        """
        Resolve the exact same Material Theme icon used in the Explorer directory tree.
        """
        mgr = get_icon_manager()
        clean = pattern.strip()
        is_explicit_folder = clean.endswith("/") or clean.endswith("\\")
        clean_name = clean.rstrip("/\\")

        # Extract base name if a path was given (e.g. "src/components")
        base_name = os.path.basename(clean_name.replace("\\", "/")) or clean_name
        base_lower = base_name.lower()

        if is_explicit_folder:
            return mgr.get_folder_icon(base_name, is_open=False)

        # Check if known folder name in IconManager mappings
        mappings = getattr(mgr, "_mappings", None) or {}
        folder_names = mappings.get("folderNames", {})
        folder_names_expanded = mappings.get("folderNamesExpanded", {})

        if base_lower in folder_names or base_lower in folder_names_expanded:
            return mgr.get_folder_icon(base_name, is_open=False)

        # If no extension (no dot, or dot only at index 0 like '.git' or hidden folder)
        if "." not in base_name:
            return mgr.get_folder_icon(base_name, is_open=False)

        if base_name.startswith(".") and base_name.count(".") == 1:
            # e.g. .git, .vscode, .idea vs .gitignore, .env
            file_names = mappings.get("fileNames", {})
            file_exts = mappings.get("fileExtensions", {})
            if base_lower in file_names or base_lower[1:] in file_exts:
                return mgr.get_file_icon(base_name)
            return mgr.get_folder_icon(base_name, is_open=False)

        # Otherwise it has a file extension or wildcard (.py, .ts, .json, *.md, etc.)
        return mgr.get_file_icon(base_name)

    def __init__(self, pattern: str, parent=None):
        super().__init__(parent)
        self.pattern = pattern
        self.setObjectName("IgnoredItemRow")
        self.setFixedHeight(30)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self.setStyleSheet("""
            QFrame#IgnoredItemRow {
                background-color: transparent;
                border-radius: 6px;
                padding: 0 4px;
            }
            QFrame#IgnoredItemRow:hover {
                background-color: #f1f5f9;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 4, 0)
        layout.setSpacing(6)

        # Use the exact same icon as used in the Explore directory tree
        self.icon_lbl = QLabel(self)
        self.icon_lbl.setFixedSize(16, 16)
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        ic = self._resolve_item_icon(pattern)
        if ic and not ic.isNull():
            self.icon_lbl.setPixmap(ic.pixmap(QSize(16, 16)))
        else:
            fallback = load_icon("folder" if not ("." in pattern) else "file-text", (14, 14), color="#64748b")
            if fallback:
                self.icon_lbl.setPixmap(fallback.pixmap(QSize(14, 14)))
        layout.addWidget(self.icon_lbl)

        # Pattern name
        self.name_lbl = QLabel(pattern, self)
        self.name_lbl.setStyleSheet(f"""
            color: {TEXT_MAIN};
            font-size: 12px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        attach_tooltip(self.name_lbl, pattern)
        layout.addWidget(self.name_lbl, 1)

        # Restore button (removes pattern from ignore list, restores item to Explorer)
        self.remove_btn = QPushButton(self)
        self.remove_btn.setFixedSize(18, 18)
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        x_ic = load_icon("x", (10, 10), color=TEXT_MUTED)
        if x_ic:
            self.remove_btn.setIcon(x_ic)
            self.remove_btn.setIconSize(QSize(10, 10))
        else:
            self.remove_btn.setText("×")

        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                color: #94a3b8;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                color: #ef4444;
            }
        """)
        attach_tooltip(self.remove_btn, f"Restore '{pattern}' to Explorer")
        self.remove_btn.clicked.connect(lambda: self.removed.emit(self.pattern))
        layout.addWidget(self.remove_btn)

    def _show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        menu.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground, True)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: #ffffff;
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 4px;
                font-size: 12px;
                color: {TEXT_MAIN};
            }}
            QMenu::item {{
                padding: 5px 18px 5px 8px;
                border-radius: 4px;
                background-color: transparent;
                color: {TEXT_MAIN};
            }}
            QMenu::item:selected {{
                background-color: #eff6ff;
                color: #2563eb;
                font-weight: 500;
            }}
        """)
        act_remove = QAction(f"Restore '{self.pattern}' to Explorer", menu)
        act_remove.triggered.connect(lambda: self.removed.emit(self.pattern))
        menu.addAction(act_remove)
        menu.exec(self.mapToGlobal(pos))


class IgnoreListPopup(QFrame):
    """
    Dropdown popup appearing below the Exclude/Ignored Items button in Explorer header.
    Shows the top temporary excluded files/folders in the current Explorer session.
    """
    pattern_unignored = Signal(str)
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setObjectName("IgnoreListPopup")
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setFixedWidth(260)

        self.setStyleSheet(f"""
            QFrame#IgnoreListPopup {{
                background-color: #ffffff;
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(10, 10, 10, 10)
        self.root_layout.setSpacing(8)

        # 1. Header: Icon + Title + Badge
        header_lay = QHBoxLayout()
        header_lay.setContentsMargins(0, 0, 0, 0)
        header_lay.setSpacing(6)

        ic_ignore = load_icon("ignore", (14, 14), color=TEXT_MUTED)
        if ic_ignore:
            ic_lbl = QLabel(self)
            ic_lbl.setFixedSize(14, 14)
            ic_lbl.setPixmap(ic_ignore.pixmap(QSize(14, 14)))
            ic_lbl.setStyleSheet("background: transparent; border: none;")
            header_lay.addWidget(ic_lbl)

        title_lbl = QLabel("Ignored Items", self)
        title_lbl.setStyleSheet(f"""
            color: {TEXT_MAIN};
            font-size: 12px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        header_lay.addWidget(title_lbl)

        header_lay.addStretch(1)

        self.badge_lbl = QLabel("0 hidden", self)
        self.badge_lbl.setStyleSheet("""
            background-color: #f1f5f9;
            color: #64748b;
            font-size: 10px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            border: none;
        """)
        header_lay.addWidget(self.badge_lbl)
        self.root_layout.addLayout(header_lay)

        # 2. Search Input
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search ignored items...")
        self.search_input.setFixedHeight(26)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #f8fafc;
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 0 8px;
                font-size: 12px;
                color: {TEXT_MAIN};
                selection-background-color: #dbeafe;
                selection-color: {TEXT_MAIN};
            }}
            QLineEdit:focus {{
                background-color: #ffffff;
                border: 1px solid #3b82f6;
            }}
            QLineEdit::placeholder {{
                color: {TEXT_MUTED};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.root_layout.addWidget(self.search_input)

        # 3. Scrollable List of Ignored Items
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                min-height: 20px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
                background: none;
            }
        """)

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 4, 0)
        self.list_layout.setSpacing(2)
        self.scroll_area.setWidget(self.list_container)

        self.root_layout.addWidget(self.scroll_area)

        # 4. Empty State Label
        self.empty_lbl = QLabel("No items excluded in Explorer", self)
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        self.empty_lbl.setFixedHeight(50)
        self.empty_lbl.setStyleSheet(f"""
            color: {TEXT_MUTED};
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        self.empty_lbl.hide()
        self.root_layout.addWidget(self.empty_lbl)

    def refresh(self):
        """Populate the list with temporary files & folders excluded in Explorer."""
        mgr = get_ignore_manager()
        query = self.search_input.text().strip().lower()

        # Batch-remove old widgets without triggering layout recalculations
        self.setUpdatesEnabled(False)
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Session patterns are temporarily excluded files/folders (newest first)
        session_p = mgr.get_session_patterns()
        has_any = bool(session_p)

        if query:
            display_patterns = [p for p in session_p if query in p.lower()]
            self.badge_lbl.setText(f"{len(display_patterns)} found")
        else:
            display_patterns = session_p
            count_text = f"{len(session_p)} hidden" if session_p else "0 hidden"
            self.badge_lbl.setText(count_text)

        # Search bar: only show when there are items to search through
        self.search_input.setVisible(has_any)

        if not display_patterns:
            self.scroll_area.hide()
            self.empty_lbl.setText(
                "No matching items" if query
                else "No items excluded yet\n(Right-click → Exclude, or press Delete)"
            )
            self.empty_lbl.show()
        else:
            self.empty_lbl.hide()
            self.scroll_area.show()
            for pattern in display_patterns:
                row = IgnoredItemRow(pattern, self.list_container)
                row.removed.connect(self._on_remove_pattern)
                self.list_layout.addWidget(row)

        self._update_popup_height(count=len(display_patterns), has_search=has_any)
        self.setUpdatesEnabled(True)
        self.update()

    def _update_popup_height(self, count: int, has_search: bool = True):
        # Header is always ~34px; search adds 26px + 8px spacing = 34px
        header_h = 34
        search_h = 34 if has_search else 0   # 26px input + 8px spacing
        margins_h = 20                         # root_layout top+bottom margins (10+10)

        if count == 0:
            # Compact empty state: just header + empty label
            content_h = 52
        elif count <= 5:
            content_h = count * 30 + max(0, count - 1) * 2
        else:
            # 5 rows visible max, scrolls for rest
            content_h = 5 * 30 + 4 * 2

        if count > 0:
            self.scroll_area.setFixedHeight(content_h)

        total = margins_h + header_h + search_h + content_h
        self.setFixedHeight(total)

    def _on_search_changed(self, text: str):
        self.refresh()

    def _on_remove_pattern(self, pattern: str):
        mgr = get_ignore_manager()
        mgr.remove_session_pattern(pattern)
        self.pattern_unignored.emit(pattern)
        self.refresh()

    def show_below_widget(self, target_widget: QWidget):
        """Position popup smoothly below the target widget, aligned properly."""
        self.search_input.clear()
        self.refresh()

        global_pos = target_widget.mapToGlobal(QPoint(0, 0))
        target_w = target_widget.width()
        target_h = target_widget.height()

        popup_w = self.width()
        x = global_pos.x() + target_w - popup_w
        y = global_pos.y() + target_h + 6

        self.move(x, y)
        self.show()
        # Only focus search when there are items to search through
        if self.search_input.isVisible():
            self.search_input.setFocus()

    def hideEvent(self, event):
        self.closed.emit()
        super().hideEvent(event)
