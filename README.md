<div align="center">

<img src="docs/logo.svg" alt="ContextPot Logo" width="100" height="100" />

# ContextPot

**A local-first project explorer and AI-ready context exporter for developers.**

Turn any project folder into a clean, structured view of its files — then export only the context you need as Plain Text (`.txt`) or a directory tree.

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078d4?style=flat-square&logo=windows)](https://microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=flat-square&logo=python)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/UI-PySide6%20%28Qt%206%29-41cd52?style=flat-square&logo=qt)](https://www.qt.io/)
[![Architecture](https://img.shields.io/badge/Architecture-100%25%20Local-16a34a?style=flat-square&logo=shield)](https://github.com/abdulkarim20-ui/ContextPot)
[![License](https://img.shields.io/badge/License-Source--Available-f59e0b?style=flat-square)](LICENSE)

*Windows 10/11 · Python 3.10+ · PySide6 · 100% Local Processing*

</div>

---

## 💡 Why ContextPot?

Working with a real software project often means dealing with hundreds or thousands of files across deeply nested directories.

For **AI-assisted development**, **code reviews**, **technical documentation**, and **debugging**, the difficult part is rarely writing the prompt — it is assembling the right project context:

- Which files actually matter?
- Which directories are generated noise (`node_modules`, `dist`, `.git`)?
- How do you preserve the real project hierarchy?
- How do you exclude secrets and credentials?
- How do you export the result without manually copying files one by one?

**ContextPot is designed specifically around that workflow.**

$$\text{Select a Project} \longrightarrow \text{Inspect Its Structure} \longrightarrow \text{Control What Is Included} \longrightarrow \text{Export Clean Context}$$

Everything is processed **100% locally** on your machine. Zero cloud uploads, zero external telemetry, and zero account requirements.

---

## 🎯 What ContextPot Does

ContextPot combines four essential developer jobs in one lightweight, high-performance desktop application:

```text
┌─────────────────────────────────┐
│        Select a Project         │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│       Scan & Understand         │
│       Project Structure         │
└────────────────┬────────────────┘
                 │
        ┌────────┴────────┬────────────────┐
        ▼                 ▼                ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Search/Browse │ │ Ignore/Exclude│ │Monitor Changes│
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        └────────┬────────┴────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│          Choose Export          │
│   Whole Code + Tree / Tree Only │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│     Clean Local Output (.txt)   │
└─────────────────────────────────┘
```

---

## 🚀 Quick Start

### Requirements

- **Windows 10** or **Windows 11**
- **Python 3.10** or newer
- **Git**

### Installation

```bash
# Clone the repository
git clone https://github.com/abdulkarim20-ui/ContextPot.git
cd ContextPot

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
# Run directly with Python
python main.py

# Or via package entry point (if installed)
ContextPot
```

---

## 🔄 The ContextPot Workflow

ContextPot is organized around the way a developer actually interacts with a repository:

```text
Project Folder  ──►  Validate Path  ──►  Create Scan Job  ──►  Build Project Structure  ──►  Explorer
```

1. **Select a Project Root**: Drop a folder or browse to set a clean boundary for scanning and export.
2. **Inspect the Hierarchy**: Visually review directories, sub-packages, and file types.
3. **Filter Out Noise**: Strip build caches, dependencies, and temporary files using the 3-layer ignore engine.
4. **Export Clean Output**: Generate clean `.txt` files formatted for LLM prompts or architecture reviews.

---

## ⭐ Top 8 High-Impact Features

### 1. 🏠 Minimalist Project Launcher & Drop Zone
- **Zero Configuration**: Starts with a single goal: *Which project do you want to understand?*
- **Drag & Drop**: Drag any project folder directly from Windows Explorer into the drop zone.
- **Recent Projects History**: One-click re-access to recent repositories with automatic directory validation.
- **Diagnostics on Load**: Displays total file counts, folder counts, and directory paths immediately upon loading.

<p align="center">
  <img src="docs/01_home_screen.png" alt="Launcher Screen" width="700" />
</p>

<p align="center">
  <img src="docs/02_loaded_folder.png" alt="Loaded Folder State" width="700" />
</p>

---

### 2. ⚡ Sub-100ms Structure-First Scanner
- **Fast Traversal**: Scans 1,200+ files in **~97 ms** using Python's native `os.scandir()`.
- **Structure-First Browsing**: Does **not** read file bodies into memory during normal browsing. File contents are loaded lazily on demand only when an export is requested.
- **Safety Limits**: Depth limits (`MAX_FOLDER_DEPTH = 50`) and symlink cycle detection prevent infinite loops.
- **Metadata Toggle**: Live background scans bypass expensive `stat()` and timestamp conversion calls.

---

### 3. 🌲 Interactive Project Explorer with 370+ Icons
- **Visual Clarity**: Recognizable file-type identities powered by 370+ cached SVG icons from the Material Icon Theme ecosystem.
- **Atomic Navigation**: Quick **Collapse All** and **Expand All** toolbar actions with instant icon state synchronization.
- **Expanded State Memory**: Maintains open folders across file-saves and re-scans.
- **Non-Blocking Incremental Population**: Batched node insertion (150 items per event loop turn) keeps the window fully interactive and responsive even on huge codebases.

<p align="center">
  <img src="docs/03_explorer_tree.png" alt="Interactive Explorer Tree" width="700" />
</p>

---

### 4. 🔍 Real-Time Inline Search & Match Highlighting
- **Instant Search**: Type into the search field to filter the visible tree down to matching filenames and their parent hierarchy.
- **Amber Match Highlighting**: Custom item delegate renders a clean amber badge (`#FEF3C7`) behind matching characters.
- **Automatic Parent Expansion**: Items matching inside collapsed subfolders automatically expand for immediate discovery.
- **Debounced Input**: Eliminates typing stutter on large trees.

---

### 5. 👁️ Threaded Background Filesystem Watcher
- **Dedicated Worker Thread**: `QFileSystemWatcher` registration, dynamic directory discovery, and filesystem sweeps execute in a worker `QThread`.
- **Intelligent 300 ms Debounce**: Coalesces bursts of filesystem events (e.g. `Ctrl+S` bursts, git checkouts, build runs) into a single quiet refresh.
- **Structural Signature Verification**: Uses `hashlib.blake2b` to compute a structure signature. Normal file content edits **never** trigger unnecessary tree item rebuilds.
- **Zero GUI Freezes**: External additions, removals, and renames update smoothly in the background without causing Windows "Not Responding" stalls.

---

### 6. 🚫 3-Layer Ignore Engine (Built-in, Custom, Session)
A project contains much more than the source code you want to inspect:

$$\text{Built-in Defaults} + \text{Persistent User Rules} + \text{Session Exclusions} = \text{Effective Ignore Set}$$

- **Layer 1: Built-in Defaults**: Automatically filters 18+ bloat patterns (`node_modules/`, `.git/`, `dist/`, `build/`, `__pycache__/`, `.venv/`, `.next/`, `User_Data/`).
- **Layer 2: Persistent User Rules**: Define custom glob patterns (`*.log`, `*.tmp`, `coverage/`) in the Settings card.
- **Layer 3: Session Exclusions**: Right-click any file or folder to exclude it for your current working session without touching global configs.
- **High-Speed `_CompiledMatcher`**: O(1) exact hash set lookups combined with compiled regular expressions evaluate thousands of files in milliseconds.

<p align="center">
  <img src="docs/05_excluded_items_list.png" alt="Session Excluded Items Popup" width="700" />
</p>

---

### 7. 🖱️ Context Menu & Scoped Subtree Actions
Right-clicking any tree item provides contextual operations without leaving the Explorer view:
- **Exclude from Export**: Instantly hides and excludes the selected item(s) for the current session.
- **Export This File/Folder**: Scopes the export strictly to the selected subfolder or single file.
- **Copy Path**: Copies the absolute Windows filesystem path directly to your clipboard.
- **Multi-Selection Support**: Select multiple items using `Ctrl+Click` or `Shift+Click` and exclude them in a single batch.

<p align="center">
  <img src="docs/04_context_menu.png" alt="Explorer Context Menu" width="700" />
</p>

---

### 8. 📄 Clean Plain Text (`.txt`) & Tree Exporter with Secret Redaction
Converts the active project context into portable Plain Text (`.txt`) files:

| Export Mode | Output Format | Purpose & Best Use Case |
| :--- | :--- | :--- |
| **Whole code + Tree** | Single `.txt` file | **AI Prompts & Full Review**: Complete directory tree diagram followed by ordered file contents with clear boundaries. |
| **Tree Only** | Single `.txt` file | **Architectural Overviews**: Lightweight directory hierarchy outline without source code bodies. |

- **Automatic Secret Sanitization**: Scans source file contents during export for common credential patterns (`api_key`, `token`, `secret`, `private_key`, `auth`, `password`) and replaces values with `/* REDACTED SENSITIVE VALUE */`.
- **Smart Destination Memory**: Remembers export destinations per repository and prompts to set defaults.
- **Animated Toast Feedback**: Notification confirms export completion with a one-click button to reveal the output file in Windows Explorer.

<p align="center">
  <img src="docs/06_export_mode.png" alt="Export Mode Selector" width="700" />
</p>

---

## ⚙️ Settings & Ignore Configuration

The Settings view provides centralized control over application behavior and filtering rules:

- **Custom Ignore Patterns**: Add and remove persistent glob patterns for files and directories.
- **Workflow Preferences**: Toggle automatic scanning on folder drop and manage export destination defaults.

<p align="center">
  <img src="docs/07_settings_ignore_patterns.png" alt="Settings & Ignore Patterns" width="700" />
</p>

---

## 🆚 Why ContextPot Instead of Zipping?

| Challenge | Zip Archives (`.zip`) | ContextPot Exporter |
| :--- | :---: | :---: |
| **AI Readability** | ❌ Cannot be parsed directly by prompt windows | ✅ **100% AI-ready clean Plain Text (`.txt`)** |
| **Structure Clarity** | ❌ Requires extraction and navigation | ✅ **Visual hierarchical tree included** |
| **Noise Filtering** | ❌ Zips everything, including `node_modules` | ✅ **Smart 3-tier ignore engine** |
| **Secret Protection** | ❌ Plain-text keys and tokens exposed | ✅ **Automatic sensitive value redaction** |
| **Selective Scope** | ❌ Difficult to omit subfolders on the fly | ✅ **Right-click instant exclusions** |
| **Token Efficiency** | ❌ Blows LLM token windows with bloat | ✅ **Saves up to 85% of LLM token space** |

---

## ⚡ Performance Highlights

| Operation | Standard Approach | ContextPot Engine | Performance Gain |
| :--- | :--- | :--- | :--- |
| **Ignore Matching (1,200 files)** | 833 ms | **3.8 ms** | **214× faster** |
| **Directory Structure Scan (1,277 files)** | 1,003 ms | **~97 ms** | **10.4× faster** |
| **Tree Rebuild on Normal File Save** | Rebuild 5,000+ items | **0 ms (signature skip)** | **Instantaneous** |
| **File Content Memory Footprint** | Eager load (hundreds of MB) | **Lazy (near-zero RAM)** | **99% memory saving** |

---

## 🛡️ Security & Privacy Notes

- **100% Offline**: ContextPot never uploads code, metadata, or telemetry to external servers.
- **Secret Redaction**: Common credential keys (`api_key`, `token`, `secret`, `password`) are automatically masked with placeholders during export.
- **Best Practice Reminder**: Secret redaction is a safety layer, not a replacement for human review. Always inspect exported text before uploading to external AI services or sharing with third parties.

---

## 🚫 What ContextPot Is NOT

To keep ContextPot fast, focused, and lightweight:

- ❌ **Not an IDE or Text Editor**: Use VS Code, Cursor, or PyCharm for editing code.
- ❌ **Not an AI Model / LLM**: ContextPot prepares and controls the clean context that you supply to an AI system.
- ❌ **Not a Cloud Storage Service**: All operations are strictly local and offline.
- ❌ **Not a Replacement for Git**: ContextPot focuses on context inspection and export, not version control.

**ContextPot does one job with excellence: Understand the project structure, control the project context, and produce clean local exports.**

---

## 🗺️ Roadmap

- [ ] Multi-folder workspace support (combine multiple root directories)
- [ ] One-click "Copy Export to Clipboard" (bypass file save dialog)
- [ ] In-app file preview pane
- [ ] Keyboard shortcuts (Ctrl+F for search, Ctrl+E for export, Ctrl+R for reload)
- [ ] Git-aware file status indicators (modified, untracked, ignored)
- [ ] Cross-platform builds (macOS & Linux)

---

## 🆘 Troubleshooting

### ContextPot fails to launch
```bash
# Verify Python version (must be 3.10+)
python --version

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Run directly with error logging
python main.py
```

### Tree does not update after external changes
- The background filesystem watcher automatically tracks directory changes. If external scripts perform mass alterations and the tree appears stale, click **Back** and re-open the folder to perform a fresh instant scan.

### Export is missing expected files
- Check **Settings → Ignore Patterns** to ensure your custom rules are not unintentionally excluding source folders.
- Confirm that the files are visible in the Explorer tree prior to export.

### Settings or recents not persisting
- Check the console output on launch for the resolved data path. Ensure your user account has write permissions to `<project_root>/User_Data/` or `%APPDATA%\ContextPot\`.

---

## 📜 License & Credits

### Icon Attributions
SVG file and folder icons are derived from the **Material Icon Theme** ecosystem:
- **Project**: [vscode-material-icon-theme](https://github.com/material-extensions/vscode-material-icon-theme)
- **License**: [MIT License](https://opensource.org/licenses/MIT)

### Frameworks & Fonts
- **GUI Framework**: [PySide6 (Qt 6)](https://www.qt.io/)
- **Typography**: Inter (UI text) and JetBrains Mono (code and monospace paths)

### License
Copyright &copy; 2026 **AbdulKarim**. All rights reserved.  
Distributed under the terms specified in the [LICENSE](LICENSE) file.

<div align="center">

---

**ContextPot**  
*Understand the project. Control the context. Export what matters.*

</div>
