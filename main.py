"""
ContextPot - Modern PySide6 UI Application
"""

import os
import sys
from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtWidgets import QApplication
from app.config.theme import APP_QSS, BG_CARD, BG_MAIN, TEXT_MAIN
from app.core.fonts import apply_default_font, load_app_fonts
from app.core.icons import ASSETS_DIR, get_asset_path, load_icon, render_pixmap
from app.core.runtime import runtime_info
from app.core.window_utils import setup_app_user_model_id
from app.views.main_window import MainWindow

def main():
    # Print runtime info for diagnostics
    info = runtime_info()
    print(f"[ContextPot] mode={info['mode']}  user_data={info['user_data_dir']}")

    # Setup native Windows app user model ID for proper taskbar grouping (MUST match installer AppUserModelID)
    setup_app_user_model_id("AbdulKarim.ContextPot.1.0")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("ContextPot")
    app.setApplicationDisplayName("")

    # Load bundled fonts (Inter, JetBrains Mono) before stylesheet is applied
    load_app_fonts()
    apply_default_font(app)

    app.setStyleSheet(APP_QSS)

    # Set application-level window icon for taskbar and dialogs (prefer native multi-size .ico)
    ico_path = get_asset_path("app_logo.ico")
    if os.path.exists(ico_path):
        app.setWindowIcon(QIcon(ico_path))
    else:
        app_icon = load_icon("app_logo", (64, 64))
        if app_icon and not app_icon.isNull():
            app.setWindowIcon(app_icon)

    # Standard dark palette fallback
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BG_MAIN))
    palette.setColor(QPalette.WindowText, QColor(TEXT_MAIN))
    palette.setColor(QPalette.Base, QColor(BG_CARD))
    palette.setColor(QPalette.Text, QColor(TEXT_MAIN))
    palette.setColor(QPalette.Button, QColor(BG_CARD))
    palette.setColor(QPalette.ButtonText, QColor(TEXT_MAIN))
    app.setPalette(palette)

    window = MainWindow()
    window.show_animated()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
