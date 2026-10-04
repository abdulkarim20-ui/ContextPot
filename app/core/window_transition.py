from PySide6.QtCore import QTimer

class WindowTransitionManager:
    """
    Manages native window presentation.
    Avoids full-window QGraphicsOpacityEffect on top-level windows to prevent
    Windows DWM black flashes/rendering path degradation.
    """
    def __init__(self, window):
        self.window = window
        self._anim = None

    def animate_show(self, duration: int = 0, on_finished=None):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

        if on_finished:
            QTimer.singleShot(0, on_finished)

    def animate_close(self, duration: int = 180, on_finished=None):
        self.window.hide()
        if on_finished:
            on_finished()
