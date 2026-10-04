import os
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget
from app.config.theme import (
    BORDER_DASHED,
    FONT_PRIMARY,
    FS_BODY_M,
    FS_CAPTION,
    FW_REGULAR,
    FW_SEMIBOLD,
    PRIMARY,
    PRIMARY_HOVER,
    TEXT_MUTED,
    TEXT_PRIMARY,
)
from app.core.recent_manager import load_recent_directories, remove_recent_directory
from app.core.tooltip import attach_tooltip

class RecentBar(QWidget):
    """
    Dynamic quick-access bar showing recent folders with clickable link tags.
    When empty, displays 'Recent: None'.
    When folders exist, displays 'Recent: Folder1 | Folder2'.
    Prevents text overlapping and start-character truncation using elision ('...')
    and dynamic space-aware layout prioritizing clear visibility.
    """
    recent_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.setFixedHeight(26)

        self._paths: List[str] = []

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(4, 0, 4, 0)
        self.layout.setSpacing(6)
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # 1. "Recent:" Label
        self.label = QLabel("Recent:")
        self.label.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-family: "{FONT_PRIMARY}";
            font-size: {FS_BODY_M}px;
            font-weight: {FW_SEMIBOLD};
            background: transparent;
            border: none;
        """)
        self.layout.addWidget(self.label)

        # Container for dynamic links or 'None'
        self.links_container = QWidget(self)
        self.links_container.setStyleSheet("background: transparent;")
        self.links_layout = QHBoxLayout(self.links_container)
        self.links_layout.setContentsMargins(0, 0, 0, 0)
        self.links_layout.setSpacing(6)
        self.links_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.layout.addWidget(self.links_container, 1)

        # Load initial recent directories from User_Data/RP_recent_dir.json
        self.refresh()

    def refresh(self):
        """Reload recent folders from User_Data/RP_recent_dir.json and update the UI."""
        paths = load_recent_directories()
        self.set_recent_paths(paths)

    def set_recent_paths(self, paths: List[str]):
        """Populate the links container with either 'None' or clickable folder links."""
        self._paths = list(paths or [])
        self._relayout_links()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout_links()

    def _relayout_links(self):
        """Build and position links with smart elision and space allocation."""
        while self.links_layout.count():
            child = self.links_layout.takeAt(0)
            if child.widget():
                w = child.widget()
                w.setParent(None)
                w.deleteLater()

        if not self._paths:
            none_lbl = QLabel("None")
            none_lbl.setStyleSheet(f"""
                color: {TEXT_MUTED};
                font-family: "{FONT_PRIMARY}";
                font-size: {FS_BODY_M}px;
                font-weight: {FW_REGULAR};
                background: transparent;
                border: none;
            """)
            self.links_layout.addWidget(none_lbl)
            return

        # Measure available width inside links_container
        avail_w = self.links_container.width()
        if avail_w <= 10:
            parent_w = self.width() if self.width() > 10 else 332
            label_w = self.label.sizeHint().width()
            avail_w = max(180, parent_w - label_w - 24)

        font = QFont(FONT_PRIMARY, FS_BODY_M)
        font.setWeight(QFont.DemiBold)
        fm = QFontMetrics(font)

        SEP_W = 1
        SEP_SPACING = 6 * 2
        SEP_TOTAL = SEP_W + SEP_SPACING
        MIN_THIRD_ITEM_W = 48  # Minimum width needed to display 3rd folder meaningfully
        BTN_PAD = 6            # Safety margin for button text rendering

        names = [os.path.basename(p.rstrip("\\/")) or p for p in self._paths]
        req_widths = [fm.horizontalAdvance(n) + BTN_PAD for n in names]

        # Prioritize showing the first two names clearly.
        # If 3 items exist, only show the 3rd if sufficient space remains.
        if len(names) <= 2:
            items_to_show = list(range(len(names)))
        else:
            needed_first_two = req_widths[0] + req_widths[1] + SEP_TOTAL
            space_left_for_third = avail_w - needed_first_two - SEP_TOTAL
            if space_left_for_third >= MIN_THIRD_ITEM_W:
                items_to_show = [0, 1, 2]
            else:
                items_to_show = [0, 1]

        num_seps = max(0, len(items_to_show) - 1)
        content_avail_w = max(40, avail_w - (num_seps * SEP_TOTAL))
        total_needed = sum(req_widths[i] for i in items_to_show)

        allocated_widths = {}
        if total_needed <= content_avail_w:
            for i in items_to_show:
                allocated_widths[i] = req_widths[i]
        else:
            if len(items_to_show) == 3:
                # 3 items shown: first two get priority (up to 40% each), 3rd gets rest
                w0 = min(req_widths[0], int(content_avail_w * 0.40))
                w1 = min(req_widths[1], int(content_avail_w * 0.40))
                w2 = max(MIN_THIRD_ITEM_W, content_avail_w - w0 - w1)
                allocated_widths[0] = w0
                allocated_widths[1] = w1
                allocated_widths[2] = w2
            elif len(items_to_show) == 2:
                # 2 items shown: balance gracefully
                max_w0 = int(content_avail_w * 0.55)
                w0 = min(req_widths[0], max_w0)
                w1 = content_avail_w - w0
                # If item 1 needs less than w1, donate back to item 0
                if req_widths[1] < w1:
                    w0 = min(req_widths[0], content_avail_w - req_widths[1])
                    w1 = content_avail_w - w0
                allocated_widths[0] = w0
                allocated_widths[1] = w1
            else:
                allocated_widths[items_to_show[0]] = content_avail_w

        for idx, item_idx in enumerate(items_to_show):
            path = self._paths[item_idx]
            name = names[item_idx]
            alloc_w = allocated_widths[item_idx]

            # Fixed-size clean vertical divider
            if idx > 0:
                sep = QFrame()
                sep.setFixedSize(1, 10)
                sep.setStyleSheet(f"background-color: {BORDER_DASHED}; border: none;")
                self.links_layout.addWidget(sep)

            # Left-aligned elided button text with "..." at the end
            text_avail_w = max(10, alloc_w - BTN_PAD)
            elided_name = fm.elidedText(name, Qt.ElideRight, text_avail_w)

            btn = QPushButton(elided_name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {PRIMARY_HOVER};
                    font-family: "{FONT_PRIMARY}";
                    font-size: {FS_BODY_M}px;
                    font-weight: {FW_SEMIBOLD};
                    border: none;
                    padding: 0px 2px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    color: {PRIMARY};
                    text-decoration: underline;
                }}
                QPushButton:pressed {{
                    color: #1e40af;
                }}
            """)
            btn.setMaximumWidth(alloc_w)
            attach_tooltip(btn, path)
            btn.clicked.connect(self._create_click_handler(path))
            self.links_layout.addWidget(btn)

        self.links_layout.addStretch(1)

    def _create_click_handler(self, path: str):
        def _on_click():
            if os.path.isdir(path):
                self.recent_selected.emit(path)
            else:
                # Folder was deleted or moved while displayed: clean up & refresh
                remove_recent_directory(path)
                self.refresh()
        return _on_click
