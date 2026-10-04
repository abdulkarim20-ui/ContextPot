# Contributing to ContextPot

Thank you for your interest in contributing to **ContextPot**! We welcome bug reports, feature suggestions, architecture improvements, and code contributions.

Please read this document to understand our development workflow and contribution standards.

---

## Code of Conduct

By participating in this project, you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to the project maintainers.

---

## How Can I Contribute?

### 1. Reporting Bugs
Before creating an issue, please search existing issues to avoid duplicates. When filing a bug report:
- Use the **Bug Report** template.
- Specify your exact OS version (Windows 10 / 11) and Python version (`python --version`).
- Provide clear, reproducible step-by-step instructions.
- Include terminal logs or error tracebacks if applicable.

### 2. Suggesting Enhancements
Feature requests are welcome! When proposing a new feature:
- Clearly explain the problem the feature solves.
- Describe how you envision the user interaction or export pipeline.
- Detail why this feature aligns with ContextPot's mission (local-first, fast, lightweight project exploration).

### 3. Code Contributions & Pull Requests
For non-trivial changes, please open an issue first to discuss the proposed architecture before spending time writing code.

---

## Development Setup

### Prerequisites
- **Python 3.10+**
- **Git**
- **Windows 10 / 11**

### Setup Steps
```bash
# 1. Fork and clone the repository
git clone https://github.com/<your-username>/ContextPot.git
cd ContextPot

# 2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 3. Install development dependencies
pip install -r requirements-dev.txt

# 4. Run ContextPot locally
python main.py
```

---

## Architectural Guidelines

When contributing code to ContextPot, please observe these core rules:

1. **Keep Filesystem I/O Off the GUI Thread**:
   - Never run `os.scandir()`, recursive file walks, or heavy file reading directly on the Qt main thread.
   - Use dedicated worker `QThread` instances (`DirectoryScannerThread`, `_WatcherWorker`) and connect back to the UI using queued signals.
2. **Structure-First Browsing**:
   - Do not eagerly read file bodies into memory during normal browsing. File reading must remain lazy and execute strictly on export.
3. **Respect the 3-Layer Ignore System**:
   - New exclusion rules must integrate with `app/core/ignore_manager.py` to ensure consistency across scanning, watching, and exporting.
4. **Preserve Secret Redaction Safety**:
   - Ensure any export pipeline modifications respect `sanitize_content()` in `app/core/exporter.py`.

---

## Testing & Verification

Before submitting a Pull Request, always verify that all tests pass cleanly:

```bash
# Static syntax and compile validation
python -m compileall app

# Run full test suite
pytest -v
```

If you add new features or modify core engine behavior, please add corresponding unit tests in `tests/`.

---

## Pull Request Checklist

- [ ] Branch created from `main` with a descriptive name (e.g., `feature/xyz` or `fix/abc`).
- [ ] Code follows PEP 8 conventions with clean type hints where appropriate.
- [ ] No personal configuration files or `User_Data/` artifacts committed.
- [ ] `pytest` passes with 100% success rate.
- [ ] PR description clearly describes the changes and links to any related issue.
