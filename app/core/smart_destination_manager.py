import os
import json
from typing import Dict, Any, Optional

from app.config.paths import SMART_DESTINATION_FILE, data_dir

class SmartDestinationManager:
    """
    Manages smart export destination memory and global fixed export location.
    Persists configuration in User_Data/RP_Smart_destination.json.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SmartDestinationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.smart_destination_enabled: bool = True
        self.global_fixed_destination_enabled: bool = False
        self.global_fixed_destination_path: str = ""
        self.folder_preferences: Dict[str, Dict[str, Any]] = {}
        
        self.load_data()

    def _normalize_path(self, path: Optional[str]) -> str:
        if not path:
            return ""
        return os.path.normpath(os.path.abspath(path)).replace("\\", "/").lower()

    def load_data(self):
        """Load data from RP_Smart_destination.json."""
        os.makedirs(data_dir(), exist_ok=True)
        if not os.path.exists(SMART_DESTINATION_FILE):
            return

        try:
            with open(SMART_DESTINATION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.smart_destination_enabled = data.get("smart_destination_enabled", True)
                    self.global_fixed_destination_enabled = data.get("global_fixed_destination_enabled", False)
                    self.global_fixed_destination_path = data.get("global_fixed_destination_path", "")
                    self.folder_preferences = data.get("folder_preferences", {})
        except Exception as e:
            print(f"[SmartDestinationManager] Error loading config: {e}")

    def save_data(self):
        """Save data to RP_Smart_destination.json."""
        os.makedirs(data_dir(), exist_ok=True)
        data = {
            "smart_destination_enabled": self.smart_destination_enabled,
            "global_fixed_destination_enabled": self.global_fixed_destination_enabled,
            "global_fixed_destination_path": self.global_fixed_destination_path,
            "folder_preferences": self.folder_preferences
        }
        try:
            with open(SMART_DESTINATION_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[SmartDestinationManager] Error saving config: {e}")

    # --- Smart Destination Toggle ---

    def is_smart_enabled(self) -> bool:
        return self.smart_destination_enabled and not self.global_fixed_destination_enabled

    def set_smart_enabled(self, enabled: bool):
        self.smart_destination_enabled = enabled
        if enabled:
            self.global_fixed_destination_enabled = False
        self.save_data()

    # --- Global Fixed Destination ---

    def is_global_fixed_enabled(self) -> bool:
        return self.global_fixed_destination_enabled

    def set_global_fixed_enabled(self, enabled: bool):
        self.global_fixed_destination_enabled = enabled
        if enabled:
            self.smart_destination_enabled = False
        self.save_data()

    def get_global_fixed_path(self) -> str:
        return self.global_fixed_destination_path

    def set_global_fixed_path(self, path: str):
        self.global_fixed_destination_path = path.strip()
        self.save_data()

    # --- Per-Project Preferences & Resolution ---

    def get_default_destination(self, source_folder: str) -> Optional[str]:
        """
        Determines if an automatic export destination should be used.
        Returns target directory path if resolved, else None (prompts file dialog).
        """
        # 1. Global Fixed Destination takes precedence if enabled
        if self.global_fixed_destination_enabled and self.global_fixed_destination_path:
            if os.path.exists(self.global_fixed_destination_path):
                return self.global_fixed_destination_path

        # 2. Smart Destination per project
        if self.smart_destination_enabled and not self.global_fixed_destination_enabled:
            key = self._normalize_path(source_folder)
            pref = self.folder_preferences.get(key, {})
            target = pref.get("default_export_path")
            if target and os.path.exists(target):
                return target

        return None

    def set_default_destination(self, source_folder: str, target_path: str):
        """Set default export location for a source project and reset manual counter."""
        if not source_folder or not target_path:
            return
        key = self._normalize_path(source_folder)
        if key not in self.folder_preferences:
            self.folder_preferences[key] = {}

        self.folder_preferences[key]["default_export_path"] = target_path
        self.folder_preferences[key]["history"] = {"count": 0, "last_path": target_path}
        self.save_data()

    def clear_default_destination(self, source_folder: str):
        """Remove saved default export location for a project."""
        key = self._normalize_path(source_folder)
        if key in self.folder_preferences:
            self.folder_preferences[key]["default_export_path"] = None
            self.save_data()

    def record_export(self, source_folder: str, target_path: str) -> int:
        """
        Tracks consecutive exports to a target directory.
        Returns the consecutive export count.
        """
        if not source_folder or not target_path:
            return 0

        key = self._normalize_path(source_folder)
        if key not in self.folder_preferences:
            self.folder_preferences[key] = {}

        history = self.folder_preferences[key].get("history", {"count": 0, "last_path": None})
        last_path = history.get("last_path")
        count = history.get("count", 0)

        # Compare normalized target paths
        norm_target = self._normalize_path(target_path)
        norm_last = self._normalize_path(last_path) if last_path else None

        if norm_target == norm_last:
            count += 1
        else:
            count = 1

        history["count"] = count
        history["last_path"] = target_path
        self.folder_preferences[key]["history"] = history
        self.save_data()

        return count

    def should_prompt_smart_destination(self, source_folder: str, target_path: str, count: int) -> bool:
        """
        Checks if the 3-in-a-row prompt should be shown:
        - Smart destination is enabled
        - Global fixed destination is not enabled
        - Project doesn't already have a saved default
        - Target path exported 3 times consecutively
        """
        if not self.smart_destination_enabled or self.global_fixed_destination_enabled:
            return False

        key = self._normalize_path(source_folder)
        pref = self.folder_preferences.get(key, {})
        if pref.get("default_export_path"):
            return False

        return count == 3

# Global accessor
def get_smart_destination_manager() -> SmartDestinationManager:
    return SmartDestinationManager()
