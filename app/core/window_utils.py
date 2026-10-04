import sys
from PySide6.QtGui import QColor

def setup_app_user_model_id(app_id: str = "AbdulKarim.ContextPot.1.0") -> None:
    """Ensure Windows taskbar groups icons under this explicit app ID and enforce light title bar for dialogs."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass

        # Force Windows native file dialogs ("Select Repository or Project Folder") to use crisp White title bars
        try:
            import ctypes
            uxtheme = ctypes.windll.uxtheme
            try:
                # Ordinal 135: SetPreferredAppMode (3 = ForceLight)
                uxtheme[135](3)
            except Exception:
                pass
            try:
                # Ordinal 132: AllowDarkModeForApp (False = Disable dark title bar for dialogs)
                uxtheme[132](False)
            except Exception:
                pass
        except Exception:
            pass

def apply_native_title_bar(window, bg_hex: str = "#ffffff", text_hex: str = "#0f172a", border_hex: str = "#e2e8f0", dark_mode: bool = False) -> None:
    """
    Apply native DWM title bar styling, seamless caption background, Win11 rounded corners,
    and a unified outer perimeter window border (supporting both Light and Dark modes).
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = int(window.winId())
        if not hwnd:
            return

        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWA_BORDER_COLOR = 34
        DWMWA_CAPTION_COLOR = 35
        DWMWA_TEXT_COLOR = 36

        # 1. Native Light / Dark Mode Buttons (0 = Light mode with dark glyphs, 1 = Dark mode)
        dwm_dark = ctypes.c_int(1 if dark_mode else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(dwm_dark), ctypes.sizeof(dwm_dark)
        )

        # 2. Modern Windows 11 Rounded Corners (2 = DWMWCP_ROUND)
        corner_pref = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(corner_pref), ctypes.sizeof(corner_pref)
        )

        # 3. Caption Background (Converted to Win32 COLORREF 0x00BBGGRR format)
        qc = QColor(bg_hex)
        caption_color = ctypes.c_int((qc.blue() << 16) | (qc.green() << 8) | qc.red())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(caption_color), ctypes.sizeof(caption_color)
        )

        # 4. Caption Text Color
        qt = QColor(text_hex)
        text_color = ctypes.c_int((qt.blue() << 16) | (qt.green() << 8) | qt.red())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_TEXT_COLOR, ctypes.byref(text_color), ctypes.sizeof(text_color)
        )

        # 5. Unified Outer Window Perimeter Border Color (around title bar & window edges)
        qb = QColor(border_hex)
        border_color = ctypes.c_int((qb.blue() << 16) | (qb.green() << 8) | qb.red())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_BORDER_COLOR, ctypes.byref(border_color), ctypes.sizeof(border_color)
        )

        # 6. Smooth Native Animation Fix (Remove WS_POPUP bit)
        try:
            GWL_STYLE = -16
            WS_POPUP = 0x80000000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            if style & WS_POPUP:
                new_style = style & ~WS_POPUP
                if new_style >= 0x80000000:
                    new_style -= 0x100000000
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, ctypes.c_long(new_style))
                SWP_FLAGS = 0x0002 | 0x0001 | 0x0004 | 0x0020 | 0x0010
                ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_FLAGS)
        except Exception:
            pass

        window._dark_titlebar_applied = True
    except Exception:
        pass

# Alias for backwards compatibility
apply_dark_title_bar = apply_native_title_bar

def toggle_always_on_top(window, enable: bool) -> None:
    """Toggle Always-on-Top without destroying or recreating native window handles."""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            hwnd = wintypes.HWND(int(window.winId()))
            HWND_TOPMOST = ctypes.c_void_p(-1)
            HWND_NOTOPMOST = ctypes.c_void_p(-2)
            flags = 0x0002 | 0x0001 | 0x0010  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
            ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST if enable else HWND_NOTOPMOST, 0, 0, 0, 0, flags)
            return
        except Exception:
            pass
    from PySide6.QtCore import Qt
    window.setWindowFlag(Qt.WindowStaysOnTopHint, enable)
    window.show()

def watch_and_style_dialog_white(expected_title_part: str = "") -> None:
    """
    Spawns a fast lightweight background watcher that intercepts the native
    Windows IFileOpenDialog and enforces a crisp White DWM title bar (Light Mode).

    Strategy:
      - Poll at 5 ms intervals for up to 2 seconds looking for new top-level
        windows owned by this process.
      - Match by title (case-insensitive substring) OR by window class name
        (IFileDialog on Win10/11 appears as 'NativeHWNDHost').
      - Once found, keep re-applying every 50 ms for the entire dialog lifetime
        so that Windows cannot revert the styling.
    """
    if sys.platform != "win32":
        return

    import os
    import time
    import threading
    import ctypes
    from ctypes import wintypes

    my_pid = os.getpid()
    dwmapi = ctypes.windll.dwmapi
    user32  = ctypes.windll.user32

    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    DWMWA_BORDER_COLOR  = 34
    DWMWA_CAPTION_COLOR = 35
    DWMWA_TEXT_COLOR    = 36

    # Colors as Windows COLORREF (0x00BBGGRR)
    # #ffffff  → white title bar
    c_dark   = ctypes.c_int(0)
    c_cap    = ctypes.c_int(0x00FFFFFF)   # White   (#ffffff)  R=FF G=FF B=FF
    c_text   = ctypes.c_int(0x002A170F)   # Slate-900 (#0f172a) in COLORREF: B=2a G=17 R=0f
    c_border = ctypes.c_int(0x00F0E8E2)   # Slate-200 (#e2e8f0) in COLORREF: B=f0 G=e8 R=e2

    # Window classes used by Windows IFileOpenDialog (Win10/11) and classic #32770 dialogs
    DIALOG_CLASSES = frozenset({"NativeHWNDHost", "#32770", "bosa_sdm_msWord"})

    def apply_to_hwnd(h: int) -> None:
        try:
            dwmapi.DwmSetWindowAttribute(h, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(c_dark),   ctypes.sizeof(c_dark))
            dwmapi.DwmSetWindowAttribute(h, DWMWA_CAPTION_COLOR,           ctypes.byref(c_cap),    ctypes.sizeof(c_cap))
            dwmapi.DwmSetWindowAttribute(h, DWMWA_TEXT_COLOR,              ctypes.byref(c_text),   ctypes.sizeof(c_text))
            dwmapi.DwmSetWindowAttribute(h, DWMWA_BORDER_COLOR,            ctypes.byref(c_border), ctypes.sizeof(c_border))
        except Exception:
            pass

    def get_window_class(hwnd: int) -> str:
        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, 256)
        return buf.value

    def get_window_title(hwnd: int) -> str:
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value

    def worker() -> None:
        applied_hwnds: set = set()
        title_lower = expected_title_part.lower() if expected_title_part else ""

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def enum_proc(hwnd, _lParam):
            # Must belong to our process and be visible
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value != my_pid:
                return True
            if not user32.IsWindowVisible(hwnd):
                return True

            title = get_window_title(hwnd)
            cls   = get_window_class(hwnd)

            title_ok = (not title_lower) or (title_lower in title.lower())
            class_ok = cls in DIALOG_CLASSES

            if (title_ok and title) or class_ok:
                apply_to_hwnd(hwnd)
                applied_hwnds.add(hwnd)
            return True

        cb = WNDENUMPROC(enum_proc)

        # Phase 1 – detect: poll tightly for up to 2 s (400 × 5 ms)
        for _ in range(400):
            time.sleep(0.005)
            user32.EnumWindows(cb, 0)
            if applied_hwnds:
                break

        if not applied_hwnds:
            return  # dialog never appeared

        # Phase 2 – sustain: re-apply every 50 ms until dialog closes (up to 60 s)
        for _ in range(1200):
            time.sleep(0.05)
            alive = False
            for h in list(applied_hwnds):
                if user32.IsWindow(h) and user32.IsWindowVisible(h):
                    apply_to_hwnd(h)
                    alive = True
                else:
                    applied_hwnds.discard(h)
            if not alive:
                break

    threading.Thread(target=worker, daemon=True).start()


def prompt_select_directory(parent=None, caption: str = "Select Folder", start_dir: str = "", options=None) -> str:
    """
    Open native directory selection dialog with guaranteed crisp White title bar.
    The watcher thread is started *before* the blocking QFileDialog call so it
    can intercept the window the moment it appears.
    """
    watch_and_style_dialog_white(caption)
    from PySide6.QtWidgets import QFileDialog
    if options is None:
        options = QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
    return QFileDialog.getExistingDirectory(parent, caption, start_dir, options)
