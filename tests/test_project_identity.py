"""
Tests for Project Identity Detection and ProjectIdentityBadge UI widget.
"""
from app.core.project_identity import detect_project_identity
from app.widgets.project_identity_badge import ProjectIdentityBadge
from app.widgets.drop_zone.loaded_folder_card import LoadedFolderCard


def test_detect_python_project():
    data = {
        "name": "MyPythonProject",
        "type": "folder",
        "children": [
            {"name": "pyproject.toml", "type": "file"},
            {"name": "main.py", "type": "file"},
            {"name": "scanner.py", "type": "file"},
            {
                "name": "app",
                "type": "folder",
                "children": [
                    {"name": "__init__.py", "type": "file"},
                    {"name": "utils.py", "type": "file"},
                ],
            },
        ],
    }
    identity = detect_project_identity(data)
    assert identity["name"] == "Python"
    assert identity["icon_file"] == "main.py"


def test_detect_react_project():
    data = {
        "name": "my-web-app",
        "type": "folder",
        "children": [
            {"name": "package.json", "type": "file"},
            {
                "name": "src",
                "type": "folder",
                "children": [
                    {"name": "App.tsx", "type": "file"},
                    {"name": "main.tsx", "type": "file"},
                    {"name": "index.css", "type": "file"},
                ],
            },
        ],
    }
    identity = detect_project_identity(data)
    assert identity["name"] == "React"
    assert identity["icon_file"] == "app.tsx"


def test_detect_typescript_project():
    data = {
        "name": "ts-lib",
        "type": "folder",
        "children": [
            {"name": "tsconfig.json", "type": "file"},
            {"name": "package.json", "type": "file"},
            {
                "name": "src",
                "type": "folder",
                "children": [
                    {"name": "index.ts", "type": "file"},
                    {"name": "math.ts", "type": "file"},
                ],
            },
        ],
    }
    identity = detect_project_identity(data)
    assert identity["name"] == "TypeScript"
    assert identity["icon_file"] == "app.ts"


def test_detect_java_project():
    data = {
        "name": "backend",
        "type": "folder",
        "children": [
            {"name": "pom.xml", "type": "file"},
            {
                "name": "src",
                "type": "folder",
                "children": [
                    {"name": "Main.java", "type": "file"},
                    {"name": "Controller.java", "type": "file"},
                ],
            },
        ],
    }
    identity = detect_project_identity(data)
    assert identity["name"] == "Java"
    assert identity["icon_file"] == "Main.java"


def test_detect_rust_project():
    data = {
        "name": "rust-cli",
        "type": "folder",
        "children": [
            {"name": "Cargo.toml", "type": "file"},
            {
                "name": "src",
                "type": "folder",
                "children": [
                    {"name": "main.rs", "type": "file"},
                ],
            },
        ],
    }
    identity = detect_project_identity(data)
    assert identity["name"] == "Rust"
    assert identity["icon_file"] == "main.rs"


def test_detect_node_backend_project():
    data = {
        "name": "node-backend",
        "type": "folder",
        "children": [
            {"name": "package.json", "type": "file"},
            {"name": "server.js", "type": "file"},
            {"name": "routes.js", "type": "file"},
        ],
    }
    identity = detect_project_identity(data)
    assert identity["name"] in ("Node.js", "JavaScript")


def test_detect_empty_or_unknown():
    assert detect_project_identity(None) == {"name": "Unknown", "icon_file": "project"}
    assert detect_project_identity({}) == {"name": "Unknown", "icon_file": "project"}
    assert detect_project_identity({"name": "Empty", "children": []}) == {
        "name": "Unknown",
        "icon_file": "project",
    }


def test_project_identity_badge_widget(qapp):
    badge = ProjectIdentityBadge()
    assert badge.identity_name == "Unknown"

    badge.set_identity({"name": "Python", "icon_file": "main.py"})
    assert badge.identity_name == "Python"
    assert not badge._icon.pixmap().isNull()

    badge.set_identity({"name": "TypeScript", "icon_file": "app.ts"})
    assert badge.identity_name == "TypeScript"
    assert not badge._icon.pixmap().isNull()

    # Backwards compatibility test
    badge.set_language("Rust")
    assert badge.identity_name == "Rust"


def test_loaded_folder_card_identity_integration(qapp):
    card = LoadedFolderCard()
    card.set_data({
        "name": "Test4",
        "path": "X:/Playground/Test4",
        "files": 42,
        "folders": 7,
        "size_str": "120 KB",
        "project_identity": {"name": "Python", "icon_file": "main.py"},
        "status": "Scan completed",
    })
    assert card.project_identity.identity_name == "Python"
    assert card.lang_badge.identity_name == "Python"
    assert not card.project_identity._icon.pixmap().isNull()
    # Short name is not elided
    assert card.name_lbl.text() == "Test4"


def test_loaded_folder_card_title_elision(qapp):
    card = LoadedFolderCard()
    card.resize(312, 88)
    card.show()

    # Long project name with identity badge
    card.set_data({
        "name": "talentmatch-agent",
        "path": "X:/Playground/talentmatch-agent",
        "files": 2698,
        "folders": 37,
        "size_str": "115.9 MB",
        "project_identity": {"name": "Python", "icon_file": "main.py"},
        "status": "Scan completed",
    })

    # The label text should be elided with '…' (ellipsis)
    assert "…" in card.name_lbl.text() or "..." in card.name_lbl.text()
    assert card.name_lbl.text().startswith("talent")
    assert card.name_lbl.text() != "talentmatch-agent"
    # Full project name is preserved
    assert card._full_project_name == "talentmatch-agent"
    # Custom tooltip provides the full name
    assert card.name_lbl._custom_tooltip_filter.text == "talentmatch-agent"

    # Short project name should NOT be elided
    card.set_data({
        "name": "Short",
        "path": "X:/Playground/Short",
        "files": 10,
        "folders": 1,
        "size_str": "10 KB",
        "project_identity": {"name": "Python", "icon_file": "main.py"},
        "status": "Scan completed",
    })
    assert card.name_lbl.text() == "Short"
    assert card.name_lbl._custom_tooltip_filter.text == ""


def test_animated_drag_drop_folder_icon_box(qapp):
    from app.widgets.drop_zone.folder_icon_box import ZoomableFolderIconBox

    box = ZoomableFolderIconBox()
    # Ensure animation frames were extracted and rendered
    assert len(box._frames) == 90
    assert box._frame_idx == 0

    # Test tick animation progression
    box._on_tick()
    assert box._frame_idx == 1

    # Jump to end and test alternate reverse behavior
    box._frame_idx = 89
    box._frame_dir = 1
    box._on_tick()
    assert box._frame_idx == 89
    assert box._frame_dir == -1

    box._on_tick()
    assert box._frame_idx == 88

    # Test zoom scaling
    box.set_scale(1.05)
    assert box.get_scale() == 1.05
    box.set_hovered(True)


def test_ignored_item_row_icons(qapp):
    from app.views.explorer.ignore_list_popup import IgnoredItemRow

    # Python file
    py_row = IgnoredItemRow("main.py")
    assert not py_row.icon_lbl.pixmap().isNull()

    # Node modules folder
    nm_row = IgnoredItemRow("node_modules")
    assert not nm_row.icon_lbl.pixmap().isNull()

    # Markdown file
    md_row = IgnoredItemRow("README.md")
    assert not md_row.icon_lbl.pixmap().isNull()

    # Folder with trailing slash
    f_row = IgnoredItemRow("build/")
    assert not f_row.icon_lbl.pixmap().isNull()
