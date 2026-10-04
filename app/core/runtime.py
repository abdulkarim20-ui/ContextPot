r"""
ContextPot runtime mode detection and user data path management.

Portable mode:
    A file named ``portable.flag`` exists beside the executable, or
    the executable filename contains "portable".
    Data is stored in local ``<app_dir>/User_Data``.

Installed mode:
    Frozen Windows executable without portable.flag.
    Data is stored in ``%APPDATA%\ContextPot\User_Data``.
    Never writes user data inside Program Files.

Development mode:
    Running from source -> ``<project_root>/User_Data``.
"""
from __future__ import annotations

import os
import sys
from enum import Enum
from pathlib import Path


class RuntimeMode(str, Enum):
    DEVELOPMENT = "development"
    PORTABLE = "portable"
    INSTALLED = "installed"


APP_NAME = "ContextPot"
PORTABLE_FLAG = "portable.flag"


def app_dir() -> Path:
    """Directory containing the source tree or frozen executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # Go up two levels from app/core/ to project root
    return Path(__file__).resolve().parents[2]


def is_portable() -> bool:
    """Portable is enabled either by portable.flag beside the executable or if executable name contains 'portable'."""
    return (app_dir() / PORTABLE_FLAG).is_file() or "portable" in Path(sys.executable).stem.lower()


def runtime_mode() -> RuntimeMode:
    """Determine the active runtime mode."""
    if not getattr(sys, "frozen", False):
        return RuntimeMode.DEVELOPMENT
    return RuntimeMode.PORTABLE if is_portable() else RuntimeMode.INSTALLED


def user_data_dir() -> Path:
    """
    Return the durable per-user data directory.

    Important:
    - Never write installed user data under Program Files (requires admin permissions).
    - Portable data stays beside the portable executable.
    - Development data stays in the local repository workspace.
    """
    mode = runtime_mode()

    if mode in (RuntimeMode.DEVELOPMENT, RuntimeMode.PORTABLE):
        path = app_dir() / "User_Data"
    else:
        appdata = os.environ.get("APPDATA")
        if not appdata:
            appdata = str(Path.home() / "AppData" / "Roaming")
        path = Path(appdata) / APP_NAME / "User_Data"

    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_info() -> dict[str, str]:
    """Return runtime metadata dictionary."""
    mode = runtime_mode()
    return {
        "mode": mode.value,
        "app_dir": str(app_dir()),
        "user_data_dir": str(user_data_dir()),
    }
