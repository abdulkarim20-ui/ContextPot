import gc
import os
import sys

import pytest


@pytest.fixture(scope="session", autouse=True)
def _qt_cleanup():
    yield
    try:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            app.closeAllWindows()
            app.processEvents()
    except Exception:
        pass
    gc.collect()


def pytest_sessionfinish(session, exitstatus):
    session.config._ci_exitstatus = int(exitstatus)


def pytest_unconfigure(config):
    if sys.platform == "win32" and os.environ.get("CI"):
        status = getattr(config, "_ci_exitstatus", 0)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(status)
