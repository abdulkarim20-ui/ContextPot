import os
from typing import Optional
from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget
from app.core.icons import load_icon

class ToastNotification(QWidget):
    """
    Modern floating toast notification pill that slides up from the bottom:
    - Checkmark icon (emerald green #10b981)
    - Filename / feedback text
    - Smooth cubic slide & fade micro-animation
    - Auto-dismisses after 2.5 seconds
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedHeight(32)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 16, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignVCenter)

        # Checkmark icon
        self.icon_lbl = QLabel(self)
        self.icon_lbl.setFixedSize(14, 14)
        check_ic = load_icon("check", (14, 14), color="#10b981")
        if check_ic:
            self.icon_lbl.setPixmap(check_ic.pixmap(QSize(14, 14)))
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.icon_lbl)

        # Message label
        self.msg_lbl = QLabel(self)
        self.msg_lbl.setStyleSheet("""
            color: #ffffff;
            font-size: 12px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.msg_lbl)

        self._anim = None
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self.dismiss_animated)

        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dark pill background
        painter.setBrush(QBrush(QColor("#0f172a")))
        painter.setPen(QPen(QColor("#334155"), 1))
        rect = self.rect().adjusted(1, 1, -1, -1)
        radius = rect.height() / 2.0
        painter.drawRoundedRect(rect, radius, radius)

    def show_message(self, message: str, duration_ms: int = 2500):
        self.msg_lbl.setText(message)
        self.adjustSize()

        target_parent = self.parentWidget() or self.window()
        if target_parent:
            p_rect = target_parent.rect()
            text_width = self.msg_lbl.fontMetrics().boundingRect(message).width()
            w = max(190, text_width + 56)
            h = 32
            x = (p_rect.width() - w) // 2
            target_y = p_rect.height() - 48
            start_y = p_rect.height() - 15

            self.setGeometry(QRect(x, start_y, w, h))
            self.show()
            self.raise_()

            anim = QPropertyAnimation(self, b"pos", self)
            anim.setDuration(220)
            anim.setStartValue(QPoint(x, start_y))
            anim.setEndValue(QPoint(x, target_y))
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
            self._anim = anim

            self._dismiss_timer.start(duration_ms)

    def dismiss_animated(self):
        if not self.isVisible():
            return
        if self.parent():
            x = self.x()
            current_y = self.y()
            end_y = current_y + 25

            anim = QPropertyAnimation(self, b"pos", self)
            anim.setDuration(160)
            anim.setStartValue(QPoint(x, current_y))
            anim.setEndValue(QPoint(x, end_y))
            anim.setEasingCurve(QEasingCurve.InCubic)
            anim.finished.connect(self.hide)
            anim.start()
            self._anim = anim
        else:
            self.hide()
