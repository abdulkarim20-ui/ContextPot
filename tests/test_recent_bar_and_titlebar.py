import os
import sys
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton, QFrame, QLabel

from app.widgets.recent_bar import RecentBar
from app.widgets.title_bar import HeaderToolBar
from app.config.theme import TITLEBAR_GRADIENT_START, TITLEBAR_GRADIENT_END

@pytest.fixture(scope="session")
def qapp():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

def test_recent_bar_empty(qapp):
    bar = RecentBar()
    bar.set_recent_paths([])
    labels = bar.links_container.findChildren(QLabel)
    assert len(labels) == 1
    assert labels[0].text() == "None"

def test_recent_bar_long_paths_space_constraint(qapp):
    bar = RecentBar()
    bar.setFixedWidth(332)
    bar.links_container.setFixedWidth(260)
    
    # 3 long paths:
    paths = ["X:\\Python Course", "X:\\My Personal Projects", "X:\\Playground"]
    bar.set_recent_paths(paths)
    
    buttons = bar.links_container.findChildren(QPushButton)
    separators = bar.links_container.findChildren(QFrame)
    
    # First two items prioritized, 3rd omitted due to lack of space
    assert len(buttons) == 2
    assert len(separators) == 1
    
    # Buttons start with correct initial letters (never cut off from start)
    assert buttons[0].text().startswith("Python")
    assert buttons[1].text().startswith("My")
    
    # Divider is a clean 1px wide vertical bar
    assert separators[0].width() == 1
    assert separators[0].height() == 10

def test_recent_bar_short_paths_fit_three(qapp):
    bar = RecentBar()
    bar.setFixedWidth(332)
    bar.links_container.setFixedWidth(260)
    
    paths = ["X:\\A", "X:\\B", "X:\\C"]
    bar.set_recent_paths(paths)
    
    buttons = bar.links_container.findChildren(QPushButton)
    separators = bar.links_container.findChildren(QFrame)
    
    # All 3 items fit
    assert len(buttons) == 3
    assert len(separators) == 2
    assert buttons[0].text() == "A"
    assert buttons[1].text() == "B"
    assert buttons[2].text() == "C"

def test_titlebar_gradient_and_clean_toolbar(qapp):
    from app.config.theme import TITLEBAR_BG, TITLEBAR_TOP_GRADIENT
    from app.views.main_window import MainWindow

    toolbar = HeaderToolBar()
    style = toolbar.styleSheet()
    assert "background: transparent" in style
    assert "border: none" in style

    assert TITLEBAR_BG == "#ffffff"
    assert "qlineargradient" not in TITLEBAR_TOP_GRADIENT

    win = MainWindow()
    assert win.windowTitle() == "ContextPot"
    central_style = win.centralWidget().styleSheet()
    assert "qlineargradient" not in central_style
