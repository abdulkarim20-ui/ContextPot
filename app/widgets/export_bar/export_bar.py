from PySide6.QtCore import QEasingCurve, QRect, QSize, Qt, QVariantAnimation, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
)
from app.config.theme import (
    ACCENT_PRESSED,
    PRIMARY,
    PRIMARY_HOVER,
)
from app.core.icons import render_pixmap
from app.core.tooltip import attach_tooltip
from app.widgets.export_bar.export_dropdown_pill import ExportDropdownPill


class ShimmerExportButton(QPushButton):
    """
    Solid royal blue Export button with a smooth, slow luminous shimmer sweep
    across the text when clicked.
    """
    def __init__(self, parent=None):
        super().__init__("Export", parent)
        self.setFixedSize(108, 32)
        self.setCursor(Qt.PointingHandCursor)
        self._shimmer_progress: float = -1.0
        self._is_shimmering: bool = False
        self._cycle_duration_ms: int = 450
        self._anim: QVariantAnimation | None = None
        self._icon_pm = render_pixmap("export_btn", (14, 14), color="#ffffff")
        attach_tooltip(self, "Export repository structure")

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.update()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.update()

    def start_shimmer(self, cycle_duration_ms: int = 450):
        """Start a quick, continuous shimmer loop across the Export button until stop_shimmer() is called."""
        self._is_shimmering = True
        self._cycle_duration_ms = cycle_duration_ms
        self._run_shimmer_cycle()

    def _run_shimmer_cycle(self):
        if not self._is_shimmering:
            self._shimmer_progress = -1.0
            self.update()
            return

        if self._anim and self._anim.state() == QVariantAnimation.Running:
            self._anim.stop()

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(self._cycle_duration_ms)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Linear)

        def _on_step(v):
            if self._is_shimmering:
                self._shimmer_progress = float(v)
                self.update()

        def _on_finish():
            if self._is_shimmering:
                self._run_shimmer_cycle()
            else:
                self._shimmer_progress = -1.0
                self.update()

        self._anim.valueChanged.connect(_on_step)
        self._anim.finished.connect(_on_finish)
        self._anim.start()

    def stop_shimmer(self):
        """Stop the shimmer effect immediately and restore solid royal blue state."""
        self._is_shimmering = False
        if self._anim and self._anim.state() == QVariantAnimation.Running:
            self._anim.stop()
        self._shimmer_progress = -1.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.TextAntialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # 1. Background Pill: ALWAYS solid royal blue in normal state (never light/washed out)
        if not self.isEnabled():
            bg = QColor("#e2e8f0")
        elif self.isDown():
            bg = QColor(ACCENT_PRESSED)  # Deep blue on press
        elif self.underMouse():
            bg = QColor(PRIMARY_HOVER)   # Rich dark blue on hover
        else:
            bg = QColor(PRIMARY)         # Standard state: ALWAYS solid royal blue (#2563eb)

        p.setBrush(QBrush(bg))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.rect(), 16, 16)

        # 2. Quick Luminous Sheen across the button pill
        if self._shimmer_progress >= 0.0 and self.isEnabled():
            p_val = self._shimmer_progress
            sheen_w = self.width() * 0.5
            cx = (self.width() + sheen_w * 2) * p_val - sheen_w
            pill_grad = QLinearGradient(cx - sheen_w / 2, 0, cx + sheen_w / 2, 0)
            pill_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
            pill_grad.setColorAt(0.5, QColor(255, 255, 255, 50))
            pill_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(QBrush(pill_grad))
            p.drawRoundedRect(self.rect(), 16, 16)

        # 3. Typography & Measurement
        font = QFont("Inter")
        font.setPixelSize(12)
        font.setWeight(QFont.Bold)
        p.setFont(font)
        fm = QFontMetrics(font)

        text = self.text()
        text_w = fm.horizontalAdvance(text)
        icon_w = 14
        spacing = 6
        total_w = icon_w + spacing + text_w
        start_x = (self.width() - total_w) // 2

        # 4. Draw Export Icon
        icon_y = (self.height() - 14) // 2
        if self._icon_pm and not self._icon_pm.isNull():
            p.drawPixmap(start_x, icon_y, 14, 14, self._icon_pm)

        # 5. Draw Text with quick luminous Shimmer sweep on click
        text_x = start_x + icon_w + spacing
        text_rect = QRect(text_x, 0, text_w + 4, self.height())

        if self._shimmer_progress >= 0.0 and self.isEnabled():
            p_val = self._shimmer_progress
            cx = (p_val * 1.8) - 0.4
            half_w = 0.28

            stops = [(0.0, QColor(255, 255, 255, 150))]
            p_left = cx - half_w
            if 0.0 < p_left < 1.0:
                stops.append((p_left, QColor(255, 255, 255, 150)))
            p_mid = cx
            if 0.0 < p_mid < 1.0:
                stops.append((p_mid, QColor(255, 255, 255, 255)))
            p_right = cx + half_w
            if 0.0 < p_right < 1.0:
                stops.append((p_right, QColor(255, 255, 255, 150)))
            stops.append((1.0, QColor(255, 255, 255, 150)))
            stops.sort(key=lambda s: s[0])

            grad = QLinearGradient(text_x, 0, text_x + text_w, 0)
            last_pos = -1.0
            for pos, col in stops:
                pos = max(0.0, min(1.0, pos))
                if pos > last_pos:
                    grad.setColorAt(pos, col)
                    last_pos = pos

            p.setPen(QPen(QBrush(grad), 1))
        else:
            txt_color = QColor("#94a3b8") if not self.isEnabled() else QColor("#ffffff")
            p.setPen(QPen(txt_color))

        p.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, text)
        p.end()


class ExportBar(QFrame):
    """
    Modular Export Footer Bar matching the exact design specification:
    - Left: Custom interactive pill dropdown with rotating chevron and rich floating popup card.
    - Right: Electric royal blue Export button (always blue) with quick text & button shimmer animation on click.
    """
    export_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ExportBar")
        self.setFixedHeight(36)
        self.setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Left: Custom Pill Dropdown
        self.dropdown_pill = ExportDropdownPill(default_mode="Whole code + Tree", parent=self)
        layout.addWidget(self.dropdown_pill, 1)

        # 2. Right: Blue Pill Export Action Button (Always Solid Blue + Quick Shimmer on Click)
        self.export_btn = ShimmerExportButton(parent=self)
        self.export_btn.clicked.connect(self._on_export_clicked)
        layout.addWidget(self.export_btn)

    def _on_export_clicked(self):
        if self.export_btn._is_shimmering:
            return
        self.export_btn.start_shimmer()
        selected_mode = self.dropdown_pill.get_mode()
        self.export_clicked.emit(selected_mode)

    def get_selected_option(self) -> str:
        return self.dropdown_pill.get_mode()
