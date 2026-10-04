import os
import time
import logging
import hashlib
from datetime import datetime
from threading import Event
from typing import Any, Callable, Dict, Optional, Set
from PySide6.QtCore import QThread, Signal
from app.core.ignore_manager import INTERNAL_PROJECT_IGNORES, get_ignore_manager

logger = logging.getLogger(__name__)

# Extensions safe to read as text/code
ALLOWED_CODE_EXTENSIONS = {
    '.py', '.pyw', '.js', '.jsx', '.ts', '.tsx', '.html', '.htm',
    '.css', '.scss', '.sass', '.less', '.json', '.xml', '.yaml', '.yml',
    '.md', '.txt', '.sql', '.c', '.cpp', '.h', '.hpp', '.java', '.cs',
    '.sh', '.bat', '.ps1', '.dockerfile', '.conf', '.ini', '.toml',
    '.gitignore', '.env', '.vb', '.rb', '.php', '.go', '.rs', '.swift',
    '.kt', '.kts', '.lua', '.pl', '.r', '.m', '.vue', '.svelte'
}

SPECIAL_TEXT_FILES = {'dockerfile', 'makefile', 'license', 'readme', 'changelog', 'cmakelists.txt'}

# Performance limits
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB limit for reading text contents
MAX_FOLDER_DEPTH = 50  # Prevent infinite loops / symlink loops

# Default ignored folder names
DEFAULT_IGNORED_DIRS: Set[str] = {
    '.git', '.svn', '.hg', '.idea', '.vscode', '__pycache__',
    'node_modules', 'dist', 'build', '.next', '.nuxt', 'venv', '.venv', 'env', 'User_Data'
}


def get_display_file_type(filename: str) -> str:
    """Return friendly display type based on extension."""
    _, ext = os.path.splitext(filename.lower())
    mapping = {
        '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
        '.tsx': 'React TSX', '.jsx': 'React JSX', '.html': 'HTML',
        '.css': 'CSS', '.scss': 'SCSS', '.json': 'JSON', '.md': 'Markdown',
        '.txt': 'Text', '.c': 'C Source', '.cpp': 'C++ Source',
        '.h': 'C Header', '.hpp': 'C++ Header', '.rs': 'Rust',
        '.go': 'Go', '.java': 'Java', '.cs': 'C#', '.yaml': 'YAML',
        '.yml': 'YAML', '.toml': 'TOML', '.xml': 'XML', '.sql': 'SQL',
        '.sh': 'Shell Script', '.bat': 'Batch Script', '.ps1': 'PowerShell',
        '.png': 'PNG Image', '.jpg': 'JPEG Image', '.svg': 'SVG Vector',
        '.pdf': 'PDF Document', '.zip': 'Archive', '.tar': 'Archive',
    }
    return mapping.get(ext, 'File')


_WIN_RESERVED_NAMES = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def _is_windows_reserved(name: str) -> bool:
    stem = name.split(".")[0].lower()
    return stem in _WIN_RESERVED_NAMES


def _safe_relpath(path: str, start: str) -> str:
    """Compute relative path safely across drives or device mounts without raising ValueError."""
    try:
        return os.path.relpath(path, start)
    except (ValueError, OSError):
        p_norm = os.path.abspath(path).replace("\\", "/")
        s_norm = os.path.abspath(start).replace("\\", "/")
        if p_norm.lower().startswith(s_norm.lower()):
            rel = p_norm[len(s_norm):].lstrip("/")
            return rel if rel else "."
        return os.path.basename(path)


def scan_directory_structure(
    startpath: str,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    pause_event: Optional[Event] = None,
    stop_event: Optional[Event] = None,
    ignore_manager=None,
    collect_metadata: bool = True,
) -> Dict[str, Any]:
    """
    Recursively scans the directory and builds a structured tree dictionary.
    Supports pausing via threading.Event and safe stopping.
    Uses persistent scan ignore rules only.
    """
    if not startpath or not os.path.isdir(startpath):
        logger.warning(f"Invalid start path: {startpath}")
        return {
            'name': 'Invalid',
            'path': startpath or '',
            'type': 'folder',
            'display_type': 'Folder',
            'children': [],
            'structure_signature': '',
        }

    root_name = os.path.basename(os.path.abspath(startpath)) or startpath
    root_node: Dict[str, Any] = {
        'name': root_name,
        'path': '.',
        'abs_path': os.path.abspath(startpath),
        'type': 'folder',
        'display_type': 'Folder',
        'children': [],
        'stats': {
            'files': 0,
            'folders': 0,
            'total_size': 0
        }
    }

    # Stack: (abs_path, parent_node, depth)
    stack = [(os.path.abspath(startpath), root_node, 0)]
    ignore_mgr = ignore_manager or get_ignore_manager()
    processed_count = 0
    total_folders = 0
    total_size = 0
    visited_paths: Set[str] = set()

    structure_hash = hashlib.blake2b(digest_size=16)

    while stack:
        # Check Stop
        if stop_event and stop_event.is_set():
            root_node['structure_signature'] = structure_hash.hexdigest()
            return root_node

        # Check Pause (Blocks if cleared)
        if pause_event:
            pause_event.wait()

        current_path, current_node, depth = stack.pop()

        if depth > MAX_FOLDER_DEPTH:
            logger.warning(f"Max depth reached at {current_path}")
            continue

        try:
            real_path = os.path.realpath(current_path)
            if real_path in visited_paths:
                continue
            visited_paths.add(real_path)
        except OSError:
            continue

        try:
            items = list(os.scandir(current_path))
            # Sort: folders first, then files alphabetically
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
        except (OSError, PermissionError) as e:
            logger.debug(f"Cannot access {current_path}: {e}")
            continue

        for entry in items:
            item = entry.name
            full_path = entry.path

            # Skip hidden files/directories, Windows reserved devices, internal User_Data, and ignored items
            if (
                item.startswith('.')
                or _is_windows_reserved(item)
                or item in INTERNAL_PROJECT_IGNORES
                or item in DEFAULT_IGNORED_DIRS
                or ignore_mgr.should_ignore_scan(item)
                or ignore_mgr.should_ignore_scan(full_path)
            ):
                continue

            try:
                is_dir = entry.is_dir(follow_symlinks=False)
                is_file = entry.is_file(follow_symlinks=False)
            except OSError:
                continue

            try:
                if is_dir:
                    rel_p = _safe_relpath(full_path, startpath)
                    relative = rel_p.replace("\\", "/")
                    total_folders += 1
                    structure_hash.update(f"D:{relative}\n".encode("utf-8", "surrogatepass"))
                    new_folder_node: Dict[str, Any] = {
                        'name': item,
                        'path': rel_p,
                        'abs_path': full_path,
                        'type': 'folder',
                        'display_type': 'Folder',
                        'children': []
                    }
                    current_node['children'].append(new_folder_node)
                    stack.append((full_path, new_folder_node, depth + 1))

                elif is_file:
                    rel_p = _safe_relpath(full_path, startpath)
                    relative = rel_p.replace("\\", "/")
                    processed_count += 1
                    structure_hash.update(f"F:{relative}\n".encode("utf-8", "surrogatepass"))
                    if progress_callback:
                        progress_callback(processed_count, item)

                    if collect_metadata:
                        try:
                            stat_info = entry.stat(follow_symlinks=False)
                            file_size = stat_info.st_size
                            file_mtime = stat_info.st_mtime
                        except (OSError, PermissionError):
                            file_size = 0
                            file_mtime = 0

                        total_size += file_size

                        last_modified = (
                            datetime.fromtimestamp(file_mtime).isoformat()
                            if file_mtime
                            else ""
                        )
                    else:
                        file_size = 0
                        last_modified = ""

                    file_node: Dict[str, Any] = {
                        'name': item,
                        'path': rel_p,
                        'abs_path': full_path,
                        'type': 'file',
                        'display_type': get_display_file_type(item),
                        'size_bytes': file_size,
                        'last_modified': last_modified,
                        'content': None  # Read lazily on-demand during export
                    }

                    current_node['children'].append(file_node)
            except Exception as e:
                logger.debug(f"Skipping entry {full_path}: {e}")
                continue

    root_node['stats'] = {
        'files': processed_count,
        'folders': total_folders,
        'total_size': total_size
    }
    root_node['structure_signature'] = structure_hash.hexdigest()
    return root_node


class DirectoryScannerThread(QThread):
    """
    Background worker thread for scanning directory structures with
    real-time smooth progress emissions, pause/resume, and safe cancellation.
    Supports estimate_progress=False for fast background live scans.
    """
    scan_finished = Signal(dict)
    progress_update = Signal(int, int, str)  # current, total, current_file_name
    scan_error = Signal(str)

    def __init__(
        self,
        path: str,
        parent=None,
        ignore_manager=None,
        estimate_progress: bool = False,
        collect_metadata: bool = True,
    ):
        super().__init__(parent)
        self.path = path
        self.ignore_manager = ignore_manager or get_ignore_manager()
        self.estimate_progress = estimate_progress
        self.collect_metadata = collect_metadata
        self.pause_event = Event()
        self.pause_event.set()  # Start in running state
        self.stop_event = Event()
        self.stop_requested = False

        self._last_emit_time = 0.0

    def run(self):
        if not self.path or not os.path.isdir(self.path):
            self.scan_error.emit(f"Invalid directory path: {self.path}")
            return

        self._last_emit_time = 0.0

        def on_progress(count: int, filename: str):
            if self.stop_event.is_set():
                return
            now = time.time()
            if (now - self._last_emit_time) > 0.05:
                self.progress_update.emit(count, 0, filename)
                self._last_emit_time = now

        # Run single-pass recursive directory scan
        try:
            result = scan_directory_structure(
                startpath=self.path,
                progress_callback=on_progress,
                pause_event=self.pause_event,
                stop_event=self.stop_event,
                ignore_manager=self.ignore_manager,
                collect_metadata=self.collect_metadata,
            )
            if not self.stop_event.is_set():
                self.scan_finished.emit(result)
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            self.scan_error.emit(str(e))

    def is_paused(self) -> bool:
        return not self.pause_event.is_set()

    def pause(self):
        self.pause_event.clear()

    def resume(self):
        self.pause_event.set()

    def stop(self):
        self.stop_requested = True
        self.stop_event.set()
        self.pause_event.set()  # Unblock if paused so thread can exit promptly
