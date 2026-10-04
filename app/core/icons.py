import os
import sys
import re
from typing import Dict, Optional, Tuple
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_ICON_DPR = 2.0
_PIXMAP_CACHE: Dict[Tuple[str, int, int, str], Optional[QPixmap]] = {}

def _resolve_assets_dir() -> str:
    """
    Resolve the assets directory path correctly in both:
    - Development mode: running from source tree
    - Frozen mode:      running from a PyInstaller bundle (sys._MEIPASS)
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # PyInstaller one-file: extract dir is sys._MEIPASS
        # PyInstaller one-folder: executable is beside the assets folder
        meipass = sys._MEIPASS
        candidate = os.path.join(meipass, "assets")
        if os.path.isdir(candidate):
            return candidate
        # one-folder fallback: assets shipped beside the EXE
        exe_dir = os.path.dirname(sys.executable)
        candidate2 = os.path.join(exe_dir, "assets")
        if os.path.isdir(candidate2):
            return candidate2
    # Development / source mode
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))

ASSETS_DIR = _resolve_assets_dir()

def render_pixmap(name: str, size: Tuple[int, int], color: Optional[str] = None) -> Optional[QPixmap]:
    """Render an SVG with runtime stroke/fill tinting and Hi-DPI caching."""
    base_name = os.path.splitext(name)[0]
    w, h = size
    cache_key = (base_name, int(w), int(h), color or "")
    if cache_key in _PIXMAP_CACHE:
        val = _PIXMAP_CACHE[cache_key]
        return QPixmap(val) if val is not None else None

    svg_path = os.path.join(ASSETS_DIR, f"{base_name}.svg")
    if os.path.exists(svg_path):
        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                svg = f.read()

            if color:
                # Replace existing fill / stroke with the desired color (except fill="none" / stroke="none")
                svg = re.sub(r'stroke="(?!none")[^"]*"', f'stroke="{color}"', svg)
                svg = re.sub(r'fill="(?!none")[^"]*"', f'fill="{color}"', svg)

            renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
            if renderer.isValid():
                pm = QPixmap(int(w * _ICON_DPR), int(h * _ICON_DPR))
                pm.fill(Qt.transparent)
                painter = QPainter(pm)
                renderer.render(painter)
                painter.end()
                pm.setDevicePixelRatio(_ICON_DPR)
                _PIXMAP_CACHE[cache_key] = pm
                return QPixmap(pm)
        except Exception:
            pass

    _PIXMAP_CACHE[cache_key] = None
    return None

def load_icon(name: str, size: Tuple[int, int] = (16, 16), color: Optional[str] = None) -> Optional[QIcon]:
    """Load a QIcon from an SVG asset with optional tint color."""
    pm = render_pixmap(name, size, color)
    return QIcon(pm) if pm is not None else None

def get_asset_path(filename: str) -> str:
    """Get absolute path to an asset file in the assets directory."""
    return os.path.join(ASSETS_DIR, filename)
