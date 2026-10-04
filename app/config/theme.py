"""
Design tokens, color constants, typography system, and QSS stylesheet.
Theme: Modern Crisp White with Electric Royal Blue Brand Accents
"""

from string import Template

# ============================================
# TYPOGRAPHY SYSTEM
# ============================================

# Font Families
FONT_PRIMARY = "Inter"
FONT_UI = '"Inter", "Segoe UI Variable", "Segoe UI", -apple-system, "Helvetica Neue", Arial, sans-serif'
FONT_MONO = "JetBrains Mono"
FONT_CODE = '"JetBrains Mono", "Cascadia Code", "Consolas", "Courier New", monospace'
FONT_BRAND = "Space Grotesk"
FONT_DISPLAY = '"Space Grotesk", "Inter", sans-serif'

# Font Sizes (pixels)
FS_H1 = 32      # Display Large - Page titles
FS_H2 = 28      # Display Medium
FS_H3 = 24      # Heading Large - Card titles
FS_H4 = 20      # Heading Medium - Dialog titles
FS_H5 = 16      # Heading Small - Widget titles
FS_BODY_L = 14  # Body Large - Main content
FS_BODY_M = 13  # Body Medium - Secondary content
FS_BODY_S = 12  # Body Small - Helper text
FS_CAPTION = 11 # Captions
FS_TINY = 10    # Tiny text
FS_LABEL = 10   # Label eyebrows

# Font Weights
FW_REGULAR = 400
FW_MEDIUM = 500
FW_SEMIBOLD = 600
FW_BOLD = 700

# ============================================
# COLORS
# ============================================

# Primary Brand
PRIMARY = "#2563eb"
PRIMARY_HOVER = "#1d4ed8"
PRIMARY_LIGHT = "#eff6ff"
ACCENT = "#60a5fa"

# Backgrounds
BG_PRIMARY = "#ffffff"
BG_SECONDARY = "#f8fafc"
BG_TERTIARY = "#f1f5f9"

# Text
TEXT_PRIMARY = "#0f172a"
TEXT_SECONDARY = "#334155"
TEXT_MUTED = "#64748b"
TEXT_DIM = "#94a3b8"
TEXT_LIGHT = "#cbd5e1"

# Borders
BORDER_LIGHT = "#e2e8f0"
BORDER = BORDER_LIGHT
BORDER_DARK = "#94a3b8"
BORDER_DASHED = "#94a3b8"

# Semantic
SUCCESS = "#10b981"
WARNING = "#f59e0b"
ERROR = "#ef4444"
INFO = "#3b82f6"
DANGER = ERROR

# Brand Gradient Tokens
GRADIENT_START = "#38bdf8"
GRADIENT_END = "#2589ff"
GRADIENT_CSS = "qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #38bdf8, stop: 1 #2589ff)"
GRADIENT_CSS_HOVER = "qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #56ccf8, stop: 1 #3ca0ff)"
GRADIENT_CSS_PRESSED = "qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #0ea5e9, stop: 1 #0b63db)"

# Titlebar & Header Tokens (Solid clean background without gradient effect)
TITLEBAR_BG = "#ffffff"  # Crisp White for Windows native titlebar caption
TITLEBAR_GRADIENT_START = "#ffffff"
TITLEBAR_GRADIENT_END = "#ffffff"
TITLEBAR_BORDER = "#e2e8f0"
TITLEBAR_GRADIENT_QSS = "#ffffff"
TITLEBAR_TOP_GRADIENT = "#ffffff"

# Legacy Aliases (maintaining full backward compatibility)
BG_MAIN = BG_PRIMARY
BG_SURFACE = BG_SECONDARY
BG_CARD = BG_PRIMARY
BG_CARD_HOVER = BG_TERTIARY
BG_INPUT = BG_PRIMARY

TEXT_MAIN = TEXT_PRIMARY
BORDER_FOCUS = PRIMARY
BTN_DISABLED = BG_TERTIARY
BTN_DISABLED_BORDER = BORDER_LIGHT
BTN_DISABLED_TEXT = TEXT_DIM

ACCENT_BLUE = PRIMARY
ACCENT_HOVER = PRIMARY_HOVER
ACCENT_PRESSED = "#1e40af"
ACCENT_LIGHT = ACCENT
ACCENT_MUTED = "#3b82f6"

# ============================================
# SPACING SCALE (Base: 4px, Step: 4px)
# ============================================
SP_0 = 0
SP_1 = 4    # xs
SP_2 = 8    # sm
SP_3 = 12   # md
SP_4 = 16   # base
SP_6 = 24   # lg
SP_8 = 32   # xl
SP_12 = 48  # 2xl

# Shortcuts
SPACE_ICON_TO_TEXT = SP_2  # 8px
SPACE_FIELD_GAP = SP_3     # 12px
SPACE_SECTION = SP_6       # 24px
SPACE_CARD = SP_4          # 16px (padding)
SPACE_ELEMENT = SP_2       # 8px (between elements)

# ============================================
# PRE-MADE STYLESHEET TEMPLATES
# ============================================

def heading_style(text_color=TEXT_PRIMARY):
    return f"""
        color: {text_color};
        font-family: "{FONT_PRIMARY}";
        font-size: {FS_H4}px;
        font-weight: {FW_SEMIBOLD};
        line-height: 28px;
        background: transparent;
        border: none;
    """

def body_style(size=FS_BODY_L, color=TEXT_PRIMARY, weight=FW_REGULAR):
    return f"""
        color: {color};
        font-family: "{FONT_PRIMARY}";
        font-size: {size}px;
        font-weight: {weight};
        line-height: {int(size * 1.55)}px;
        background: transparent;
        border: none;
    """

def label_style(color=TEXT_DIM):
    return f"""
        color: {color};
        font-family: "{FONT_PRIMARY}";
        font-size: {FS_LABEL}px;
        font-weight: {FW_BOLD};
        letter-spacing: 0.8px;
        line-height: 14px;
        background: transparent;
        border: none;
    """

def card_style(radius=8, bg=BG_PRIMARY, border_color=BORDER_LIGHT):
    return f"""
        QFrame {{
            background-color: {bg};
            border: 1px solid {border_color};
            border-radius: {radius}px;
        }}
    """

def button_style(
    bg=PRIMARY,
    bg_hover=PRIMARY_HOVER,
    text_color="#ffffff",
    fs=FS_BODY_L,
    radius=6
):
    return f"""
        QPushButton {{
            color: {text_color};
            font-family: "{FONT_PRIMARY}";
            font-size: {fs}px;
            font-weight: {FW_SEMIBOLD};
            padding: 10px 16px;
            background-color: {bg};
            border: none;
            border-radius: {radius}px;
        }}
        QPushButton:hover {{
            background-color: {bg_hover};
        }}
        QPushButton:pressed {{
            background-color: {bg_hover};
            padding: 11px 15px 9px 17px;
        }}
        QPushButton:disabled {{
            background-color: {BG_TERTIARY};
            color: {TEXT_LIGHT};
        }}
    """

# ============================================
# LEGACY HELPER AND GLOBAL QSS
# ============================================

TYPE = {
    "title-lg":     dict(size=15,   weight=700, spacing="0px"),
    "title":        dict(size=13.5, weight=700, spacing="0px"),
    "body-strong":  dict(size=13,   weight=600, spacing="0px"),
    "body":         dict(size=12.5, weight=400, spacing="0px"),
    "subtext":      dict(size=11.5, weight=500, spacing="0px"),
    "caption":      dict(size=11,   weight=600, spacing="0px"),
    "caption-dim":  dict(size=11,   weight=400, spacing="0px"),
    "eyebrow":      dict(size=10,   weight=700, spacing="0.8px"),
    "micro":        dict(size=10,   weight=700, spacing="0px"),
}

def font_css(token: str, color: str = "", extra: str = "") -> str:
    """Generate inline stylesheet font rules for a typography token."""
    spec = TYPE.get(token, TYPE["body"])
    sz = spec["size"]
    size_str = f"{int(sz)}px" if isinstance(sz, (int, float)) and sz == int(sz) else f"{sz}px"
    rules = [
        f"font-size: {size_str};",
        f"font-weight: {spec['weight']};",
    ]
    if spec.get("spacing") and spec["spacing"] != "0px":
        rules.append(f"letter-spacing: {spec['spacing']};")
    if color:
        rules.append(f"color: {color};")
    if extra:
        rules.append(extra.strip())
    return " ".join(rules)

APP_QSS = Template("""
QMainWindow {
    background-color: $BG_MAIN;
}

QWidget {
    color: $TEXT_MAIN;
}

QLabel {
    background: transparent;
    border: none;
}

QToolTip {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: $FONT_UI;
    font-size: 12px;
    font-weight: 500;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 4px 8px;
}
""").substitute(
    BG_MAIN=BG_MAIN,
    TEXT_MAIN=TEXT_MAIN,
    FONT_UI=FONT_UI,
)
