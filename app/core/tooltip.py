from typing import Optional
from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QColor, QCursor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QWidget

_ACTIVE_POPUP: Optional["CustomTooltipPopup"] = None

def hide_active_tooltip():
    """Immediately dismiss any currently visible tooltip popup."""
    global _ACTIVE_POPUP
    if _ACTIVE_POPUP is not None:
        try:
            _ACTIVE_POPUP.hide()
        except Exception:
            pass
        _ACTIVE_POPUP = None

class CustomTooltipPopup(QFrame):
    """Modern floating tooltip popup with drop shadow and slide/fade micro-animation."""
    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.card = QFrame(self)
        self.card.setStyleSheet("""
            background-color: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 6px;
        """)
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(14)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 3)
        self.card.setGraphicsEffect(shadow)

        root = QHBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.addWidget(self.card)

        card_lay = QHBoxLayout(self.card)
        card_lay.setContentsMargins(8, 4, 8, 4)
        self.label = QLabel(text)
        self.label.setStyleSheet("color: #f8fafc; font-size: 12px; font-weight: 500; background: transparent; border: none;")
        card_lay.addWidget(self.label)
        self._anim = None

    def set_text(self, text: str):
        self.label.setText(text)
        self.adjustSize()

    def show_animated(self, target_pos: QPoint, slide_up: bool = True):
        global _ACTIVE_POPUP
        if _ACTIVE_POPUP is not None and _ACTIVE_POPUP is not self:
            try:
                _ACTIVE_POPUP.hide()
            except Exception:
                pass
        _ACTIVE_POPUP = self

        self.adjustSize()
        start_offset = 4 if slide_up else -4
        start_pos = QPoint(target_pos.x(), target_pos.y() + start_offset)
        self.move(start_pos)
        self.show()

        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(100)
        anim.setStartValue(start_pos)
        anim.setEndValue(target_pos)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._anim = anim

    def hide(self):
        global _ACTIVE_POPUP
        if _ACTIVE_POPUP is self:
            _ACTIVE_POPUP = None
        super().hide()


class TooltipFilter(QObject):
    """Event filter that manages showing and quickly dismissing custom tooltips."""
    def __init__(self, target: QWidget, text: str):
        super().__init__(target)
        self.target = target
        self.text = text
        self._popup: Optional[CustomTooltipPopup] = None

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._show)

    def set_text(self, text: str):
        self.text = text
        if self._popup:
            self._popup.set_text(text)

    def eventFilter(self, watched, event):
        target = getattr(self, "target", None)
        if target is not None and watched == target:
            e_type = event.type()
            if e_type == QEvent.Enter:
                if self.text:
                    self._timer.start()
            elif e_type in (
                QEvent.Leave,
                QEvent.MouseButtonPress,
                QEvent.MouseButtonRelease,
                QEvent.Hide,
                QEvent.WindowDeactivate,
                QEvent.FocusOut,
                QEvent.Wheel,
            ):
                self._timer.stop()
                if self._popup:
                    self._popup.hide()
            elif e_type == QEvent.MouseMove:
                if not self.target.underMouse():
                    self._timer.stop()
                    if self._popup:
                        self._popup.hide()
        return super().eventFilter(watched, event)

    def _show(self):
        if not self.target.isVisible() or not self.text or not self.target.underMouse():
            return
        if not self._popup:
            self._popup = CustomTooltipPopup(self.text, parent=self.target.window())
        else:
            self._popup.set_text(self.text)

        self._popup.adjustSize()
        rect = self.target.rect()
        center = self.target.mapToGlobal(rect.center())
        w = self._popup.sizeHint().width()
        x = int(center.x() - w / 2.0)
        y = self.target.mapToGlobal(rect.bottomLeft()).y() + 4
        self._popup.show_animated(QPoint(x, y), slide_up=True)


def attach_tooltip(widget: QWidget, text: str) -> TooltipFilter:
    """Attach or update modern animated tooltip on any widget without duplicates."""
    widget.setToolTip("")  # Ensure native Qt tooltip is suppressed
    if hasattr(widget, "_custom_tooltip_filter") and widget._custom_tooltip_filter:
        tf: TooltipFilter = widget._custom_tooltip_filter
        tf.set_text(text)
        return tf

    tf = TooltipFilter(widget, text)
    widget._custom_tooltip_filter = tf
    widget.installEventFilter(tf)
    return tf

