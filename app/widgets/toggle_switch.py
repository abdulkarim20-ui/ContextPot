from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget
from app.config.theme import ACCENT, BORDER_DASHED

class ToggleSwitch(QWidget):
    """
    Smooth pill-shaped toggle switch with brand gradient active styling (Light Mode).
    """
    toggled = Signal(bool)

    def __init__(self, checked: bool = False, on_toggle=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 20)
        self.setCursor(Qt.PointingHandCursor)
        self._checked = checked
        self._on_toggle = on_toggle
        self._thumb_pos = 18.0 if checked else 2.0
        self._anim = None

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool, emit_signal: bool = True):
        if self._checked != checked:
            self._checked = checked
            self._animate()
            if emit_signal:
                if self._on_toggle:
                    self._on_toggle(self._checked)
                self.toggled.emit(self._checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self._animate()
            if self._on_toggle:
                self._on_toggle(self._checked)
            self.toggled.emit(self._checked)
        super().mousePressEvent(event)

    def _animate(self):
        if self._anim is not None:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"thumb_pos")
        self._anim.setDuration(140)
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(18.0 if self._checked else 2.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

    def get_thumb_pos(self) -> float:
        return self._thumb_pos

    def set_thumb_pos(self, pos: float):
        self._thumb_pos = pos
        self.update()

    thumb_pos = Property(float, get_thumb_pos, set_thumb_pos)

    def paintEvent(self, event):
        p = QPainter(self)
        if not p.isActive():
            return
        p.setRenderHint(QPainter.Antialiasing)

        w, h = float(self.width()), float(self.height())
        r = h / 2.0

        p.setPen(Qt.NoPen)
        if self._checked:
            p.setBrush(QBrush(QColor("#2563eb")))
            p.drawRoundedRect(QRectF(0, 0, w, h), r, r)
            p.setBrush(QBrush(QColor("#ffffff")))
            p.drawEllipse(QRectF(self._thumb_pos, 2.0, 16.0, 16.0))
        else:
            # Calm, soft light-slate inactive track with subtle border
            p.setBrush(QBrush(QColor("#e2e8f0")))
            p.drawRoundedRect(QRectF(0, 0, w, h), r, r)
            # White thumb with soft border
            p.setPen(QPen(QColor("#cbd5e1"), 0.8))
            p.setBrush(QBrush(QColor("#ffffff")))
            p.drawEllipse(QRectF(self._thumb_pos, 2.0, 16.0, 16.0))
        p.end()
