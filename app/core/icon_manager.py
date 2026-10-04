import os
import json
from typing import Dict, Optional, Tuple
from PySide6.QtGui import QIcon
from app.core.icons import ASSETS_DIR

class IconManager:
    """
    Material Theme File & Folder Icon Manager for PySide6.
    Uses assets/icon_mappings.json and assets/Files Icon/*.svg to resolve
    file extensions, filenames, and folder names to beautiful rich SVG icons.
    Features instant resolution caching and null-icon suppression.
    """
    _instance = None
    _icon_cache: Dict[str, QIcon] = {}
    _file_icon_cache: Dict[str, QIcon] = {}
    _folder_icon_cache: Dict[Tuple[str, bool], QIcon] = {}
    _mappings: Optional[dict] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IconManager, cls).__new__(cls)
            cls._instance.base_path = os.path.join(ASSETS_DIR, "Files Icon")
            cls._instance._load_mappings()
        return cls._instance

    def _load_mappings(self):
        """Load icon mappings from assets/icon_mappings.json."""
        if self._mappings is not None:
            return

        mapping_path = os.path.join(ASSETS_DIR, "icon_mappings.json")
        try:
            if os.path.exists(mapping_path):
                with open(mapping_path, "r", encoding="utf-8") as f:
                    self._mappings = json.load(f)
            else:
                self._mappings = {}
        except Exception as e:
            print(f"[IconManager] Error loading icon mappings: {e}")
            self._mappings = {}

    def _get_icon(self, icon_name: str) -> QIcon:
        """Helper to load and cache QIcon from svg name."""
        if not icon_name:
            return QIcon()

        if icon_name in self._icon_cache:
            return self._icon_cache[icon_name]

        path = os.path.join(self.base_path, f"{icon_name}.svg")

        # Fallback for clones or unusual names
        if not os.path.exists(path):
            base_id = icon_name.split(".")[0]
            path = os.path.join(self.base_path, f"{base_id}.svg")

        if not os.path.exists(path):
            empty_icon = QIcon()
            self._icon_cache[icon_name] = empty_icon
            return empty_icon

        icon = QIcon(path)
        self._icon_cache[icon_name] = icon
        return icon

    def get_file_icon(self, filename: str) -> QIcon:
        """Get icon for a file based on name or extension (Material Theme logic)."""
        name_lower = filename.lower()
        if name_lower in self._file_icon_cache:
            return self._file_icon_cache[name_lower]

        icon = self._resolve_file_icon(name_lower)
        self._file_icon_cache[name_lower] = icon
        return icon

    def _resolve_file_icon(self, name_lower: str) -> QIcon:
        if not self._mappings:
            return self._get_icon("file")

        # 1. Check exact filename matches (e.g. package.json, dockerfile)
        file_names = self._mappings.get("fileNames", {})
        if name_lower in file_names:
            icon = self._get_icon(file_names[name_lower])
            if not icon.isNull():
                return icon

        # 2. Check Extension Match (multi-part support like .test.js)
        exts = self._mappings.get("fileExtensions", {})
        parts = name_lower.split(".")

        for i in range(1, len(parts)):
            candidate = ".".join(parts[i:])
            if candidate in exts:
                icon = self._get_icon(exts[candidate])
                if not icon.isNull():
                    return icon

        # 3. Fallback: try raw extension if not found in mappings
        ext = os.path.splitext(name_lower)[1]
        if ext and ext.startswith("."):
            bare_ext = ext[1:]
            if bare_ext in exts:
                icon = self._get_icon(exts[bare_ext])
                if not icon.isNull():
                    return icon

            icon = self._get_icon(bare_ext)
            if not icon.isNull():
                return icon

        # 4. Final Fallback: Generic File
        return self._get_icon("file")

    def get_folder_icon(self, foldername: str, is_open: bool = False) -> QIcon:
        """Get icon for a folder (Material Theme logic)."""
        name_lower = foldername.lower()
        cache_key = (name_lower, is_open)
        if cache_key in self._folder_icon_cache:
            return self._folder_icon_cache[cache_key]

        icon = self._resolve_folder_icon(name_lower, is_open)
        self._folder_icon_cache[cache_key] = icon
        return icon

    def _resolve_folder_icon(self, name_lower: str, is_open: bool = False) -> QIcon:
        if not self._mappings:
            generic_id = "folder-open" if is_open else "folder"
            return self._get_icon(generic_id)

        folder_names = self._mappings.get("folderNames", {})
        folder_names_expanded = self._mappings.get("folderNamesExpanded", {})

        # 1. Try specific folder name match
        icons_to_check = folder_names_expanded if is_open else folder_names

        if name_lower in icons_to_check:
            icon = self._get_icon(icons_to_check[name_lower])
            if not icon.isNull():
                return icon

        # 2. Derive state from alternate state if only one exists
        if is_open and name_lower in folder_names:
            base_icon_name = folder_names[name_lower]
            open_candidate = f"{base_icon_name}-open"
            icon = self._get_icon(open_candidate)
            if not icon.isNull():
                return icon
            icon = self._get_icon(base_icon_name)
            if not icon.isNull():
                return icon

        if not is_open and name_lower in folder_names_expanded:
            base_icon_name = folder_names_expanded[name_lower]
            if base_icon_name.endswith("-open"):
                closed_candidate = base_icon_name[:-5]
                icon = self._get_icon(closed_candidate)
                if not icon.isNull():
                    return icon
            icon = self._get_icon(base_icon_name)
            if not icon.isNull():
                return icon

        # 3. Final Fallback: Generic Folder Open/Closed
        generic_id = "folder-open" if is_open else "folder"
        return self._get_icon(generic_id)

# Global accessor
def get_icon_manager() -> IconManager:
    return IconManager()
