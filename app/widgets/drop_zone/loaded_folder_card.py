from typing import Any, Dict
from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from app.config.theme import (
    BG_TERTIARY,
    BORDER,
    FONT_PRIMARY,
    FS_BODY_L,
    FS_CAPTION,
    FW_REGULAR,
    FW_SEMIBOLD,
    PRIMARY,
    SUCCESS,
    TEXT_MAIN,
    TEXT_MUTED,
    TEXT_PRIMARY,
)
from app.core.icons import load_icon, render_pixmap
from app.core.tooltip import attach_tooltip
from app.widgets.project_identity_badge import ProjectIdentityBadge

class StatusIndicatorWidget(QWidget):
    """
    Dedicated crisp status indicator drawing either an anti-aliased dot or checkmark,
    guaranteeing 100% horizontal and vertical alignment with the text.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(11, 11)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._mode = "dot"  # "dot" or "check"
        self._color = QColor("#16a34a")

    def set_dot(self, color_hex: str):
        self._mode = "dot"
        self._color = QColor(color_hex)
        self.update()

    def set_check(self, color_hex: str = "#16a34a"):
        self._mode = "check"
        self._color = QColor(color_hex)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.Antialiasing, True)

        if self._mode == "dot":
            painter.setBrush(self._color)
            painter.setPen(Qt.NoPen)
            # Centered 5.5px dot inside 11x11 box
            painter.drawEllipse(QRectF(2.5, 2.5, 6.0, 6.0))
        elif self._mode == "check":
            pen = QPen(self._color, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            # Crisp checkmark: (1.8, 5.5) -> (4.4, 8.2) -> (9.2, 2.8)
            painter.drawLine(QPointF(1.8, 5.5), QPointF(4.4, 8.2))
            painter.drawLine(QPointF(4.4, 8.2), QPointF(9.2, 2.8))

        painter.end()


class LoadedFolderCard(QFrame):
    """
    Elevated card chip showing loaded repository details:
    Folder Icon Chip, Name, Language Badge, Stats, Real-Time Smooth Progress Bar,
    Aligned Status Indicator (with live dot & analyzing animation),
    and Remove (x) Button.
    """
    remove_clicked = Signal()
    open_explorer_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LoadedFolderCard")
        self.setFixedSize(312, 88)
        self.setStyleSheet(f"""
            QFrame#LoadedFolderCard {{
                background-color: #ffffff;
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        self._full_project_name = "Project"

        # Ellipsis timer for analyzing state
        self._dots_timer = QTimer(self)
        self._dots_timer.setInterval(320)
        self._dots_timer.timeout.connect(self._on_dots_tick)
        self._dots_step = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(10)

        # 1. Left Folder Icon Box (Light blue tinted rounded chip)
        self.icon_box = QFrame()
        self.icon_box.setFixedSize(44, 44)
        self.icon_box.setStyleSheet("""
            QFrame {
                background-color: #eff6ff;
                border: 1px solid #dbeafe;
                border-radius: 9px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        ib_lay = QVBoxLayout(self.icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ib_lay.setAlignment(Qt.AlignCenter)

        self.folder_icon_lbl = QLabel()
        self.folder_icon_lbl.setAlignment(Qt.AlignCenter)
        self.folder_icon_lbl.setStyleSheet("background: transparent; border: none;")
        pm = render_pixmap("loaded_folder", (30, 30))
        if pm:
            self.folder_icon_lbl.setPixmap(pm)

        ib_lay.addWidget(self.folder_icon_lbl)
        layout.addWidget(self.icon_box)

        # 2. Middle Info Column (Folder name, stats, progress bar, status)
        info_col = QVBoxLayout()
        info_col.setContentsMargins(0, 0, 0, 0)
        info_col.setSpacing(2)
        info_col.setAlignment(Qt.AlignVCenter)

        # Row 1: Title + Language Tag
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(6)
        title_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.name_lbl = QLabel("Project")
        self.name_lbl.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-family: "{FONT_PRIMARY}";
            font-size: {FS_BODY_L}px;
            font-weight: {FW_SEMIBOLD};
            background: transparent;
            border: none;
        """)
        title_row.addWidget(self.name_lbl)

        self.project_identity = ProjectIdentityBadge(parent=self)
        self.project_identity.hide()
        self.lang_badge = self.project_identity
        title_row.addWidget(self.project_identity)
        title_row.addStretch(1)
        info_col.addLayout(title_row)

        # Row 2: Stats (files · folders · size)
        self.stats_lbl = QLabel("0 files · 0 folders · 0 kb")
        self.stats_lbl.setStyleSheet(f"""
            color: {TEXT_MUTED};
            font-family: "{FONT_PRIMARY}";
            font-size: {FS_CAPTION}px;
            font-weight: {FW_REGULAR};
            background: transparent;
            border: none;
        """)
        info_col.addWidget(self.stats_lbl)

        # Row 3: Modern 4px Slim Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {BG_TERTIARY};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {PRIMARY};
                border-radius: 2px;
            }}
        """)
        self.progress_bar.hide()
        info_col.addWidget(self.progress_bar)

        # Row 4: Status Row with Aligned Indicator Dot + High Contrast Status Label
        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(5)
        status_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.status_indicator = StatusIndicatorWidget(self)
        self.status_indicator.set_dot(SUCCESS)
        status_row.addWidget(self.status_indicator)

        self.status_text_lbl = QLabel("Ready to scan", self)
        self.status_text_lbl.setStyleSheet(f"""
            color: {SUCCESS};
            font-family: "{FONT_PRIMARY}";
            font-size: {FS_CAPTION}px;
            font-weight: {FW_SEMIBOLD};
            background: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
        """)
        status_row.addWidget(self.status_text_lbl)
        status_row.addStretch(1)
        info_col.addLayout(status_row)

        layout.addLayout(info_col, 1)

        # 3. Top-Right Remove/Clear Button (x.svg)
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setAlignment(Qt.AlignTop | Qt.AlignRight)

        self.remove_btn = QPushButton()
        self.remove_btn.setFixedSize(18, 18)
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        x_icon = load_icon("x", (10, 10), color=TEXT_MUTED)
        if x_icon:
            self.remove_btn.setIcon(x_icon)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #f1f5f9;
            }
            QPushButton:pressed {
                background: #e2e8f0;
            }
        """)
        attach_tooltip(self.remove_btn, "Remove repository")
        self.remove_btn.clicked.connect(self.remove_clicked.emit)
        right_col.addWidget(self.remove_btn)

        layout.addLayout(right_col)

    def _on_dots_tick(self):
        """Cycle animated ellipsis during background folder analysis."""
        self._dots_step = (self._dots_step + 1) % 4
        dots = "." * self._dots_step
        self.status_text_lbl.setText(f"Analyzing folder{dots}")

    def _start_analyzing_animation(self):
        self._dots_step = 1
        self.progress_bar.hide()
        self.status_indicator.set_dot("#2563eb")
        self.status_text_lbl.setText("Analyzing folder.")
        self.status_text_lbl.setStyleSheet(
            "color: #2563eb; font-size: 11px; font-weight: 600; "
            "background: transparent; border: none; padding: 0px; margin: 0px;"
        )
        self.status_text_lbl.show()
        self.status_indicator.show()
        if not self._dots_timer.isActive():
            self._dots_timer.start(260)

    def _stop_analyzing_animation(self):
        if self._dots_timer.isActive():
            self._dots_timer.stop()

    def enterEvent(self, event):
        p = self.parent()
        if p and hasattr(p, "_on_child_hover"):
            p._on_child_hover(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        p = self.parent()
        if p and hasattr(p, "_on_child_hover"):
            p._on_child_hover(False)
        super().leaveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_title_elision()

    def showEvent(self, event):
        super().showEvent(event)
        self._update_title_elision()

    def _update_title_elision(self):
        """
        Dynamically elide long project folder names using '...' so that the
        ProjectIdentityBadge and remove button never collide or get pushed off-card.
        """
        full_name = getattr(self, "_full_project_name", "") or self.name_lbl.text()
        if not full_name:
            return

        card_w = self.width() if 100 <= self.width() <= 350 else 312
        # Deduct icon box (44), remove btn (18), margins (10+10=20), and layout spacings (10+10=20)
        avail_info_w = card_w - 44 - 18 - 20 - 20  # ~210px

        badge_w = 0
        if hasattr(self, "project_identity") and self.project_identity.isVisible():
            badge_w = self.project_identity.width()
            if badge_w <= 0:
                badge_w = self.project_identity.sizeHint().width()
            if badge_w <= 0:
                badge_w = 80

        spacing = 6 if badge_w > 0 else 0
        # Allow extra breathing space when badge is visible so it never crowds the remove button
        safety_margin = 6 if badge_w > 0 else 0
        max_title_w = max(40, avail_info_w - badge_w - spacing - safety_margin)

        fm = self.name_lbl.fontMetrics()
        full_text_w = fm.horizontalAdvance(full_name)

        if full_text_w > max_title_w:
            elided = fm.elidedText(full_name, Qt.ElideRight, max_title_w)
            self.name_lbl.setText(elided)
            attach_tooltip(self.name_lbl, full_name)
        else:
            self.name_lbl.setText(full_name)
            attach_tooltip(self.name_lbl, "")

    def set_data(self, data: Dict[str, Any]):
        """
        Update the loaded-folder card atomically.
        Project identity is only revealed after scanning completes.
        This prevents Unknown -> Python -> Unknown flicker while the background scanner is still running.
        """
        self._full_project_name = data.get("name", "Project")
        self.name_lbl.setText(self._full_project_name)
        status = data.get("status", "Ready to scan")

        # --------------------------------------------------------
        # ANALYZING
        # --------------------------------------------------------
        if status.startswith("Analyzing"):
            # Do not change project identity while the scan is still producing the tree.
            self.project_identity.hide()
            self.stats_lbl.setText("Calculating…")
            self._start_analyzing_animation()
            self._update_title_elision()
            return

        # --------------------------------------------------------
        # SCANNING
        # --------------------------------------------------------
        if status.startswith("Scanning"):
            # Keep identity hidden until the final scan result.
            self.project_identity.hide()
            self._start_analyzing_animation()
            self._update_title_elision()
            return

        # --------------------------------------------------------
        # COMPLETED
        # --------------------------------------------------------
        if status == "Scan completed":
            identity = data.get("project_identity")
            if identity:
                self.project_identity.set_identity(identity)
                self.project_identity.show()
            elif "language" in data:
                self.project_identity.set_language(data["language"])
                self.project_identity.show()
            else:
                self.project_identity.hide()
            files = data.get("files", 0)
            folders = data.get("folders", 0)
            size_str = data.get("size_str", "0 kb")
            self.stats_lbl.setText(f"{files} files · {folders} folders · {size_str}")
            self._stop_analyzing_animation()
            self.finish_progress()
            self._update_title_elision()
            return

        # --------------------------------------------------------
        # READY / OTHER
        # --------------------------------------------------------
        self.project_identity.hide()
        files = data.get("files", 0)
        folders = data.get("folders", 0)
        size_str = data.get("size_str", "0 kb")
        self.stats_lbl.setText(f"{files} files · {folders} folders · {size_str}")
        self._stop_analyzing_animation()
        self.reset_progress(status)
        self._update_title_elision()

    def start_progress(self):
        """Prepare UI for scanning."""
        self._stop_analyzing_animation()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        self.status_indicator.set_dot("#2589ff")
        self.status_text_lbl.setText("Scanning...")
        self.status_text_lbl.setStyleSheet("color: #2589ff; font-size: 11px; font-weight: 600; background: transparent; border: none; padding: 0px; margin: 0px;")

    def update_progress(self, current: int, total: int, filename: str = ""):
        """Update progress live count."""
        self._stop_analyzing_animation()
        if total > 0:
            percent = min(100, int((current / total) * 100))
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percent)
            self.status_text_lbl.setText(f"Scanning... {percent}% ({current}/{total})")
        else:
            self.progress_bar.setRange(0, 0)
            self.status_text_lbl.setText(f"Scanning... {current} files")

        if not self.progress_bar.isVisible():
            self.progress_bar.show()

        self.status_indicator.set_dot("#2589ff")
        self.status_text_lbl.setStyleSheet("color: #2589ff; font-size: 11px; font-weight: 600; background: transparent; border: none; padding: 0px; margin: 0px;")

    def set_paused(self, paused: bool):
        """Show paused state visual cue."""
        self._stop_analyzing_animation()
        if paused:
            self.status_indicator.set_dot("#d97706")
            self.status_text_lbl.setText("Paused - Click Resume")
            self.status_text_lbl.setStyleSheet("color: #d97706; font-size: 11px; font-weight: 600; background: transparent; border: none; padding: 0px; margin: 0px;")
        else:
            self.status_indicator.set_dot("#2589ff")
            self.status_text_lbl.setText("Scanning...")
            self.status_text_lbl.setStyleSheet("color: #2589ff; font-size: 11px; font-weight: 600; background: transparent; border: none; padding: 0px; margin: 0px;")

    def finish_progress(self):
        """Mark scan completed with clean green checkmark icon."""
        self._stop_analyzing_animation()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.hide()
        self.status_indicator.set_check("#16a34a")
        self.status_text_lbl.setText("Scan completed")
        self.status_text_lbl.setStyleSheet("color: #16a34a; font-size: 11px; font-weight: 600; background: transparent; border: none; padding: 0px; margin: 0px;")

    def reset_progress(self, status_text: str = "Ready to scan"):
        """Reset progress back to idle ready or error state."""
        self._stop_analyzing_animation()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        is_error = "fail" in status_text.lower() or "error" in status_text.lower()
        color = "#ef4444" if is_error else "#16a34a"
        self.status_indicator.set_dot(color)
        self.status_text_lbl.setText(status_text)
        self.status_text_lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 600; background: transparent; border: none; padding: 0px; margin: 0px;")
