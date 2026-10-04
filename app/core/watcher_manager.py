import os
from typing import Optional, Set

from PySide6.QtCore import (
    QFileSystemWatcher,
    QObject,
    QThread,
    QTimer,
    Qt,
    Signal,
    Slot,
)

from app.core.ignore_manager import get_ignore_manager


INTERNAL_IGNORED_NAMES = {"User_Data"}


class _WatcherWorker(QObject):
    changed = Signal(str)
    stopped = Signal()

    def __init__(self):
        super().__init__()

        self._watcher: Optional[QFileSystemWatcher] = None
        self._debounce: Optional[QTimer] = None

        self._watched_dirs: Set[str] = set()
        self._pending_dirs: Set[str] = set()

        self._root_path = ""
        self._ignore_manager = None

    @Slot(str, object)
    def start_watching(self, root_path: str, ignore_manager=None):
        self._root_path = os.path.abspath(root_path)
        self._ignore_manager = ignore_manager or get_ignore_manager()

        if not os.path.isdir(self._root_path):
            self.stopped.emit()
            return

        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._on_directory_changed)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)
        self._debounce.timeout.connect(self._flush)

        # IMPORTANT:
        # This recursive traversal now happens in the worker thread.
        self._add_directory_recursive(self._root_path)

    @Slot()
    def stop_watching(self):
        if self._debounce is not None:
            self._debounce.stop()

        if self._watcher is not None:
            try:
                paths = list(self._watched_dirs)
                if paths:
                    self._watcher.removePaths(paths)
            except Exception:
                pass

            self._watcher.deleteLater()
            self._watcher = None

        self._watched_dirs.clear()
        self._pending_dirs.clear()
        self._root_path = ""

        self.stopped.emit()

    def _is_ignored(self, path: str) -> bool:
        name = os.path.basename(path.rstrip("\\/"))

        if not name:
            return False

        return (
            name.startswith(".")
            or name in INTERNAL_IGNORED_NAMES
            or self._ignore_manager.should_ignore_explorer(name)
            or self._ignore_manager.should_ignore_explorer(path)
        )

    def _watch_dir(self, path: str):
        if self._watcher is None:
            return

        path = os.path.abspath(path)

        if path in self._watched_dirs:
            return

        if not os.path.isdir(path):
            return

        if path != self._root_path and self._is_ignored(path):
            return

        try:
            if self._watcher.addPath(path):
                self._watched_dirs.add(path)
        except Exception:
            pass

    def _add_directory_recursive(self, root: str):
        stack = [os.path.abspath(root)]

        while stack:
            current = stack.pop()

            if not os.path.isdir(current):
                continue

            if current != self._root_path and self._is_ignored(current):
                continue

            self._watch_dir(current)

            try:
                with os.scandir(current) as entries:
                    for entry in entries:
                        try:
                            if (
                                entry.name.startswith(".")
                                or entry.name in INTERNAL_IGNORED_NAMES
                                or self._ignore_manager.should_ignore_explorer(entry.name)
                            ):
                                continue

                            if entry.is_dir(follow_symlinks=False):
                                stack.append(entry.path)

                        except OSError:
                            continue

            except (OSError, PermissionError):
                continue

    def _refresh_directory(self, path: str):
        if not os.path.isdir(path):
            return

        self._watch_dir(path)

        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        if (
                            entry.name.startswith(".")
                            or entry.name in INTERNAL_IGNORED_NAMES
                            or self._ignore_manager.should_ignore_explorer(entry.name)
                        ):
                            continue

                        if entry.is_dir(follow_symlinks=False):
                            normalized = os.path.abspath(entry.path)

                            if normalized not in self._watched_dirs:
                                self._add_directory_recursive(normalized)

                    except OSError:
                        continue

        except (OSError, PermissionError):
            pass

    @Slot(str)
    def _on_directory_changed(self, path: str):
        path = os.path.abspath(path)

        self._pending_dirs.add(path)

        # This also happens inside the worker thread.
        self._refresh_directory(path)

        if self._debounce is not None:
            self._debounce.start()

    @Slot()
    def _flush(self):
        pending = tuple(self._pending_dirs)
        self._pending_dirs.clear()

        for path in pending:
            self.changed.emit(path)


class FileSystemWatcherManager(QObject):
    """
    Public watcher facade.

    All QFileSystemWatcher work and recursive filesystem traversal happen
    in a dedicated worker thread. Signals emitted by the worker are delivered
    back to the GUI thread.
    """

    changed = Signal()
    file_changed = Signal(str)
    directory_changed = Signal(str)

    _start_requested = Signal(str, object)
    _stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._thread: Optional[QThread] = None
        self._worker: Optional[_WatcherWorker] = None
        self._root_path = ""

    @property
    def root_path(self) -> str:
        return self._root_path

    def start(self, root_path: str, ignore_manager=None):
        self.stop()

        if not root_path or not os.path.isdir(root_path):
            return

        self._root_path = os.path.abspath(root_path)

        thread = QThread(self)
        worker = _WatcherWorker()

        worker.moveToThread(thread)

        self._start_requested.connect(
            worker.start_watching,
            Qt.QueuedConnection,
        )
        self._stop_requested.connect(
            worker.stop_watching,
            Qt.QueuedConnection,
        )

        worker.changed.connect(self._on_worker_changed)
        worker.stopped.connect(thread.quit)

        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._thread = thread
        self._worker = worker

        thread.start()

        self._start_requested.emit(
            self._root_path,
            ignore_manager or get_ignore_manager(),
        )

    def stop(self):
        thread = self._thread

        if thread is None:
            self._root_path = ""
            return

        try:
            self._stop_requested.emit()
        except RuntimeError:
            pass

        # Give the worker a short opportunity to shut down.
        if thread.isRunning():
            thread.quit()
            thread.wait(500)

        self._thread = None
        self._worker = None
        self._root_path = ""

    @Slot(str)
    def _on_worker_changed(self, path: str):
        self.directory_changed.emit(path)
        self.changed.emit()
