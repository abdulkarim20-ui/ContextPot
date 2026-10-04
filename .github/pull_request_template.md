## Description

Brief summary of the changes introduced in this pull request and the rationale behind them.

Fixes #(issue)

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change fixing an issue)
- [ ] ✨ New feature (non-breaking change adding functionality)
- [ ] ⚡ Performance improvement (optimizations without changing product behavior)
- [ ] 📝 Documentation update
- [ ] 🧹 Refactoring / Code cleanup

## Architectural Checklist

- [ ] Filesystem I/O, directory traversal, and watcher registration remain **off the GUI thread** (using worker `QThread` instances).
- [ ] File content loading remains **lazy** (only loaded during export, not during browsing).
- [ ] Secret redaction safety (`sanitize_content`) is preserved.
- [ ] No personal files, secrets, or `User_Data/` artifacts are included in this PR.

## Verification & Testing

- [ ] `python -m compileall app` passed with zero errors.
- [ ] `pytest -v` passed with 100% success rate.
- [ ] Tested manually on Windows with a sample project folder.
