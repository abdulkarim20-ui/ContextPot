import os
import sys
from typing import Optional
from PySide6.QtCore import QEvent, QEasingCurve, QPropertyAnimation, QSize, Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from app.config.theme import BG_MAIN, BORDER, TEXT_MAIN, TITLEBAR_BG, TITLEBAR_TOP_GRADIENT
from app.core.icons import get_asset_path, load_icon, render_pixmap
from app.core.scanner import DirectoryScannerThread
from app.core.project_identity import detect_project_identity
from app.core.ignore_manager import get_ignore_manager
from app.core.settings_manager import SettingsManager
from app.core.watcher_manager import FileSystemWatcherManager
from app.core.window_transition import WindowTransitionManager
from app.core.window_utils import apply_native_title_bar, toggle_always_on_top
from app.views.explorer import ExplorerView
from app.views.launcher_view import LauncherView
from app.views.settings.settings_view import SettingsView

class MainWindow(QMainWindow):
    """
    ContextPot - Main Application Window.
    Uses unified Notepad-style seamless canvas between native DWM title bar and client area,
    with a unified outer perimeter frame border.
    """
    TOTAL_WIDTH = 360
    TOTAL_HEIGHT_EMPTY = 314
    TOTAL_HEIGHT_LOADED = 314
    TOTAL_HEIGHT_EXPLORER = 440
    TOTAL_HEIGHT_SETTINGS = 545

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ContextPot")

        # Native window with minimize and close buttons
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        # Window icon configuration:
        # Titlebar icon (16x16) uses Titlebar_logo.svg only
        # Taskbar icon (larger sizes) uses app_logo.ico / app_logo.svg
        window_icon = QIcon()
        pm_title = render_pixmap("Titlebar_logo", (16, 16))
        if pm_title and not pm_title.isNull():
            window_icon.addPixmap(pm_title)

        ico_path = get_asset_path("app_logo.ico")
        if os.path.exists(ico_path):
            app_ico = QIcon(ico_path)
            for sz in [(24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]:
                pm = app_ico.pixmap(*sz)
                if pm and not pm.isNull():
                    window_icon.addPixmap(pm)
        else:
            pm_task = render_pixmap("app_logo", (64, 64))
            if pm_task and not pm_task.isNull():
                window_icon.addPixmap(pm_task)

        if not window_icon.isNull():
            self.setWindowIcon(window_icon)

        self.setStyleSheet(f"background-color: {BG_MAIN};")

        # Scanner thread and state tracking
        self.scan_thread: Optional[DirectoryScannerThread] = None
        self._previous_view_before_settings: Optional[QWidget] = None
        self._has_scanned: bool = False
        self._last_scanned_path: str = ""
        self._auto_scan_requested_path: str = ""

        # Passive Explorer-only filesystem watcher. It registers OS-level
        # notifications; it does not keep project files or directories open.
        self._watcher = FileSystemWatcherManager(self)
        self._watcher.changed.connect(self._on_project_changed)
        self._live_scan_thread: Optional[DirectoryScannerThread] = None
        self._live_scan_pending = False
        self._force_next_scan_refresh = False

        self.settings = SettingsManager()

        # Window transition & resize manager
        self._transition_mgr = WindowTransitionManager(self)
        self._resize_anim = None
        self._overhead_cached = None

        # Set initial client size corresponding to TOTAL_HEIGHT_EMPTY
        initial_client_h = self._to_client_height(self.TOTAL_HEIGHT_EMPTY)
        self.setFixedSize(self.TOTAL_WIDTH, initial_client_h)

        # Central widget: seamless canvas without any internal separator border
        central_widget = QWidget(self)
        central_widget.setObjectName("CentralWidget")
        central_widget.setStyleSheet(f"""
            QWidget#CentralWidget {{
                background-color: {BG_MAIN};
                border: none;
            }}
        """)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(14, 2, 14, 12)
        root_layout.setSpacing(0)

        # Stacked Widget for View Switching (Launcher <-> Explorer <-> Settings)
        self.stack = QStackedWidget(self)
        self.stack.setStyleSheet("background: transparent; border: none;")
        root_layout.addWidget(self.stack)

        # 1. Launcher View
        self.launcher_view = LauncherView(parent=self)
        self.launcher_view.settings_requested.connect(self._open_settings)
        self.launcher_view.forward_requested.connect(self._on_launcher_forward)
        self.launcher_view.open_explorer_clicked.connect(self._on_launcher_forward)
        self.launcher_view.folder_selected.connect(self._on_folder_selected)
        self.launcher_view.folder_cleared.connect(self._on_folder_cleared)
        self.launcher_view.scan_requested.connect(self._on_start_scan)
        self.stack.addWidget(self.launcher_view)

        # 2. Explorer and Settings Views are lazily created on first access
        self._explorer_view: Optional[ExplorerView] = None
        self._settings_view: Optional[SettingsView] = None

    def _ensure_explorer_view(self) -> ExplorerView:
        if self._explorer_view is None:
            self._explorer_view = ExplorerView(parent=self)
            self._explorer_view.back_clicked.connect(self._on_explorer_back)
            self._explorer_view.settings_clicked.connect(self._open_settings)
            self._explorer_view.item_ignored.connect(self._on_item_ignored)
            self._explorer_view.pattern_unignored.connect(self._on_pattern_unignored)
            self.stack.addWidget(self._explorer_view)
        return self._explorer_view

    def _ensure_settings_view(self) -> SettingsView:
        if self._settings_view is None:
            self._settings_view = SettingsView(parent=self)
            self._settings_view.back_clicked.connect(self._close_settings)
            self._settings_view.always_on_top_toggled.connect(self._on_always_on_top)
            self._settings_view.ignore_card.patterns_changed.connect(self._on_ignore_patterns_changed)
            self.stack.addWidget(self._settings_view)
        return self._settings_view

    @property
    def explorer_view(self) -> ExplorerView:
        return self._ensure_explorer_view()

    @property
    def settings_view(self) -> SettingsView:
        return self._ensure_settings_view()

    def _get_frame_overhead(self) -> int:
        """Returns the native titlebar and window border overhead in pixels."""
        if self.isVisible():
            diff = self.frameGeometry().height() - self.geometry().height()
            if diff > 0:
                self._overhead_cached = diff
                return diff
        if self._overhead_cached:
            return self._overhead_cached
        if sys.platform == "win32":
            try:
                import ctypes
                caption_h = ctypes.windll.user32.GetSystemMetrics(4)
                frame_h = ctypes.windll.user32.GetSystemMetrics(32)
                padded_b = ctypes.windll.user32.GetSystemMetrics(92)
                return caption_h + (frame_h + padded_b) * 2
            except Exception:
                pass
        return 39

    def _to_client_height(self, total_height: int) -> int:
        """Convert desired total window height into inner Qt client height."""
        overhead = self._get_frame_overhead()
        return max(200, total_height - overhead)

    def _get_target_total_height(self) -> int:
        """Determine target height based on current active state."""
        current_w = self.stack.currentWidget()
        if self._settings_view is not None and current_w == self._settings_view:
            return self.TOTAL_HEIGHT_SETTINGS
        if self._explorer_view is not None and current_w == self._explorer_view:
            return self.TOTAL_HEIGHT_EXPLORER
        if bool(self.launcher_view.drop_zone.get_selected_path()):
            return self.TOTAL_HEIGHT_LOADED
        return self.TOTAL_HEIGHT_EMPTY

    def showEvent(self, event):
        super().showEvent(event)
        # Apply seamless DWM caption styling with unified outer perimeter border (Light Mode)
        apply_native_title_bar(self, bg_hex=TITLEBAR_BG, text_hex=TEXT_MAIN, border_hex=BORDER, dark_mode=False)

        # Apply native Windows title bar and taskbar icons via WM_SETICON
        if sys.platform == "win32":
            try:
                import ctypes
                WM_SETICON = 0x0080
                ICON_SMALL = 0
                ICON_BIG = 1
                hwnd = int(self.winId())

                # Titlebar icon: Titlebar_logo.svg only
                pm_title = render_pixmap("Titlebar_logo", (16, 16))
                if pm_title and not pm_title.isNull():
                    hicon_small = pm_title.toImage().toHICON()
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)

                # Taskbar icon: app_logo.ico / app_logo.svg
                ico_path = get_asset_path("app_logo.ico")
                hicon_big = None
                if os.path.exists(ico_path):
                    task_pm = QIcon(ico_path).pixmap(64, 64)
                    if task_pm and not task_pm.isNull():
                        hicon_big = task_pm.toImage().toHICON()
                if not hicon_big:
                    pm_task = render_pixmap("app_logo", (64, 64))
                    if pm_task and not pm_task.isNull():
                        hicon_big = pm_task.toImage().toHICON()

                if hicon_big:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
            except Exception:
                pass

        target_total = self._get_target_total_height()
        exact_client_h = self._to_client_height(target_total)
        if self.height() != exact_client_h:
            self.setFixedSize(self.TOTAL_WIDTH, exact_client_h)

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if not self.isMinimized():
                target_total = self._get_target_total_height()
                exact_client_h = self._to_client_height(target_total)
                self.setFixedSize(self.TOTAL_WIDTH, exact_client_h)
        super().changeEvent(event)

    def animate_to_total_height(self, target_total_h: int):
        """Smooth dynamic window height resizing (snappy ~120ms)."""
        target_client_h = self._to_client_height(target_total_h)
        current_size = self.size()
        target_size = QSize(self.TOTAL_WIDTH, target_client_h)
        if current_size == target_size:
            return

        self.setMinimumSize(self.TOTAL_WIDTH, min(current_size.height(), target_client_h))
        self.setMaximumSize(self.TOTAL_WIDTH, max(current_size.height(), target_client_h))

        if self._resize_anim is not None:
            self._resize_anim.stop()

        self._resize_anim = QPropertyAnimation(self, b"size")
        self._resize_anim.setDuration(120)
        self._resize_anim.setStartValue(current_size)
        self._resize_anim.setEndValue(target_size)
        self._resize_anim.setEasingCurve(QEasingCurve.OutCubic)

        def _on_finish():
            self.setFixedSize(self.TOTAL_WIDTH, target_client_h)
            self._resize_anim = None
            self.update()

        self._resize_anim.finished.connect(_on_finish)
        self._resize_anim.start()

    def _open_settings(self):
        self._previous_view_before_settings = self.stack.currentWidget()
        self.stack.setCurrentWidget(self.settings_view)
        self.animate_to_total_height(self.TOTAL_HEIGHT_SETTINGS)

    def _close_settings(self):
        prev = self._previous_view_before_settings or self.launcher_view
        self.stack.setCurrentWidget(prev)
        if self._explorer_view is not None and prev == self._explorer_view:
            self.animate_to_total_height(self.TOTAL_HEIGHT_EXPLORER)
        else:
            has_folder = bool(self.launcher_view.drop_zone.get_selected_path())
            target_total = self.TOTAL_HEIGHT_LOADED if has_folder else self.TOTAL_HEIGHT_EMPTY
            self.animate_to_total_height(target_total)

    def _on_folder_selected(self, path: str, data: dict):
        is_analyzing = data.get("status", "").startswith("Analyzing")

        # The drop-zone emits twice for a normal selection: an immediate
        # "Analyzing..." payload and a later "Ready to scan" payload. Do not
        # kill an auto-scan when the second payload arrives.
        if is_analyzing:
            self._stop_running_scan()

        norm_path = os.path.normcase(os.path.abspath(path))
        norm_last = os.path.normcase(os.path.abspath(self._last_scanned_path)) if self._last_scanned_path else ""
        is_same_as_last = bool(norm_last and norm_path == norm_last)

        if not is_same_as_last:
            self._has_scanned = False
            get_ignore_manager().clear_session_patterns()

        # Initial folder selection auto-scans by default; scan button remains hidden
        self.launcher_view.scan_btn.hide()

        # Enable forward navigation if we have previously scanned project data in the explorer
        has_explorer_project = bool(self._explorer_view is not None and getattr(self._explorer_view, "_project_path", None))
        if self._has_scanned or has_explorer_project:
            self.launcher_view.header_toolbar.set_forward_enabled(True)
            if self._has_scanned and is_same_as_last:
                self.launcher_view.drop_zone._explorer_link_btn.show()

        # Auto Scan is triggered directly on folder selection (reducing 1 manual click step).
        # Do not restart scan if this project is already scanned and loaded
        if not (self._has_scanned and is_same_as_last):
            if is_analyzing or path != self._auto_scan_requested_path:
                self._auto_scan_requested_path = path
                QTimer.singleShot(0, self._on_start_scan)

        if self.stack.currentWidget() == self.launcher_view:
            self.animate_to_total_height(self.TOTAL_HEIGHT_LOADED)

    def _on_folder_cleared(self):
        self._stop_running_scan()
        self._has_scanned = False
        self._last_scanned_path = ""
        self._auto_scan_requested_path = ""
        get_ignore_manager().clear_session_patterns()
        self.launcher_view.scan_btn.setText("Scan folder")
        self.launcher_view.scan_btn.set_active(False)
        self.launcher_view.scan_btn.hide()
        if self.stack.currentWidget() == self.launcher_view:
            self.animate_to_total_height(self.TOTAL_HEIGHT_EMPTY)

    def _stop_running_scan(self):
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
            self.scan_thread.wait(500)
            self.scan_thread = None

    def _on_start_scan(self):
        # 1. If currently scanning, handle Pause / Resume toggle
        if self.scan_thread and self.scan_thread.isRunning():
            if self.scan_thread.is_paused():
                self.scan_thread.resume()
                self.launcher_view.scan_btn.setText("Pause")
                self.launcher_view.drop_zone.set_scan_paused(False)
            else:
                self.scan_thread.pause()
                self.launcher_view.scan_btn.setText("Resume")
                self.launcher_view.drop_zone.set_scan_paused(True)
            return

        # 2. Initiate fresh scan
        folder_path = self.launcher_view.drop_zone.get_selected_path()
        if not folder_path or not os.path.exists(folder_path):
            return

        self.launcher_view.scan_btn.setText("Pause")
        self.launcher_view.drop_zone.start_scan_progress()

        self.scan_thread = DirectoryScannerThread(
            folder_path,
            parent=self,
            ignore_manager=get_ignore_manager(),
            estimate_progress=False,
        )
        self.scan_thread.progress_update.connect(self._on_scan_progress)
        self.scan_thread.scan_finished.connect(self._on_scan_finished)
        self.scan_thread.scan_error.connect(self._on_scan_error)
        self.scan_thread.start()

    def _on_scan_progress(self, current: int, total: int, filename: str):
        self.launcher_view.drop_zone.update_scan_progress(current, total, filename)

    def _on_scan_finished(self, data: dict):
        self._has_scanned = True
        self._last_scanned_path = self.launcher_view.drop_zone.get_selected_path()

        # Format scanned stats to keep drop zone chip accurate when navigating back to launcher
        stats = data.get("stats", {})
        files_cnt = stats.get("files", 0)
        folders_cnt = stats.get("folders", 0)
        total_size = stats.get("total_size", 0)
        if total_size >= 1024 * 1024:
            size_str = f"{total_size / (1024 * 1024):.1f} MB"
        elif total_size >= 1024:
            size_str = f"{total_size / 1024:.1f} KB"
        else:
            size_str = f"{total_size} B"

        project_name = data.get("name") or os.path.basename(self._last_scanned_path) or "Project"
        project_path = data.get("abs_path") or self._last_scanned_path

        project_identity = detect_project_identity(data)
        card_data = {
            "name": project_name,
            "path": project_path,
            "files": files_cnt,
            "folders": folders_cnt,
            "size_str": size_str,
            "project_identity": project_identity,
            "status": "Scan completed",
        }
        self.launcher_view.drop_zone._current_data = card_data
        self.launcher_view.drop_zone.loaded_card.set_data(card_data)
        self.launcher_view.drop_zone.finish_scan_progress()

        self.explorer_view.set_project(project_name, project_path, data)

        # Transition immediately to Explorer View without showing "Rescan folder" on launcher
        self._transition_to_explorer()

    def _on_launcher_forward(self):
        """Navigate forward to explorer if a project was scanned or active."""
        if self._has_scanned or (self._explorer_view is not None and self._explorer_view._project_path):
            self._transition_to_explorer()

    def _transition_to_explorer(self):
        exp = self.explorer_view
        exp.reset_view_state()
        self.launcher_view.header_toolbar.set_forward_enabled(False)
        self.stack.setCurrentWidget(exp)
        self.animate_to_total_height(self.TOTAL_HEIGHT_EXPLORER)
        # Defer watcher initialization so explorer appearance is instantaneous
        project_path = exp._project_path
        if project_path:
            QTimer.singleShot(0, lambda p=project_path: self._start_project_watcher(p))

    def _on_scan_error(self, error_msg: str):
        self.launcher_view.scan_btn.setText("Scan folder")
        self.launcher_view.drop_zone.reset_scan_progress("Scan failed")

    def _on_explorer_back(self):
        """Return to Launcher, stop watcher/live scan, and enable Forward navigation."""
        if self._explorer_view is not None:
            self._explorer_view.reset_view_state()
        self._stop_project_watcher()
        self._stop_live_scan()

        self.stack.setCurrentWidget(self.launcher_view)
        self.launcher_view.scan_btn.hide()
        if self._has_scanned or (self._explorer_view is not None and self._explorer_view._project_path):
            self.launcher_view.header_toolbar.set_forward_enabled(True)
            # Show the 'Open Explorer' hint in the drop zone
            self.launcher_view.drop_zone._explorer_link_btn.show()
        # Use LOADED height if a folder is still in the drop zone
        has_folder = bool(self.launcher_view.drop_zone.get_selected_path())
        target_h = self.TOTAL_HEIGHT_LOADED if has_folder else self.TOTAL_HEIGHT_EMPTY
        self.animate_to_total_height(target_h)

    def closeEvent(self, event):
        self._stop_running_scan()
        self._stop_project_watcher()
        self._stop_live_scan()
        super().closeEvent(event)

    def _start_project_watcher(self, project_path: str):
        if not project_path or not os.path.isdir(project_path):
            return
        self._watcher.start(project_path, get_ignore_manager())

    def _stop_project_watcher(self):
        self._watcher.stop()

    def _stop_live_scan(self):
        self._live_scan_pending = False
        if self._live_scan_thread and self._live_scan_thread.isRunning():
            self._live_scan_thread.stop()
            self._live_scan_thread.wait(500)
        self._live_scan_thread = None

    def _on_project_changed(self):
        """Debounced watcher callback: refresh the Explorer silently without manual rescan."""
        if self._explorer_view is None or not self._explorer_view._project_path:
            return
        if not os.path.isdir(self._explorer_view._project_path):
            return

        if self._live_scan_thread and self._live_scan_thread.isRunning():
            self._live_scan_pending = True
            return

        QTimer.singleShot(0, self._start_live_scan)

    def _start_live_scan(self):
        if self._explorer_view is None or not self._explorer_view._project_path or not os.path.isdir(self._explorer_view._project_path):
            return
        if self._live_scan_thread and self._live_scan_thread.isRunning():
            self._live_scan_pending = True
            return

        self._live_scan_thread = DirectoryScannerThread(
            self._explorer_view._project_path,
            parent=self,
            ignore_manager=get_ignore_manager(),
            estimate_progress=False,
            collect_metadata=False,
        )
        self._live_scan_thread.progress_update.connect(lambda *_: None)
        self._live_scan_thread.scan_finished.connect(self._on_live_scan_finished)
        self._live_scan_thread.scan_error.connect(self._on_live_scan_error)
        self._live_scan_thread.finished.connect(self._on_live_scan_thread_finished)
        self._live_scan_thread.start()

    def _on_live_scan_finished(self, data: dict):
        if self._explorer_view is not None:
            force = self._force_next_scan_refresh
            self._force_next_scan_refresh = False
            self.explorer_view.refresh_scan_data(data, force=force)

    def _on_live_scan_error(self, _error: str):
        # The finished handler below owns the pending-refresh retry.
        pass

    def _on_live_scan_thread_finished(self):
        self._live_scan_thread = None
        if self._live_scan_pending:
            self._live_scan_pending = False
            QTimer.singleShot(0, self._start_live_scan)

    def _on_ignore_patterns_changed(self, _patterns):
        """Immediately re-apply ignore rules to the live Explorer tree."""
        self._force_next_scan_refresh = True
        explorer_active = (
            self._explorer_view is not None and (
                self.stack.currentWidget() == self._explorer_view
                or self._previous_view_before_settings == self._explorer_view
            )
        )
        if explorer_active and self._explorer_view._project_path and os.path.isdir(self._explorer_view._project_path):
            self._watcher.start(self._explorer_view._project_path, get_ignore_manager())
            self._live_scan_pending = False
            if self._live_scan_thread and self._live_scan_thread.isRunning():
                self._live_scan_pending = True
            else:
                QTimer.singleShot(0, self._start_live_scan)

    def _on_item_ignored(self, pattern: str):
        """Update watcher when an item is excluded from the Explorer tree."""
        if self._explorer_view is not None and self._explorer_view._project_path and os.path.isdir(self._explorer_view._project_path):
            path = self._explorer_view._project_path
            QTimer.singleShot(50, lambda: self._watcher.start(path, get_ignore_manager()))

    def _on_pattern_unignored(self, pattern: str):
        """When user removes a pattern from Explorer exclusions or ignore list, refresh watcher and trigger live scan."""
        self._force_next_scan_refresh = True
        if self._explorer_view is not None and self._explorer_view._project_path and os.path.isdir(self._explorer_view._project_path):
            self._watcher.start(self._explorer_view._project_path, get_ignore_manager())
            self._live_scan_pending = False
            if self._live_scan_thread and self._live_scan_thread.isRunning():
                self._live_scan_pending = True
            else:
                QTimer.singleShot(0, self._start_live_scan)
        if self._settings_view is not None:
            self.settings_view.ignore_card.refresh_patterns()

    def _on_always_on_top(self, enabled: bool):
        toggle_always_on_top(self, enabled)

    def show_animated(self, duration: int = 0):
        self._transition_mgr.animate_show(duration=duration)

    def close_animated(self, duration: int = 180):
        self._transition_mgr.animate_close(duration=duration, on_finished=self.close)
