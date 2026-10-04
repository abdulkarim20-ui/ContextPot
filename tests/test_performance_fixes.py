import os
import sys
import tempfile
import time
import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from app.core.scanner import scan_directory_structure, DirectoryScannerThread
from app.core.watcher_manager import FileSystemWatcherManager
from app.views.explorer.directory_tree import DirectoryTreeWidget
from app.views.explorer.explorer_view import ExplorerView


@pytest.fixture(scope="session")
def qapp():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_scanner_metadata_and_signature():
    with tempfile.TemporaryDirectory() as temp_dir:
        sub_dir = os.path.join(temp_dir, "sub")
        os.makedirs(sub_dir)
        file1 = os.path.join(temp_dir, "file1.txt")
        file2 = os.path.join(sub_dir, "file2.py")

        with open(file1, "w", encoding="utf-8") as f:
            f.write("hello")
        with open(file2, "w", encoding="utf-8") as f:
            f.write("print('world')")

        # Scan with collect_metadata=True
        data_full = scan_directory_structure(temp_dir, collect_metadata=True)
        assert data_full["structure_signature"] != ""
        sig1 = data_full["structure_signature"]
        assert data_full["stats"]["files"] == 2
        assert data_full["stats"]["folders"] == 1
        assert data_full["stats"]["total_size"] > 0

        # Scan with collect_metadata=False
        data_no_meta = scan_directory_structure(temp_dir, collect_metadata=False)
        sig2 = data_no_meta["structure_signature"]
        # Signature should match regardless of collect_metadata
        assert sig1 == sig2
        assert data_no_meta["stats"]["total_size"] == 0
        for child in data_no_meta["children"]:
            if child["type"] == "file":
                assert child["size_bytes"] == 0
                assert child["last_modified"] == ""

        # Test signature stability on file modification
        time.sleep(0.01)
        with open(file1, "w", encoding="utf-8") as f:
            f.write("hello modified content that is much longer")

        data_modified = scan_directory_structure(temp_dir, collect_metadata=False)
        assert data_modified["structure_signature"] == sig1

        # Test signature change on new file
        file3 = os.path.join(temp_dir, "file3.md")
        with open(file3, "w", encoding="utf-8") as f:
            f.write("# New file")

        data_new_file = scan_directory_structure(temp_dir, collect_metadata=False)
        assert data_new_file["structure_signature"] != sig1


def test_directory_scanner_thread(qapp):
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test")

        received = []

        thread = DirectoryScannerThread(
            temp_dir,
            collect_metadata=False,
            estimate_progress=False,
        )
        thread.scan_finished.connect(lambda data: received.append(data))
        thread.start()
        thread.wait(5000)
        qapp.processEvents()

        assert len(received) == 1
        assert received[0]["structure_signature"] != ""
        assert received[0]["stats"]["files"] == 1


def test_watcher_manager_threading(qapp):
    with tempfile.TemporaryDirectory() as temp_dir:
        watcher = FileSystemWatcherManager()
        watcher.start(temp_dir)
        assert watcher.root_path == os.path.abspath(temp_dir)
        assert watcher._thread is not None
        assert watcher._thread.isRunning()

        # Let worker initialize
        qapp.processEvents()

        watcher.stop()
        assert watcher.root_path == ""
        assert watcher._thread is None


def test_incremental_tree_population(qapp):
    tree = DirectoryTreeWidget()
    tree.show()

    # Create dummy scan data with 300 items
    scan_data = {
        "name": "Root",
        "abs_path": "/fake/root",
        "type": "folder",
        "children": [
            {
                "name": f"file_{i}.txt",
                "abs_path": f"/fake/root/file_{i}.txt",
                "type": "file",
                "display_type": "Text",
                "size_bytes": 0,
                "last_modified": "",
                "content": None,
            }
            for i in range(300)
        ],
        "structure_signature": "test_sig_123",
    }

    tree.populate(scan_data)
    assert tree.topLevelItemCount() == 1
    root = tree.topLevelItem(0)
    assert root.text(0) == "Root"

    # Initially before batches finish, queue has pending items
    assert tree._populate_active is True

    # Process events to allow batches to finish
    for _ in range(20):
        qapp.processEvents()
        if not tree._populate_active:
            break
        time.sleep(0.01)

    assert tree._populate_active is False
    assert root.childCount() == 300


def test_explorer_view_skip_rebuild_on_same_signature(qapp):
    view = ExplorerView()
    view.show()

    scan_data_1 = {
        "name": "Project",
        "abs_path": "/fake/project",
        "type": "folder",
        "children": [
            {
                "name": "item1.py",
                "abs_path": "/fake/project/item1.py",
                "type": "file",
                "display_type": "Python",
                "size_bytes": 0,
                "last_modified": "",
                "content": None,
            }
        ],
        "structure_signature": "sig_alpha",
    }

    view.set_project("Project", "/fake/project", scan_data_1)
    # Drain events for tree populate
    for _ in range(10):
        qapp.processEvents()
        time.sleep(0.01)

    # Spy on populate
    populate_called = []
    original_populate = view.tree_widget.populate

    def mock_populate(data):
        populate_called.append(data)
        original_populate(data)

    view.tree_widget.populate = mock_populate

    # Refresh with same structure_signature
    scan_data_2 = dict(scan_data_1)
    scan_data_2["stats"] = {"some": "change"}
    view.refresh_scan_data(scan_data_2)
    assert len(populate_called) == 0  # Rebuild was SKIPPED!

    # Refresh with different signature
    scan_data_3 = dict(scan_data_1)
    scan_data_3["structure_signature"] = "sig_beta"
    view.refresh_scan_data(scan_data_3)
    assert len(populate_called) == 1  # Rebuild was TRIGGERED!


def test_tree_expand_restoration_and_search(qapp):
    tree = DirectoryTreeWidget()
    tree.show()

    scan_data = {
        "name": "Project",
        "abs_path": "/fake/project",
        "type": "folder",
        "children": [
            {
                "name": "subfolder",
                "abs_path": "/fake/project/subfolder",
                "type": "folder",
                "display_type": "Folder",
                "children": [
                    {
                        "name": "target_file.py",
                        "abs_path": "/fake/project/subfolder/target_file.py",
                        "type": "file",
                        "display_type": "Python",
                        "size_bytes": 0,
                        "last_modified": "",
                        "content": None,
                    }
                ],
            },
            {
                "name": "other_file.txt",
                "abs_path": "/fake/project/other_file.txt",
                "type": "file",
                "display_type": "Text",
                "size_bytes": 0,
                "last_modified": "",
                "content": None,
            },
        ],
        "structure_signature": "sig_search_test",
    }

    tree.populate(scan_data)
    for _ in range(15):
        qapp.processEvents()
        if not tree._populate_active:
            break
        time.sleep(0.01)

    root = tree.topLevelItem(0)
    assert root.childCount() == 2

    # Find the subfolder item and expand it
    subfolder_item = None
    for i in range(root.childCount()):
        item = root.child(i)
        if item.text(0) == "subfolder":
            subfolder_item = item
            break
    assert subfolder_item is not None
    subfolder_item.setExpanded(True)

    # Re-populate and ensure subfolder stays expanded
    tree.populate(scan_data)
    for _ in range(15):
        qapp.processEvents()
        if not tree._populate_active:
            break
        time.sleep(0.01)

    root = tree.topLevelItem(0)
    new_subfolder_item = None
    for i in range(root.childCount()):
        item = root.child(i)
        if item.text(0) == "subfolder":
            new_subfolder_item = item
            assert item.isExpanded() is True

    assert new_subfolder_item is not None

    # Test search filtering
    tree.filter_items("target_file")
    assert new_subfolder_item.isHidden() is False
    assert new_subfolder_item.isExpanded() is True


def test_scanner_invalid_path_and_ignores():
    # Invalid path
    res = scan_directory_structure("/path/that/does/not/exist/ContextPot_test")
    assert res["name"] == "Invalid"
    assert res["structure_signature"] == ""

    # Test internal ignores (.git, User_Data)
    with tempfile.TemporaryDirectory() as temp_dir:
        git_dir = os.path.join(temp_dir, ".git")
        user_data = os.path.join(temp_dir, "User_Data")
        valid_dir = os.path.join(temp_dir, "src")
        os.makedirs(git_dir)
        os.makedirs(user_data)
        os.makedirs(valid_dir)

        with open(os.path.join(git_dir, "config"), "w") as f:
            f.write("gitconfig")
        with open(os.path.join(user_data, "settings.json"), "w") as f:
            f.write("{}")
        with open(os.path.join(valid_dir, "app.py"), "w") as f:
            f.write("print(1)")

        data = scan_directory_structure(temp_dir)
        child_names = [c["name"] for c in data["children"]]
        assert "src" in child_names
        assert ".git" not in child_names
        assert "User_Data" not in child_names

