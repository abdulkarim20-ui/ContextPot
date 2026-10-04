import os
from collections import deque
from typing import Any, Dict, Optional, Set
from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
)
from app.config.theme import BORDER, FONT_MONO, FONT_UI, TEXT_MAIN, TEXT_MUTED
from app.core.icon_manager import get_icon_manager
from app.core.ignore_manager import get_ignore_manager

class SearchHighlightDelegate(QStyledItemDelegate):
    """
    Custom item delegate that renders tree items with:
    - Clean custom selection (#eff6ff) and hover (#f1f5f9) rounded backgrounds
    - 0 OS-default branch selection artifacts or blue blocks
    - Amber/gold highlight badges (#FEF3C7 / #92400E) for search matches
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_query = ""

    def set_search_query(self, query: str):
        self.search_query = query.strip().lower()

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        self.initStyleOption(option, index)
        rect = option.rect
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        # Draw custom selection / hover background with gentle rounded corners
        if option.state & QStyle.State_Selected:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#eff6ff"))
            painter.drawRoundedRect(rect.adjusted(0, 1, -2, -1), 4, 4)
        elif option.state & QStyle.State_MouseOver:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#f1f5f9"))
            painter.drawRoundedRect(rect.adjusted(0, 1, -2, -1), 4, 4)

        icon = index.data(Qt.DecorationRole)
        text = index.data(Qt.DisplayRole) or ""

        # Draw Icon
        icon_size = 16
        icon_rect = QRect(rect.left() + 2, rect.top() + (rect.height() - icon_size) // 2, icon_size, icon_size)
        if isinstance(icon, QIcon) and not icon.isNull():
            icon.paint(painter, icon_rect, Qt.AlignCenter)
            text_rect = QRect(rect.left() + 22, rect.top(), max(0, rect.width() - 24), rect.height())
        else:
            text_rect = QRect(rect.left() + 4, rect.top(), max(0, rect.width() - 6), rect.height())

        # If no search query or no match in text, paint normal text
        if not self.search_query or self.search_query not in text.lower():
            painter.setFont(option.font)
            text_color = QColor("#2563eb") if (option.state & QStyle.State_Selected) else QColor("#0f172a")
            painter.setPen(text_color)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, text)
            painter.restore()
            return

        # Paint text with highlighted matching characters (Amber Badge)
        painter.setFont(option.font)
        fm = QFontMetrics(option.font)

        x = text_rect.left()
        y_text = text_rect.top() + (text_rect.height() + fm.ascent() - fm.descent()) // 2
        y_box = text_rect.top() + (text_rect.height() - fm.height()) // 2

        lower_text = text.lower()
        q_len = len(self.search_query)
        pos = 0

        while pos < len(text):
            match_idx = lower_text.find(self.search_query, pos)
            if match_idx == -1:
                part = text[pos:]
                painter.setPen(QColor("#2563eb") if (option.state & QStyle.State_Selected) else QColor("#0f172a"))
                painter.drawText(x, y_text, part)
                x += fm.horizontalAdvance(part)
                break
            else:
                if match_idx > pos:
                    prefix = text[pos:match_idx]
                    painter.setPen(QColor("#2563eb") if (option.state & QStyle.State_Selected) else QColor("#0f172a"))
                    painter.drawText(x, y_text, prefix)
                    x += fm.horizontalAdvance(prefix)

                match_text = text[match_idx:match_idx + q_len]
                match_w = fm.horizontalAdvance(match_text)

                # Soft amber badge highlight
                highlight_bg = QRect(x - 1, y_box, match_w + 2, fm.height())
                painter.fillRect(highlight_bg, QColor("#FEF3C7"))

                painter.setPen(QColor("#92400E"))
                painter.drawText(x, y_text, match_text)
                x += match_w
                pos = match_idx + q_len

        painter.restore()


class DirectoryTreeWidget(QTreeWidget):
    """
    Rich, high-performance Directory Tree view using Material file & folder icons.
    Features:
    - Real-time search filtering with amber keyword match highlighting
    - Dynamic folder expand/collapse icons
    - 0-artifact transparent branch selection styling
    - Ultra-clean light mode styling with subtle hover and selection states
    - Crisp, atomic collapse of expanded child folders with instant icon synchronization
    - Right-click context menu for ignoring items and exporting subfolders
    """
    file_selected = Signal(str)
    export_subfolder_requested = Signal(str, str)
    export_items_requested = Signal(list, str)
    item_ignored = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_manager = get_icon_manager()
        self._is_all_collapsed = False
        self._search_query = ""

        self._populate_generation = 0
        self._populate_generation_active = 0
        self._populate_queue = deque()

        self._populate_timer = QTimer(self)
        self._populate_timer.setSingleShot(True)
        self._populate_timer.timeout.connect(self._populate_batch)

        self._populate_active = False

        self.setHeaderHidden(True)
        self.setColumnCount(1)
        self.setIndentation(16)
        self.setRootIsDecorated(True)
        self.setAnimated(False)  # Crisp, instantaneous expand/collapse without visual stutter
        self.setUniformRowHeights(True)
        self.setIconSize(QSize(16, 16))
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setFocusPolicy(Qt.StrongFocus)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_custom_context_menu)

        # Attach Search Highlight Delegate
        self.search_delegate = SearchHighlightDelegate(self)
        self.setItemDelegate(self.search_delegate)

        chevron_right = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "chevron-right.svg")).replace("\\", "/")
        chevron_down = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "chevron-down.svg")).replace("\\", "/")

        self.setStyleSheet(f"""
            QTreeWidget {{
                background-color: #ffffff;
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 6px 4px;
                outline: 0;
                font-family: {FONT_UI};
                font-size: 12px;
                color: {TEXT_MAIN};
            }}
            QTreeWidget::item {{
                height: 24px;
                border-radius: 4px;
                padding-left: 2px;
                padding-right: 4px;
                color: {TEXT_MAIN};
                border: none;
            }}
            QTreeWidget::branch {{
                background-color: #ffffff;
            }}
            QTreeWidget::branch:selected {{
                background-color: #ffffff;
            }}
            QTreeWidget::branch:hover {{
                background-color: #ffffff;
            }}
            QTreeWidget::branch:active {{
                background-color: #ffffff;
            }}
            QTreeWidget::branch:selected:active {{
                background-color: #ffffff;
            }}
            QTreeWidget::branch:selected:!active {{
                background-color: #ffffff;
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                image: url({chevron_right});
                background-color: #ffffff;
            }}
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                image: url({chevron_down});
                background-color: #ffffff;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 4px;
                margin: 4px 1px 4px 0px;
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: #cbd5e1;
                min-height: 20px;
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #94a3b8;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

        self.itemExpanded.connect(self._on_item_expanded)
        self.itemCollapsed.connect(self._on_item_collapsed)
        self.itemClicked.connect(self._on_item_clicked)

    def _on_custom_context_menu(self, pos: QPoint):
        clicked_item = self.itemAt(pos)
        if not clicked_item:
            return

        # Preserve multi-selection: only reset selection if the clicked item
        # is NOT already in the current selection (so Ctrl+click works)
        if not clicked_item.isSelected():
            self.clearSelection()
            clicked_item.setSelected(True)

        selected_items = self.selectedItems()
        if not selected_items:
            selected_items = [clicked_item]

        items_data = [it.data(0, Qt.UserRole) or {} for it in selected_items]

        from app.views.explorer.tree_context_menu import TreeContextMenuBuilder
        builder = TreeContextMenuBuilder(
            tree_widget=self,
            selected_items=selected_items,
            items_data=items_data,
            on_ignore_batch=self.ignore_items_and_remove,
            on_export_subfolder=lambda path, mode: self.export_subfolder_requested.emit(path, mode),
            on_export_items=lambda items, mode: self.export_items_requested.emit(items, mode),
        )
        builder.show_menu(self.viewport().mapToGlobal(pos))

    def ignore_items_and_remove(self, items: list, patterns: list):
        """Atomically remove multiple selected items from tree and add to session ignore list with zero lag."""
        if not items:
            return

        self.setUpdatesEnabled(False)
        for item in items:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                idx = self.indexOfTopLevelItem(item)
                if idx >= 0:
                    self.takeTopLevelItem(idx)

        self.setUpdatesEnabled(True)
        self.viewport().update()

        # Add all patterns to temporary Explorer session ignore list & emit signals
        mgr = get_ignore_manager()
        for pattern in patterns:
            if pattern:
                mgr.add_session_pattern(pattern)
                self.item_ignored.emit(pattern)

    def ignore_item_and_remove(self, item: QTreeWidgetItem, pattern: str):
        """Single-item compatibility wrapper."""
        self.ignore_items_and_remove([item], [pattern])

    def _capture_expanded_paths(self) -> Set[str]:
        expanded = set()
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            data = item.data(0, Qt.UserRole) or {}
            path = data.get("abs_path")
            if data.get("type") == "folder" and path and item.isExpanded():
                expanded.add(os.path.normcase(os.path.abspath(path)))
            iterator += 1
        return expanded

    def _restore_expanded_paths(self, expanded_paths: Set[str]):
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            data = item.data(0, Qt.UserRole) or {}
            path = data.get("abs_path")
            if data.get("type") == "folder" and path:
                normalized = os.path.normcase(os.path.abspath(path))
                if normalized in expanded_paths:
                    item.setExpanded(True)
                    item.setIcon(0, self.icon_manager.get_folder_icon(data.get("name", ""), is_open=True))
            iterator += 1

    def populate(self, scan_data: Optional[Dict[str, Any]]):
        """
        Start an incremental tree rebuild.

        The method returns quickly and creates tree items in small GUI-thread
        batches so mouse/keyboard/window events continue to be processed.
        """
        self._populate_generation += 1
        generation = self._populate_generation

        if self._populate_timer.isActive():
            self._populate_timer.stop()

        if self._populate_active and getattr(self, "_pending_expanded_paths", None):
            expanded_paths = self._pending_expanded_paths
        else:
            expanded_paths = self._capture_expanded_paths()

        self._populate_queue.clear()
        self._populate_active = True

        self.setUpdatesEnabled(False)
        self.clear()

        if not scan_data:
            self.setUpdatesEnabled(True)
            self._populate_active = False
            return

        self._pending_expanded_paths = expanded_paths
        self._pending_scan_data = scan_data

        root_name = scan_data.get("name", "Project")
        root_path = scan_data.get("abs_path", "")

        root_item = QTreeWidgetItem()
        root_item.setText(0, root_name)
        root_item.setIcon(
            0,
            self.icon_manager.get_folder_icon(
                root_name,
                is_open=True,
            ),
        )
        root_item.setData(
            0,
            Qt.UserRole,
            {
                "type": "folder",
                "name": root_name,
                "abs_path": root_path,
            },
        )

        self.addTopLevelItem(root_item)
        root_item.setExpanded(True)

        children = scan_data.get("children", [])

        for node in children:
            self._populate_queue.append(
                (root_item, node)
            )

        self._populate_generation_active = generation

        self.setUpdatesEnabled(True)

        self._populate_timer.start(0)

    def _populate_batch(self):
        if not self._populate_active:
            return

        generation = self._populate_generation_active

        # If another populate() started, abandon this batch.
        if generation != self._populate_generation:
            self._populate_queue.clear()
            self._populate_active = False
            return

        processed = 0

        # Keep each event-loop slice small.
        max_items = 150

        self.setUpdatesEnabled(False)

        try:
            while (
                self._populate_queue
                and processed < max_items
            ):
                parent_item, node = self._populate_queue.popleft()

                item_type = node.get("type", "file")
                name = node.get("name", "")
                abs_path = node.get("abs_path", "")

                mgr = get_ignore_manager()

                if mgr.should_ignore_explorer(abs_path or name):
                    continue

                child_item = QTreeWidgetItem()
                child_item.setText(0, name)
                child_item.setData(0, Qt.UserRole, node)

                if item_type == "folder":
                    child_item.setIcon(
                        0,
                        self.icon_manager.get_folder_icon(
                            name,
                            is_open=False,
                        ),
                    )

                    children = node.get("children", [])

                    # Preserve original order.
                    for child in children:
                        self._populate_queue.append(
                            (child_item, child)
                        )

                else:
                    child_item.setIcon(
                        0,
                        self.icon_manager.get_file_icon(name)
                    )

                parent_item.addChild(child_item)
                processed += 1

        finally:
            self.setUpdatesEnabled(True)

        if self._populate_queue:
            self._populate_timer.start(0)
            return

        self._populate_active = False

        expanded_paths = getattr(
            self,
            "_pending_expanded_paths",
            set(),
        )

        self._restore_expanded_paths(expanded_paths)

        if self._search_query:
            self.filter_items(self._search_query)

        self.viewport().update()

    def filter_items(self, text: str):
        """Filter tree items based on search text and highlight matches."""
        clean_text = text.strip().lower()
        self._search_query = clean_text
        self.search_delegate.set_search_query(clean_text)

        self.setUpdatesEnabled(False)
        try:
            def check_item(item: QTreeWidgetItem) -> bool:
                match = not clean_text or (clean_text in item.text(0).lower())

                child_match = False
                for i in range(item.childCount()):
                    if check_item(item.child(i)):
                        child_match = True

                should_show = match or child_match
                item.setHidden(not should_show)

                if child_match and clean_text:
                    item.setExpanded(True)

                return should_show

            for i in range(self.topLevelItemCount()):
                check_item(self.topLevelItem(i))
        finally:
            self.setUpdatesEnabled(True)
            self.viewport().update()

    def has_expanded_child_folders(self) -> bool:
        """Check if any folder item in the tree is currently expanded."""
        it = QTreeWidgetItemIterator(self)
        while it.value():
            item = it.value()
            data = item.data(0, Qt.UserRole) or {}
            # If any child folder (parent != None) is expanded
            if data.get("type") == "folder" and item.parent() is not None and item.isExpanded():
                return True
            it += 1
        return False

    def collapse_all_expanded(self):
        """Collapse all expanded child folders cleanly at the exact same time."""
        if not self.has_expanded_child_folders():
            return

        it = QTreeWidgetItemIterator(self)
        while it.value():
            item = it.value()
            data = item.data(0, Qt.UserRole) or {}
            if data.get("type") == "folder":
                name = data.get("name", "")
                if item.parent() is not None:
                    item.setExpanded(False)
                    item.setIcon(0, self.icon_manager.get_folder_icon(name, is_open=False))
                else:
                    item.setExpanded(True)
                    item.setIcon(0, self.icon_manager.get_folder_icon(name, is_open=True))
            it += 1

        self.verticalScrollBar().setValue(0)
        self.viewport().update()

    def _on_item_expanded(self, item: QTreeWidgetItem):
        data = item.data(0, Qt.UserRole) or {}
        if data.get("type") == "folder":
            name = data.get("name", "")
            item.setIcon(0, self.icon_manager.get_folder_icon(name, is_open=True))

    def _on_item_collapsed(self, item: QTreeWidgetItem):
        data = item.data(0, Qt.UserRole) or {}
        if data.get("type") == "folder":
            name = data.get("name", "")
            item.setIcon(0, self.icon_manager.get_folder_icon(name, is_open=False))

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.UserRole) or {}
        abs_p = data.get("abs_path", "")
        if abs_p:
            self.file_selected.emit(abs_p)

    def keyPressEvent(self, event):
        """Delete key excludes all currently selected items from Explorer."""
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            selected = self.selectedItems()
            if selected:
                patterns = [
                    (it.data(0, Qt.UserRole) or {}).get("name", "")
                    for it in selected
                ]
                patterns = [p for p in patterns if p]
                if patterns:
                    self.ignore_items_and_remove(selected, patterns)
                event.accept()
                return
        super().keyPressEvent(event)



