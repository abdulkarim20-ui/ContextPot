import os
import re
from typing import List, Optional
from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, QTimer, Qt, QByteArray
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget
from app.core.icons import get_asset_path, render_pixmap


class ZoomableFolderIconBox(QWidget):
    """
    Animated folder SVG icon displaying the character's eye animation from drag_drop.svg,
    with subtle micro-zoom on hover/drag-over and zero idle CPU when hidden.
    """
    _cached_frames: Optional[List[QPixmap]] = None

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(64, 52)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._scale_factor = 1.0
        self._anim = None
        self._fallback_pm = render_pixmap("drag_drop", (58, 45))

        self._frames = self._get_or_load_frames((58, 45), dpr=2.0)
        self._frame_idx = 0
        self._frame_dir = 1  # 1 for forward, -1 for alternate reverse

        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 FPS matching the 2.967s SVG animation cycle
        self._timer.timeout.connect(self._on_tick)

        if self._frames and len(self._frames) > 1 and self.isVisible():
            self._timer.start()

    @classmethod
    def _get_or_load_frames(cls, size=(58, 45), dpr=2.0) -> List[QPixmap]:
        if cls._cached_frames is not None:
            return cls._cached_frames

        svg_path = get_asset_path("drag_drop.svg")
        if not os.path.exists(svg_path):
            cls._cached_frames = []
            return cls._cached_frames

        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_raw = f.read()

            if "@keyframes oeil0{" not in svg_raw or "@keyframes oeil1{" not in svg_raw:
                cls._cached_frames = []
                return cls._cached_frames

            k0 = svg_raw.split("@keyframes oeil0{")[1].split("}@keyframes oeil1{")[0]
            k1 = svg_raw.split("@keyframes oeil1{")[1].split("}}")[0]

            entries0 = re.findall(r"matrix\(([\d\.\,\-]+)\)", k0)
            entries1 = re.findall(r"matrix\(([\d\.\,\-]+)\)", k1)

            if not entries0 or not entries1:
                cls._cached_frames = []
                return cls._cached_frames

            svg_base = """<svg xmlns="http://www.w3.org/2000/svg" width="220" height="170" viewBox="-110 -72 220 170">
  <defs>
    <filter id="folderShadow" x="-30%" y="-30%" width="160%" height="180%">
      <feDropShadow dx="0" dy="5" stdDeviation="6" flood-color="#3b93f0" flood-opacity=".16"/>
    </filter>
  </defs>
  <g filter="url(#folderShadow)">
    <path d="M-100 -38 C-100 -53 -91 -62 -76 -62 H-35 C-27 -62 -22 -59 -17 -53 L-6 -38 H78 C92 -38 101 -27 101 -13 V58 C101 75 90 86 74 86 H-75 C-91 86 -101 75 -101 58 V-28 C-101 -32 -101 -35 -100 -38Z" fill="#3b93f0"/>
    <path d="M-101 -17 C-101 -29 -92 -38 -80 -38 H79 C91 -38 101 -29 101 -17 V58 C101 75 90 86 74 86 H-75 C-91 86 -101 75 -101 58Z" fill="#3b93f0"/>
  </g>
  <g fill="#fff" transform="translate(0 42)">
    <path d="M-20 -8A20 20 0 0 1 0 -28L0 -28A20 20 0 0 1 20 -8L20 8A20 20 0 0 1 0 28L0 28A20 20 0 0 1 -20 8Z" transform="matrix({M0})"/>
    <path d="M-20 -8A20 20 0 0 1 0 -28L0 -28A20 20 0 0 1 20 -8L20 8A20 20 0 0 1 0 28L0 28A20 20 0 0 1 -20 8Z" transform="matrix({M1})"/>
  </g>
</svg>"""

            num_frames = min(len(entries0), len(entries1))
            pixel_w = int(size[0] * dpr)
            pixel_h = int(size[1] * dpr)

            frames = []
            for i in range(num_frames):
                m0 = entries0[i]
                m1 = entries1[i]
                svg_frame = svg_base.replace("{M0}", m0).replace("{M1}", m1)
                r = QSvgRenderer(QByteArray(svg_frame.encode("utf-8")))

                pm = QPixmap(pixel_w, pixel_h)
                pm.fill(Qt.transparent)

                p = QPainter(pm)
                p.setRenderHint(QPainter.Antialiasing, True)
                p.setRenderHint(QPainter.SmoothPixmapTransform, True)
                r.render(p, QRectF(0, 0, pixel_w, pixel_h))
                p.end()

                pm.setDevicePixelRatio(dpr)
                frames.append(pm)

            cls._cached_frames = frames
            return frames
        except Exception as e:
            cls._cached_frames = []
            return cls._cached_frames

    def _on_tick(self):
        if not self._frames:
            return
        self._frame_idx += self._frame_dir
        if self._frame_idx >= len(self._frames) - 1:
            self._frame_idx = len(self._frames) - 1
            self._frame_dir = -1
        elif self._frame_idx <= 0:
            self._frame_idx = 0
            self._frame_dir = 1
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if self._frames and len(self._frames) > 1 and not self._timer.isActive():
            self._timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._timer.isActive():
            self._timer.stop()

    def get_scale(self) -> float:
        return self._scale_factor

    def set_scale(self, val: float):
        self._scale_factor = val
        self.update()

    scale_factor = Property(float, get_scale, set_scale)

    def set_hovered(self, hovered: bool):
        target = 1.05 if hovered else 1.0
        if self._anim is not None:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"scale_factor")
        self._anim.setDuration(150)
        self._anim.setStartValue(self._scale_factor)
        self._anim.setEndValue(target)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

    def paintEvent(self, event):
        p = QPainter(self)
        if not p.isActive():
            return
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        cx = self.width() / 2.0
        cy = self.height() / 2.0

        p.translate(cx, cy)
        p.scale(self._scale_factor, self._scale_factor)
        p.translate(-cx, -cy)

        pm = None
        if self._frames and 0 <= self._frame_idx < len(self._frames):
            pm = self._frames[self._frame_idx]
        elif self._fallback_pm and not self._fallback_pm.isNull():
            pm = self._fallback_pm

        if pm and not pm.isNull():
            dpr = pm.devicePixelRatio() or 1.0
            pw = pm.width() / dpr
            ph = pm.height() / dpr
            ix = (self.width() - pw) / 2.0
            iy = (self.height() - ph) / 2.0
            p.drawPixmap(int(ix), int(iy), pm)

        p.end()
