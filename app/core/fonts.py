"""
Font discovery and application font loading for ContextPot.

Fixes vs. old version:
  * Never loads the Inter VARIABLE font together with the static Inter cuts
    (mixing them under one family makes Qt pick random weights/optical sizes).
  * Applies one clean default QFont, with no hinting, so glyph spacing stays even.
  * Exposes brand_family() so the wordmark can fall back to Inter safely.
"""
import os
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication
from app.core.icons import ASSETS_DIR

FONT_UI_FAMILY = "Inter"
FONT_BRAND_FAMILY = "Space Grotesk"
FONT_MONO_FAMILY = "JetBrains Mono"


def load_app_fonts():
    """Register bundled fonts from assets/fonts into QFontDatabase."""
    fonts_dir = os.path.join(ASSETS_DIR, "fonts")
    if not os.path.exists(fonts_dir):
        return
    for fname in sorted(os.listdir(fonts_dir)):
        low = fname.lower()
        if not low.endswith((".ttf", ".otf")):
            continue
        # Skip the Inter variable font: the static Regular/Medium/SemiBold/Bold
        # cuts are already bundled and conflict with it.
        if low.startswith("inter-variablefont"):
            continue
        QFontDatabase.addApplicationFont(os.path.join(fonts_dir, fname))


def brand_family() -> str:
    """Space Grotesk if it loaded, otherwise Inter."""
    return FONT_BRAND_FAMILY if FONT_BRAND_FAMILY in QFontDatabase.families() else FONT_UI_FAMILY


def apply_default_font(app: QApplication):
    """Call right after load_app_fonts() and before app.setStyleSheet()."""
    f = QFont(FONT_UI_FAMILY)
    f.setPixelSize(13)
    f.setWeight(QFont.Weight.Normal)
    f.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality)
    # No hinting = even letter spacing on Windows. If text ever looks slightly
    # soft on a 100% display, switch to PreferVerticalHinting.
    f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(f)


def make_font(family: str, px: int, weight: QFont.Weight = QFont.Weight.Normal,
              spacing_pct: float = 100.0) -> QFont:
    """Build a QFont with integer pixel size (QSS can't do fractional sizes or letter-spacing)."""
    f = QFont(family)
    f.setPixelSize(int(px))
    f.setWeight(weight)
    f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    f.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality)
    if spacing_pct != 100.0:
        f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, spacing_pct)
    return f
