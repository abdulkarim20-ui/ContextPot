"""Shared QApplication fixture and deterministic Qt widget teardown."""

import gc
import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication


def _drain_qt(app):
    """Close top-level widgets and flush Qt's deferred deletions."""
    for widget in list(app.topLevelWidgets()):
        try:
            widget.close()
            widget.deleteLater()
        except RuntimeError:
            pass

    for _ in range(3):
        app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    gc.collect()


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
    _drain_qt(app)


@pytest.fixture(autouse=True)
def _qt_cleanup_after_each_test():
    yield
    app = QApplication.instance()
    if app is not None:
        _drain_qt(app)
