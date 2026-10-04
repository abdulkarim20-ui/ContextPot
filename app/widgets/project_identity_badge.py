"""
Project Identity Badge widget for ContextPot.
Displays the detected repository ecosystem/language with an icon and label
inside a clean, borderless pill badge with a soft blue background.
Example: [Python icon] Python
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from app.config.theme import (
    FONT_PRIMARY,
    FS_CAPTION,
    FW_SEMIBOLD,
)
from app.core.icon_manager import get_icon_manager


class ProjectIdentityBadge(QFrame):
    """
    Lightweight project identity display pill badge.
    Example: [Python icon] Python
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("ProjectIdentityBadge")
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setFixedHeight(20)
        self.setMinimumWidth(80)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(6, 0, 7, 0)
        self._layout.setSpacing(4)
        self._layout.setAlignment(Qt.AlignCenter)

        self._icon = QLabel(self)
        self._icon.setFixedSize(13, 13)
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setStyleSheet("background: transparent; border: none; padding: 0px; margin: 0px;")

        self._name = QLabel("Unknown", self)
        self._name.setStyleSheet(
            f"""
            QLabel {{
                color: #1d4ed8;
                font-family: "{FONT_PRIMARY}";
                font-size: {FS_CAPTION}px;
                font-weight: {FW_SEMIBOLD};
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }}
            """
        )

        self._layout.addWidget(self._icon)
        self._layout.addWidget(self._name)

        self.setStyleSheet("""
            QFrame#ProjectIdentityBadge {
                background-color: rgba(37, 99, 235, 0.10);
                border: none;
                border-radius: 5px;
            }
        """)

        self.set_identity({"name": "Unknown", "icon_file": "project"})

    def set_identity(self, identity: Any) -> None:
        """
        Atomically update project identity.
        The widget is disabled for visual updates while both text and icon
        are changed, preventing one-frame mismatch.
        """
        if isinstance(identity, dict):
            name = str(identity.get("name", "Unknown"))
            icon_file = str(identity.get("icon_file", "project"))
        elif isinstance(identity, str):
            name = identity
            icon_file = identity.lower()
        else:
            name = "Unknown"
            icon_file = "project"

        # --------------------------------------------------------
        # Resolve icon BEFORE touching visible UI.
        # --------------------------------------------------------
        icon_mgr = get_icon_manager()
        try:
            icon = icon_mgr.get_file_icon(icon_file)
        except Exception:
            icon = None

        pix = None
        if icon is not None and not icon.isNull():
            try:
                pix = icon.pixmap(13, 13)
            except Exception:
                pix = None

        # --------------------------------------------------------
        # One visual update.
        # --------------------------------------------------------
        self.setUpdatesEnabled(False)
        try:
            self._name.setText(name)
            if pix is not None and not pix.isNull():
                self._icon.setPixmap(pix)
                self._icon.show()
            else:
                self._icon.clear()
                self._icon.hide()
        finally:
            self.setUpdatesEnabled(True)

        self.adjustSize()
        self.updateGeometry()
        self.update()

    def set_language(self, language: str) -> None:
        """Backward compatibility for set_language calls."""
        self.set_identity({"name": language, "icon_file": language.lower()})

    @property
    def identity_name(self) -> str:
        return self._name.text()
