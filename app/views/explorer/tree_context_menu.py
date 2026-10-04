import os
import subprocess
from typing import Any, Callable, Dict, List, Optional
from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QAction, QColor, QCursor, QIcon
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QMenu, QTreeWidgetItem, QWidget
from app.config.theme import BORDER, TEXT_MAIN, TEXT_MUTED
from app.core.icons import load_icon
from app.core.ignore_manager import get_ignore_manager

class ExplorerContextMenu(QMenu):
    """
    Sleek, rounded modern context menu matching the application theme.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        chevron_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "chevron-right.svg")).replace("\\", "/")

        self.setStyleSheet(f"""
            QMenu {{
                background-color: #ffffff;
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 4px;
                font-size: 12px;
                color: {TEXT_MAIN};
            }}
            QMenu::item {{
                padding: 5px 28px 5px 8px;
                border-radius: 4px;
                background-color: transparent;
                color: {TEXT_MAIN};
            }}
            QMenu::item:selected {{
                background-color: #eff6ff;
                color: #2563eb;
                font-weight: 500;
            }}
            QMenu::item:disabled {{
                color: {TEXT_MUTED};
            }}
            QMenu::icon {{
                padding-left: 4px;
            }}
            QMenu::right-arrow {{
                image: url("{chevron_path}");
                width: 12px;
                height: 12px;
                padding-right: 6px;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {BORDER};
                margin: 4px 6px;
            }}
        """)

def reveal_in_explorer(path: str):
    if not path or not os.path.exists(path):
        return
    try:
        norm_p = os.path.normpath(path)
        if os.path.isfile(norm_p):
            subprocess.Popen(f'explorer.exe /select,"{norm_p}"')
        else:
            os.startfile(norm_p)
    except Exception as e:
        print(f"[ContextMenu] Error revealing in explorer: {e}")

class TreeContextMenuBuilder:
    """Builds and executes context actions for single or multi-selected directory tree items."""
    def __init__(
        self,
        tree_widget: QWidget,
        selected_items: List[QTreeWidgetItem],
        items_data: List[Dict[str, Any]],
        on_ignore_batch: Callable[[List[QTreeWidgetItem], List[str]], None],
        on_export_subfolder: Optional[Callable[[str, str], None]] = None,
        on_export_items: Optional[Callable[[List[Dict[str, Any]], str], None]] = None,
    ):
        self.tree = tree_widget
        self.selected_items = selected_items
        self.items_data = items_data
        self.on_ignore_batch = on_ignore_batch
        self.on_export_subfolder = on_export_subfolder
        self.on_export_items = on_export_items
        self.ignore_manager = get_ignore_manager()

    def _export_selected(self, mode: str):
        if self.on_export_items:
            self.on_export_items(self.items_data, mode)
        elif self.on_export_subfolder and self.items_data:
            abs_p = self.items_data[0].get("abs_path", "")
            self.on_export_subfolder(abs_p, mode)

    def show_menu(self, global_pos: QPoint):
        menu = ExplorerContextMenu(self.tree)
        count = len(self.selected_items)
        if count == 0:
            return

        ic_ignore = load_icon("ignore", (14, 14), color=TEXT_MUTED)
        ic_export = load_icon("export_btn", (14, 14), color=TEXT_MUTED)
        ic_reveal = load_icon("explorer", (14, 14), color=TEXT_MUTED)

        patterns = [d.get("name", "") for d in self.items_data if d.get("name")]

        if count > 1:
            # Multi-selection context actions
            act_ignore_batch = QAction(ic_ignore or QIcon(), f"Exclude {count} items", menu)
            act_ignore_batch.setToolTip("Hide selected items from view and export for this session")
            act_ignore_batch.triggered.connect(lambda: self.on_ignore_batch(self.selected_items, patterns))
            menu.addAction(act_ignore_batch)

            menu.addSeparator()

            # Export multiple selected items
            export_menu = ExplorerContextMenu(menu)
            export_menu.setTitle(f"Export {count} items")
            if ic_export:
                export_menu.setIcon(ic_export)

            act_exp_full = QAction("Whole code + Tree", export_menu)
            act_exp_full.triggered.connect(lambda: self._export_selected("Whole code + Tree"))
            export_menu.addAction(act_exp_full)

            act_exp_tree = QAction("Tree only", export_menu)
            act_exp_tree.triggered.connect(lambda: self._export_selected("Tree only"))
            export_menu.addAction(act_exp_tree)

            menu.addMenu(export_menu)
            menu.addSeparator()

            first_abs = self.items_data[0].get("abs_path", "")
            if first_abs:
                act_reveal = QAction(ic_reveal or QIcon(), "Reveal in File Explorer", menu)
                act_reveal.triggered.connect(lambda: reveal_in_explorer(first_abs))
                menu.addAction(act_reveal)

        else:
            # Single-item context actions
            first_data = self.items_data[0]
            first_item = self.selected_items[0]
            item_type = first_data.get("type", "file")
            name = first_data.get("name", "")
            abs_p = first_data.get("abs_path", "")

            ignore_label = "Exclude" if item_type == "folder" else "Exclude"
            act_ignore = QAction(ic_ignore or QIcon(), ignore_label, menu)
            act_ignore.setToolTip("Hide from view and export for this session")
            act_ignore.triggered.connect(lambda: self.on_ignore_batch([first_item], [name]))
            menu.addAction(act_ignore)

            menu.addSeparator()

            # Export single item (folder or file)
            export_menu = ExplorerContextMenu(menu)
            export_menu.setTitle(f"Export '{name}'")
            if ic_export:
                export_menu.setIcon(ic_export)

            act_exp_full = QAction("Whole code + Tree", export_menu)
            act_exp_full.triggered.connect(lambda: self._export_selected("Whole code + Tree"))
            export_menu.addAction(act_exp_full)

            act_exp_tree = QAction("Tree only", export_menu)
            act_exp_tree.triggered.connect(lambda: self._export_selected("Tree only"))
            export_menu.addAction(act_exp_tree)

            menu.addMenu(export_menu)
            menu.addSeparator()

            if abs_p:
                # Reveal in File Explorer
                act_reveal = QAction(ic_reveal or QIcon(), "Reveal in File Explorer", menu)
                act_reveal.triggered.connect(lambda: reveal_in_explorer(abs_p))
                menu.addAction(act_reveal)

        menu.exec(global_pos)
