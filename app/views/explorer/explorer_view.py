import os
from typing import Any, Dict, List, Optional
from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from app.config.theme import (
    BG_CARD,
    BORDER,
    TEXT_MAIN,
    TEXT_MUTED,
    TITLEBAR_BORDER,
    TITLEBAR_GRADIENT_QSS,
)
from app.core.icons import load_icon, render_pixmap
from app.core.tooltip import attach_tooltip
from app.views.explorer.directory_tree import DirectoryTreeWidget
from app.widgets.export_bar import ExportBar

class ExplorerView(QWidget):
    """
    Modular File Explorer View.
    Displays:
    1. Top Header Navigation (Back + Explorer title + [Search Pill + Collapse + Settings] aligned on same line).
    2. Central Directory Explorer Canvas with Tree View.
    3. Bottom Export Bar (Format Dropdown Pill + Blue Export Button).
    """
    back_clicked = Signal()
    settings_clicked = Signal()
    export_requested = Signal(str)
    item_ignored = Signal(str)
    pattern_unignored = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        self._project_name = "Project"
        self._project_path = ""
        self._scan_data: Optional[Dict[str, Any]] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 1. Top Header Bar (Clean, borderless navigation matching launcher header)
        self.header_bar = QWidget(self)
        self.header_bar.setObjectName("ExplorerHeader")
        self.header_bar.setFixedHeight(28)
        self.header_bar.setStyleSheet("background: transparent; border: none;")

        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        # Back Button (Back to Scan / Launcher)
        self.back_btn = QPushButton(self.header_bar)
        self.back_btn.setFixedSize(24, 24)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        back_icon = load_icon("arrow-left", (14, 14), color=TEXT_MAIN)
        if back_icon:
            self.back_btn.setIcon(back_icon)
            self.back_btn.setIconSize(QSize(14, 14))
        else:
            self.back_btn.setText("←")

        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 5px;
                color: {TEXT_MAIN};
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #f1f5f9;
            }}
            QPushButton:pressed {{
                background-color: #e2e8f0;
            }}
        """)
        attach_tooltip(self.back_btn, "Back to Launcher")
        self.back_btn.clicked.connect(self.back_clicked.emit)
        header_layout.addWidget(self.back_btn)

        # Forward Button (Disabled in Explorer)
        self.forward_btn = QPushButton(self.header_bar)
        self.forward_btn.setFixedSize(24, 24)
        self.forward_btn.setEnabled(False)
        self.forward_btn.setCursor(Qt.ArrowCursor)
        fwd_icon = load_icon("arrow-right", (14, 14), color="#cbd5e1")
        if fwd_icon:
            self.forward_btn.setIcon(fwd_icon)
            self.forward_btn.setIconSize(QSize(14, 14))
        self.forward_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background: transparent;
            }
        """)
        attach_tooltip(self.forward_btn, "Forward")
        header_layout.addWidget(self.forward_btn)

        # Stable Explorer title.
        self.project_title_lbl = QLabel("Explorer", self.header_bar)
        self.project_title_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.project_title_lbl.setStyleSheet(f"""
            color: {TEXT_MAIN};
            font-size: 13px;
            font-weight: 700;
            background: transparent;
            border: none;
            padding-left: 2px;
        """)
        header_layout.addWidget(self.project_title_lbl)

        header_layout.addStretch(1)

        # Action 1: Search Pill (Integrated directly on the same header line with dropdown-pill feel)
        self.search_pill = QFrame(self.header_bar)
        self.search_pill.setObjectName("SearchPill")
        self.search_pill.setFixedHeight(26)
        self.search_pill.setStyleSheet("""
            QFrame#SearchPill {
                background: transparent;
                border: none;
            }
        """)
        search_pill_layout = QHBoxLayout(self.search_pill)
        search_pill_layout.setContentsMargins(3, 0, 3, 0)
        search_pill_layout.setSpacing(3)

        self.btn_search_toggle = QPushButton(self.search_pill)
        self.btn_search_toggle.setFixedSize(20, 20)
        self.btn_search_toggle.setCursor(Qt.PointingHandCursor)
        search_icon = load_icon("search", (13, 13), color=TEXT_MUTED)
        if search_icon:
            self.btn_search_toggle.setIcon(search_icon)
            self.btn_search_toggle.setIconSize(QSize(13, 13))
        else:
            self.btn_search_toggle.setText("🔍")
        self.btn_search_toggle.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
        """)
        attach_tooltip(self.btn_search_toggle, "Search files & folders")
        self.btn_search_toggle.clicked.connect(self.toggle_search_pill)
        search_pill_layout.addWidget(self.btn_search_toggle)

        self.search_input = QLineEdit(self.search_pill)
        self.search_input.setPlaceholderText("Search files…")
        self.search_input.setFixedHeight(22)
        self.search_input.setFixedWidth(160)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                padding: 0px 4px;
                font-size: 12px;
                color: {TEXT_MAIN};
                selection-background-color: #dbeafe;
                selection-color: {TEXT_MAIN};
            }}
            QLineEdit::placeholder {{
                color: {TEXT_MUTED};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.hide()
        search_pill_layout.addWidget(self.search_input)

        self.btn_clear_search = QPushButton(self.search_pill)
        self.btn_clear_search.setFixedSize(16, 16)
        self.btn_clear_search.setCursor(Qt.PointingHandCursor)
        clear_ic = load_icon("x", (10, 10), color=TEXT_MUTED)
        if clear_ic:
            self.btn_clear_search.setIcon(clear_ic)
            self.btn_clear_search.setIconSize(QSize(10, 10))
        else:
            self.btn_clear_search.setText("✕")
        self.btn_clear_search.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: #e2e8f0;
            }}
        """)
        self.btn_clear_search.clicked.connect(self.close_search_pill)
        self.btn_clear_search.hide()
        search_pill_layout.addWidget(self.btn_clear_search)

        header_layout.addWidget(self.search_pill)

        # Action 2: Ignored Items List Dropdown Button (Near Collapse)
        self.btn_ignore_list = QPushButton(self.header_bar)
        self.btn_ignore_list.setFixedSize(24, 24)
        self.btn_ignore_list.setCursor(Qt.PointingHandCursor)
        ignore_icon = load_icon("ignore", (14, 14), color=TEXT_MUTED)
        if ignore_icon:
            self.btn_ignore_list.setIcon(ignore_icon)
            self.btn_ignore_list.setIconSize(QSize(14, 14))
        else:
            self.btn_ignore_list.setText("⊘")
        self.btn_ignore_list.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
        """)
        attach_tooltip(self.btn_ignore_list, "Ignored items list")
        self.btn_ignore_list.clicked.connect(self._toggle_ignore_popup)
        header_layout.addWidget(self.btn_ignore_list)

        # Action 3: Collapse All Button
        self.collapse_btn = QPushButton(self.header_bar)
        self.collapse_btn.setFixedSize(24, 24)
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        collapse_icon = load_icon("collapse", (14, 14), color=TEXT_MUTED)
        if collapse_icon:
            self.collapse_btn.setIcon(collapse_icon)
            self.collapse_btn.setIconSize(QSize(14, 14))
        else:
            self.collapse_btn.setText("⊞")
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
        """)
        attach_tooltip(self.collapse_btn, "Collapse all")
        self.collapse_btn.clicked.connect(self._on_collapse_clicked)
        header_layout.addWidget(self.collapse_btn)

        # Action 4: Settings Gear Button (Aligned precisely across Launcher & Explorer)
        self.settings_btn = QPushButton(self.header_bar)
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        settings_icon = load_icon("settings", (16, 16), color=TEXT_MUTED)
        if settings_icon:
            self.settings_btn.setIcon(settings_icon)
            self.settings_btn.setIconSize(QSize(16, 16))
        else:
            self.settings_btn.setText("⚙")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
        """)
        attach_tooltip(self.settings_btn, "Settings")
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        header_layout.addWidget(self.settings_btn)

        layout.addWidget(self.header_bar)

        # 2. Main File Explorer Body Area (Rich Directory Tree View)
        self.body_container = QFrame(self)
        self.body_container.setObjectName("ExplorerBody")
        self.body_container.setStyleSheet(f"""
            QFrame#ExplorerBody {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        body_layout = QVBoxLayout(self.body_container)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Directory Tree Widget
        self.tree_widget = DirectoryTreeWidget(self.body_container)
        self.tree_widget.export_subfolder_requested.connect(self._on_export_subfolder)
        self.tree_widget.export_items_requested.connect(self._on_export_items)
        self.tree_widget.item_ignored.connect(self._on_item_ignored)
        body_layout.addWidget(self.tree_widget)

        layout.addWidget(self.body_container, 1)

        # 3. Bottom Export Bar (Format Dropdown + Export Button)
        self.export_bar = ExportBar(self)
        self.export_bar.export_clicked.connect(self._on_main_export_clicked)
        layout.addWidget(self.export_bar)

        # Floating Toast Notification for Export Success
        from app.widgets.toast_notification import ToastNotification
        self.toast = ToastNotification(self)

        # Floating Ignore List Dropdown Popup
        from app.views.explorer.ignore_list_popup import IgnoreListPopup
        self.ignore_popup = IgnoreListPopup(self)
        self.ignore_popup.pattern_unignored.connect(self._on_pattern_unignored)

    def _toggle_ignore_popup(self):
        """Toggle the floating ignore list dropdown below the button."""
        if self.ignore_popup.isVisible():
            self.ignore_popup.close()
        else:
            self.ignore_popup.show_below_widget(self.btn_ignore_list)

    def _on_pattern_unignored(self, pattern: str):
        if self._project_path and os.path.exists(self._project_path):
            from app.core.scanner import scan_directory_structure
            data = scan_directory_structure(self._project_path)
            self._scan_data = data
            self.tree_widget.populate(data)
        self.pattern_unignored.emit(pattern)

    def toggle_search_pill(self):
        """Toggle the inline search input pill in the header bar."""
        is_open = not self.search_input.isVisible()
        if is_open:
            self.search_pill.setStyleSheet(f"""
                QFrame#SearchPill {{
                    background-color: #ffffff;
                    border: 1px solid {BORDER};
                    border-radius: 13px;
                }}
            """)
            self.search_input.show()
            self.search_input.setFocus()
            self.search_input.selectAll()
        else:
            self.close_search_pill()

    def close_search_pill(self):
        """Close search pill, stop any pending debounce timer, and reset tree filtering."""
        if hasattr(self, '_search_debounce_timer') and self._search_debounce_timer.isActive():
            self._search_debounce_timer.stop()
        self._pending_search_text = ""
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self.search_input.hide()
        self.btn_clear_search.hide()
        self.search_pill.setStyleSheet("""
            QFrame#SearchPill {
                background: transparent;
                border: none;
            }
        """)
        self.tree_widget.filter_items("")

    def reset_view_state(self):
        """Reset search and dismiss floating popups when navigating away or returning to Explorer."""
        self.close_search_pill()
        if hasattr(self, 'ignore_popup') and self.ignore_popup.isVisible():
            self.ignore_popup.close()

    def hideEvent(self, event):
        """Automatically reset search and close popups whenever ExplorerView becomes hidden."""
        self.reset_view_state()
        super().hideEvent(event)

    def _on_search_changed(self, text: str):
        """Handle search text input change — debounced 150ms for smooth large-tree filtering."""
        from PySide6.QtCore import QTimer
        if not hasattr(self, '_search_debounce_timer'):
            self._search_debounce_timer = QTimer(self)
            self._search_debounce_timer.setSingleShot(True)
            self._search_debounce_timer.timeout.connect(self._apply_search)
        self._pending_search_text = text
        self._search_debounce_timer.start(150)
        self.btn_clear_search.setVisible(bool(text))

    def _apply_search(self):
        text = getattr(self, '_pending_search_text', '')
        self.tree_widget.filter_items(text)

    def _on_collapse_clicked(self):
        """Collapse all expanded folders in the tree."""
        self.tree_widget.collapse_all_expanded()

    def _on_main_export_clicked(self, mode: str):
        """Export full project data."""
        self.execute_export(mode=mode)

    def _on_export_subfolder(self, abs_path: str, mode: str):
        """Export specific subfolder data."""
        self.execute_export(mode=mode, sub_path=abs_path)

    def _on_export_items(self, items_data: List[Dict[str, Any]], mode: str):
        """Export selected items (files and/or folders)."""
        self.execute_export(mode=mode, selected_items=items_data)

    def execute_export(
        self,
        mode: str,
        sub_path: Optional[str] = None,
        selected_items: Optional[List[Dict[str, Any]]] = None,
    ):
        """Perform export with Smart Destination memory and floating feedback toast."""
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QFileDialog
        from app.core.exporter import export_project_data
        from app.core.scanner import scan_directory_structure
        from app.core.smart_destination_manager import get_smart_destination_manager
        from app.widgets.smart_destination_dialog import SmartDestinationDialog

        smart_mgr = get_smart_destination_manager()

        if selected_items:
            valid_paths = [it.get("abs_path") for it in selected_items if it.get("abs_path")]
            if valid_paths:
                try:
                    common_dir = os.path.commonpath(valid_paths)
                    if os.path.isfile(common_dir):
                        common_dir = os.path.dirname(common_dir)
                except Exception:
                    common_dir = self._project_path
            else:
                common_dir = self._project_path

            source_path = common_dir if (common_dir and os.path.exists(common_dir)) else self._project_path

            if len(selected_items) == 1:
                item_name = selected_items[0].get("name", "")
                folder_name = os.path.splitext(item_name)[0] if selected_items[0].get("type") == "file" else item_name
            else:
                parent_basename = os.path.basename(source_path) or self._project_name
                folder_name = f"{parent_basename}_selected"
        else:
            source_path = sub_path if (sub_path and os.path.exists(sub_path)) else self._project_path
            folder_name = os.path.basename(source_path) if source_path else self._project_name

        # Check if default export destination is already established (via Smart or Global Fixed setting)
        target_dir = smart_mgr.get_default_destination(source_path) if source_path else None

        should_prompt = False
        prompt_target = ""

        if not target_dir:
            dialog_title = f"Select Export Directory for '{folder_name}'" if folder_name else "Select Export Directory"
            
            # Smart starting directory:
            # 1. Last recorded export path for this project in history
            # 2. Source project's folder
            # 3. Global fixed path if set
            # 4. Most recent project folder from history
            start_export_dir = ""
            if source_path:
                pref = smart_mgr.folder_preferences.get(smart_mgr._normalize_path(source_path), {})
                last_p = pref.get("history", {}).get("last_path")
                if last_p and os.path.isdir(last_p):
                    start_export_dir = last_p
                elif os.path.isdir(source_path):
                    start_export_dir = source_path
            
            if not start_export_dir and smart_mgr.global_fixed_destination_path and os.path.isdir(smart_mgr.global_fixed_destination_path):
                start_export_dir = smart_mgr.global_fixed_destination_path
            
            if not start_export_dir:
                from app.core.recent_manager import load_recent_directories
                recents = load_recent_directories()
                if recents and os.path.isdir(recents[0]):
                    start_export_dir = recents[0]
                else:
                    start_export_dir = os.path.expanduser("~")

            from app.core.window_utils import prompt_select_directory
            target_dir = prompt_select_directory(
                self,
                dialog_title,
                start_export_dir,
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            if not target_dir:
                self.export_bar.export_btn.stop_shimmer()
                return

            if source_path:
                count = smart_mgr.record_export(source_path, target_dir)
                if smart_mgr.should_prompt_smart_destination(source_path, target_dir, count):
                    should_prompt = True
                    prompt_target = target_dir

        # Ensure quick shimmer is active during the export process
        self.export_bar.export_btn.start_shimmer(cycle_duration_ms=450)

        if selected_items:
            from app.core.ignore_manager import get_ignore_manager
            mgr = get_ignore_manager()
            children = []
            for item in selected_items:
                name = item.get("name", "")
                abs_p = item.get("abs_path", "")
                item_type = item.get("type", "file")

                if mgr.should_ignore_explorer(abs_p or name):
                    continue

                if item_type == "folder" and abs_p and os.path.isdir(abs_p):
                    folder_data = scan_directory_structure(abs_p)
                    children.append(folder_data)
                elif abs_p and os.path.isfile(abs_p):
                    node = dict(item)
                    try:
                        node["size"] = os.path.getsize(abs_p)
                    except OSError:
                        pass
                    rel_to_proj = os.path.relpath(abs_p, source_path or self._project_path)
                    node["path"] = rel_to_proj.replace("\\", "/")
                    children.append(node)
                else:
                    children.append(dict(item))

            data_to_export = {
                "name": folder_name,
                "path": "",
                "abs_path": source_path or self._project_path,
                "type": "folder",
                "children": children,
            }
        else:
            # Always build a fresh payload at export time. The Explorer watcher keeps
            # the UI current, but this final scan guarantees that a save/create/delete
            # that happened immediately before clicking Export is included.
            export_root = sub_path if (sub_path and os.path.isdir(sub_path)) else self._project_path
            if not export_root or not os.path.isdir(export_root):
                self.export_bar.export_btn.stop_shimmer()
                return

            data_to_export = scan_directory_structure(export_root)
            if not sub_path:
                self._scan_data = data_to_export
                self.tree_widget.populate(data_to_export)

        try:
            created_files = export_project_data(data_to_export, target_dir, mode=mode)
            if created_files:
                filename = os.path.basename(created_files[0])

                # Quick shimmer runs continuously until the export popup toast appears
                def _on_export_complete():
                    self.toast.show_message(f"Exported: {filename}")
                    self.export_bar.export_btn.stop_shimmer()
                    self.export_requested.emit(created_files[0])

                    # When the export toast finishes (after 2.5s), display Smart Destination prompt
                    if should_prompt and prompt_target and source_path:
                        def _show_smart_prompt():
                            dlg = SmartDestinationDialog(
                                target_path=prompt_target,
                                project_name=folder_name,
                                parent=self.window() or self
                            )
                            if dlg.exec():
                                smart_mgr.set_default_destination(source_path, prompt_target)

                        QTimer.singleShot(2700, _show_smart_prompt)

                # 650ms window ensures ~1.5 snappy shimmer sweeps are clearly visible before popup appears
                QTimer.singleShot(650, _on_export_complete)
            else:
                self.export_bar.export_btn.stop_shimmer()
        except Exception as e:
            self.export_bar.export_btn.stop_shimmer()
            print(f"[Export] Error exporting data: {e}")

    def keyPressEvent(self, event):
        """Handle Escape key to dismiss search pill."""
        if event.key() == Qt.Key_Escape and self.search_input.isVisible():
            self.close_search_pill()
            event.accept()
            return
        super().keyPressEvent(event)

    def set_project(self, name: str, path: str, scan_data: Optional[Dict[str, Any]] = None):
        """Set project details and scanned directory payload."""
        self._project_name = name or "Project"
        self._project_path = path or (scan_data.get("abs_path") if scan_data else "") or ""
        self._scan_data = scan_data

        # Keep the header title stable as "Explorer"; do not duplicate the
        # selected folder name next to the Back button.

        if self._scan_data:
            self.tree_widget.populate(self._scan_data)
        elif self._project_path and os.path.exists(self._project_path):
            from app.core.scanner import scan_directory_structure
            data = scan_directory_structure(self._project_path)
            self._scan_data = data
            self.tree_widget.populate(data)

    def refresh_scan_data(self, scan_data: Optional[Dict[str, Any]], force: bool = False):
        """Replace live project data without changing the Explorer header."""
        if not scan_data:
            return

        old_signature = (
            self._scan_data.get("structure_signature")
            if self._scan_data
            else None
        )

        new_signature = scan_data.get("structure_signature")

        self._scan_data = scan_data

        # File content/metadata changed, but tree structure did not.
        # Do NOT rebuild thousands of QTreeWidgetItems unless forced (e.g. pattern unignored).
        if (
            not force
            and old_signature
            and new_signature
            and old_signature == new_signature
        ):
            return

        self.tree_widget.populate(scan_data)

    def get_scan_data(self) -> Optional[Dict[str, Any]]:
        return self._scan_data

    def _on_item_ignored(self, pattern: str):
        if self._scan_data:
            self._remove_from_scan_data(self._scan_data, pattern)
        if hasattr(self, 'ignore_popup') and self.ignore_popup.isVisible():
            self.ignore_popup.refresh()
        self.item_ignored.emit(pattern)

    def _remove_from_scan_data(self, node: Dict[str, Any], pattern: str):
        if not isinstance(node, dict):
            return
        from app.core.ignore_manager import get_ignore_manager
        mgr = get_ignore_manager()
        children = []
        for child in node.get("children", []):
            c_name = child.get("name", "")
            c_path = child.get("path", "")
            c_abs = child.get("abs_path", "")
            if (
                c_name == pattern
                or c_path == pattern
                or c_abs == pattern
                or mgr.should_ignore_explorer(c_name)
                or (c_path and mgr.should_ignore_explorer(c_path))
                or (c_abs and mgr.should_ignore_explorer(c_abs))
            ):
                continue
            self._remove_from_scan_data(child, pattern)
            children.append(child)
        node["children"] = children





