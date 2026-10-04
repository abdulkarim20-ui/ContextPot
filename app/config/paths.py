"""
Application base directory and asset/data path resolvers.
User data paths are delegated to app.core.runtime.user_data_dir() as the single source of truth.
"""
import os
import sys


def base_dir() -> str:
    """Return the application base directory (supports PyInstaller bundles)."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    # Go up two levels from app/config/ to project root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


ASSETS_DIR = os.path.join(base_dir(), "assets")


def data_dir() -> str:
    """
    Return the user data directory.
    Delegates directly to app.core.runtime.user_data_dir() as the single authority.
    """
    from app.core.runtime import user_data_dir
    return str(user_data_dir())


def _resolve_file(filename: str, legacy_filename: str) -> str:
    path = os.path.join(data_dir(), filename)
    legacy = os.path.join(data_dir(), legacy_filename)
    if not os.path.exists(path) and os.path.exists(legacy):
        return legacy
    return path


# Standard RP_ prefixed storage files (with backwards-compatible legacy fallback)
IGNORE_FILE = _resolve_file("RP_Ignore_pattern.json", "CS_Ignore_pattern.json")
RECENT_DIR_FILE = _resolve_file("RP_recent_dir.json", "CS_recent_dir.json")
SETTINGS_FILE = _resolve_file("RP_settings.json", "CS_settings.json")
SMART_DESTINATION_FILE = _resolve_file("RP_Smart_destination.json", "CS_Smart_destination.json")
