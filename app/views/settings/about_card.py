from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
)
from app.config.theme import BORDER, TEXT_MAIN, TEXT_MUTED
from app.core.fonts import FONT_UI_FAMILY, brand_family, make_font
from app.core.icons import render_pixmap
from app.core.tooltip import attach_tooltip


class AboutSocialButton(QToolButton):
    """Social icon button for GitHub and LinkedIn in the About section (Light Mode)."""
    def __init__(self, icon_name: str, url: str, tooltip: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.setFixedSize(28, 28)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setAutoRaise(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)

        self._pm_normal = render_pixmap(icon_name, (15, 15), color="#64748b")
        self._pm_hover = render_pixmap(icon_name, (15, 15), color="#2563eb")

        self.setIconSize(QSize(15, 15))
        attach_tooltip(self, tooltip)
        self._update_style(hovered=False)
        self.clicked.connect(self._open)

    def _update_style(self, hovered: bool):
        pm = self._pm_hover if hovered else self._pm_normal
        if pm:
            self.setIcon(QIcon(pm))

        if hovered:
            self.setStyleSheet("""
                QToolButton {
                    background-color: #eff6ff;
                    border: 1px solid #93c5fd;
                    border-radius: 6px;
                    padding: 0px;
                }
            """)
        else:
            self.setStyleSheet("""
                QToolButton {
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 0px;
                }
            """)

    def enterEvent(self, event):
        self._update_style(hovered=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._update_style(hovered=False)
        super().leaveEvent(event)

    def _open(self):
        url_str = self.url.strip()
        if not url_str:
            return
        if not (url_str.startswith("http://") or url_str.startswith("https://")):
            url_str = "https://" + url_str
        QDesktopServices.openUrl(QUrl(url_str))


class AboutCard(QFrame):
    """
    About card:
    - Left: wordmark 'ContextPot' (UI font 13px DemiBold matching preferences titles), version badge, creator line.
    - Right: GitHub + LinkedIn buttons.
    Fonts are set through QFont (not QSS) so size, weight and letter spacing are exact.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AboutCard")
        self.setFixedHeight(72)
        self.setStyleSheet(f"""
            QFrame#AboutCard {{
                background-color: #ffffff;
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 14, 0)
        layout.setSpacing(12)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(3)
        left_col.setAlignment(Qt.AlignVCenter)

        # --- Row 1: name + version badge (both vertically centered, fixed heights) ---
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)
        top_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.name_lbl = QLabel("ContextPot")
        self.name_lbl.setFont(make_font(FONT_UI_FAMILY, 13, QFont.Weight.DemiBold))
        self.name_lbl.setFixedHeight(20)
        self.name_lbl.setStyleSheet(f"color: {TEXT_MAIN};")
        top_row.addWidget(self.name_lbl, 0, Qt.AlignVCenter)

        self.version_lbl = QLabel("1.0.0")
        self.version_lbl.setFont(make_font(FONT_UI_FAMILY, 10, QFont.Weight.DemiBold, 102.0))
        self.version_lbl.setAlignment(Qt.AlignCenter)
        self.version_lbl.setFixedHeight(18)
        self.version_lbl.setStyleSheet("""
            color: #2563eb;
            background-color: #eff6ff;
            border: 1px solid #dbeafe;
            border-radius: 5px;
            padding: 0px 7px;
        """)
        top_row.addWidget(self.version_lbl, 0, Qt.AlignVCenter)
        top_row.addStretch(1)
        left_col.addLayout(top_row)

        # --- Row 2: creator (two labels so each gets its own exact font) ---
        creator_row = QHBoxLayout()
        creator_row.setContentsMargins(0, 0, 0, 0)
        creator_row.setSpacing(4)
        creator_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        creator_key = QLabel("Creator")
        creator_key.setFont(make_font(FONT_UI_FAMILY, 12, QFont.Weight.Normal))
        creator_key.setStyleSheet(f"color: {TEXT_MUTED};")
        creator_row.addWidget(creator_key)

        self.creator_lbl = QLabel("AbdulKarim")
        self.creator_lbl.setFont(make_font(FONT_UI_FAMILY, 12, QFont.Weight.DemiBold))
        self.creator_lbl.setStyleSheet(f"color: {TEXT_MAIN};")
        creator_row.addWidget(self.creator_lbl)
        creator_row.addStretch(1)
        left_col.addLayout(creator_row)

        layout.addLayout(left_col, 1)

        # --- Right: social buttons ---
        social_row = QHBoxLayout()
        social_row.setContentsMargins(0, 0, 0, 0)
        social_row.setSpacing(6)
        social_row.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.gh_btn = AboutSocialButton(
            "github",
            "https://github.com/abdulkarim20-ui",
            "GitHub: abdulkarim20-ui",
            parent=self,
        )
        self.li_btn = AboutSocialButton(
            "linkedin",
            "https://www.linkedin.com/in/abdulkarim27",
            "LinkedIn: abdulkarim27",
            parent=self,
        )
        social_row.addWidget(self.gh_btn)
        social_row.addWidget(self.li_btn)
        layout.addLayout(social_row)
