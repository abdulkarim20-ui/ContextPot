import json
import os
from typing import Any

from app.config.paths import SETTINGS_FILE, data_dir


class SettingsManager:
    """Small persistent settings store for ContextPot UI preferences."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._settings = {}
        self._load()

    def _load(self):
        os.makedirs(data_dir(), exist_ok=True)
        if not os.path.exists(SETTINGS_FILE):
            return
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._settings = data
        except Exception:
            self._settings = {}

    def _save(self):
        os.makedirs(data_dir(), exist_ok=True)
        tmp = SETTINGS_FILE + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
            os.replace(tmp, SETTINGS_FILE)
        except Exception:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        self._settings[key] = value
        self._save()

    def get_auto_scan(self) -> bool:
        """Whether selecting a folder should immediately start a full scan."""
        return bool(self.get("auto_scan", False))

    def set_auto_scan(self, enabled: bool):
        self.set("auto_scan", bool(enabled))

