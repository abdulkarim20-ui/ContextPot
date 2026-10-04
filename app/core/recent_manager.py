import json
import os
from typing import List

from app.config.paths import RECENT_DIR_FILE, data_dir

MAX_RECENT_ITEMS = 3

def load_recent_directories() -> List[str]:
    """
    Load recent directory paths from RP_recent_dir.json.
    Automatically filters out folders that no longer exist on disk and saves the cleaned list.
    """
    os.makedirs(data_dir(), exist_ok=True)
    if not os.path.exists(RECENT_DIR_FILE):
        return []

    try:
        with open(RECENT_DIR_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            return []

        # Filter and validate directory existence
        valid_dirs: List[str] = []
        needs_save = False

        for path in data:
            if isinstance(path, str) and os.path.isdir(path):
                norm_path = os.path.abspath(path)
                if norm_path not in valid_dirs:
                    valid_dirs.append(norm_path)
            else:
                needs_save = True

        valid_dirs = valid_dirs[:MAX_RECENT_ITEMS]

        if needs_save or len(valid_dirs) != len(data):
            _save_recent(valid_dirs)

        return valid_dirs
    except Exception:
        return []

def add_recent_directory(path: str) -> List[str]:
    """
    Add a directory path to recent history.
    Inserts at the top, removes duplicates, limits to MAX_RECENT_ITEMS, and persists to disk.
    """
    if not path or not os.path.isdir(path):
        return load_recent_directories()

    norm_path = os.path.abspath(path)
    current = load_recent_directories()

    if norm_path in current:
        current.remove(norm_path)

    current.insert(0, norm_path)
    current = current[:MAX_RECENT_ITEMS]

    _save_recent(current)
    return current

def remove_recent_directory(path: str) -> List[str]:
    """Remove a directory path from recent history and save."""
    norm_path = os.path.abspath(path)
    current = load_recent_directories()

    if norm_path in current:
        current.remove(norm_path)
        _save_recent(current)

    return current

def clear_recent_directories() -> List[str]:
    """Clear all recent directories and save empty list."""
    _save_recent([])
    return []

def _save_recent(dirs: List[str]) -> bool:
    """Safely write directory list to RP_recent_dir.json."""
    try:
        os.makedirs(data_dir(), exist_ok=True)
        temp_file = f"{RECENT_DIR_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(dirs, f, indent=2)

        # Atomic replace
        os.replace(temp_file, RECENT_DIR_FILE)
        return True
    except Exception:
        return False
