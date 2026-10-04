import os
import re
import json
import fnmatch
from typing import List, Optional, Set

from app.config.paths import IGNORE_FILE, data_dir

DEFAULT_IGNORE_PATTERNS = [
    # Environments & Dependencies
    "node_modules", "env", "venv", ".env", ".venv", ".npm", ".yarn", "vendor",
    # Build & Dist
    "dist", "build", "out", "target", ".next", ".nuxt", ".output", ".turbo", ".cache",
    # IDE & System
    ".git", ".svn", ".hg", ".DS_Store", "Thumbs.db", ".vscode", ".idea",
    # Python Cache & Logs
    "__pycache__", "*.pyc", "*.pyo", "*.pyd", "*.log", "*.tmp", "*.bak", ".pytest_cache",
    # Coverage & Cloud
    "coverage", ".coverage", ".vercel", ".serverless",
    # ContextPot internal local metadata (never part of the scanned project)
    "User_Data"
]

INTERNAL_PROJECT_IGNORES = {
    "User_Data",
}

class IgnoreManager:
    """
    Centralized manager for ignore patterns.
    Maintains strict separation between:
    1. Persistent Scan Ignore (Settings -> RP_Ignore_pattern.json)
    2. Temporary Session Exclusions (Explorer -> in-memory only)
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IgnoreManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.default_patterns = list(DEFAULT_IGNORE_PATTERNS)
        self.user_patterns: List[str] = []
        self.session_patterns: List[str] = []  # Temporary files/folders excluded in active Explorer
        self.removed_defaults: Set[str] = set()
        self.is_enabled: bool = True
        self._scan_matcher: Optional["_CompiledMatcher"] = None
        self._explorer_matcher: Optional["_CompiledMatcher"] = None
        self.load_patterns()

    def _invalidate_matchers(self):
        self._scan_matcher = None
        self._explorer_matcher = None

    def get_session_patterns(self) -> List[str]:
        """Return temporary files/folders excluded in Explorer session (newest first)."""
        return list(self.session_patterns)

    def get_persistent_patterns(self) -> List[str]:
        """Return permanent ignore patterns (user patterns + default patterns)."""
        active_user = [p for p in self.user_patterns if p not in self.removed_defaults]
        existing = set(active_user) | self.removed_defaults
        active_defaults = [p for p in self.default_patterns if p not in existing]
        return active_user + active_defaults

    def get_scan_patterns(self) -> List[str]:
        """Return patterns used for directory scans (persistent only)."""
        return self.get_persistent_patterns()

    def get_explorer_patterns(self) -> List[str]:
        """Return patterns used for Explorer view & Export (persistent + session exclusions)."""
        patterns = list(self.get_persistent_patterns())
        for pattern in self.session_patterns:
            if pattern not in patterns:
                patterns.append(pattern)
        return patterns

    def get_all_patterns(self) -> List[str]:
        """Returns ordered active patterns with session patterns first."""
        session_active = list(self.session_patterns)
        persistent = self.get_persistent_patterns()
        seen = set(session_active)
        res = list(session_active)
        for p in persistent:
            if p not in seen:
                seen.add(p)
                res.append(p)
        return res

    def add_session_pattern(self, pattern: str) -> bool:
        """Add a temporary file/folder to Explorer session ignore list (not saved to disk)."""
        p = pattern.strip()
        if not p:
            return False
        if p in self.session_patterns:
            self.session_patterns.remove(p)
        self.session_patterns.insert(0, p)
        self._invalidate_matchers()
        return True

    def remove_session_pattern(self, pattern: str) -> bool:
        """Remove a temporary file/folder from Explorer session ignore list."""
        p = pattern.strip()
        if p in self.session_patterns:
            self.session_patterns.remove(p)
            self._invalidate_matchers()
            return True
        return False

    def clear_session_patterns(self):
        """Clear all temporary session patterns."""
        self.session_patterns.clear()
        self._invalidate_matchers()

    def load_patterns(self):
        """Load ignore patterns from RP_Ignore_pattern.json."""
        os.makedirs(data_dir(), exist_ok=True)
        self._invalidate_matchers()
        if not os.path.exists(IGNORE_FILE):
            return

        try:
            with open(IGNORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.user_patterns = data.get("user_patterns", [])
                    self.removed_defaults = set(data.get("removed_defaults", []))
                    self.is_enabled = data.get("is_enabled", True)
                elif isinstance(data, list):
                    self.user_patterns = data
        except Exception as e:
            print(f"[IgnoreManager] Error loading ignore patterns: {e}")

    def save_patterns(self):
        """Save persistent ignore patterns to RP_Ignore_pattern.json."""
        os.makedirs(data_dir(), exist_ok=True)
        self._invalidate_matchers()
        data = {
            "user_patterns": self.user_patterns,
            "removed_defaults": list(self.removed_defaults),
            "is_enabled": self.is_enabled
        }
        try:
            with open(IGNORE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[IgnoreManager] Error saving ignore patterns: {e}")

    def add_pattern(self, pattern: str) -> bool:
        """Add a persistent pattern to the very TOP of the ignore list."""
        p = pattern.strip()
        if not p:
            return False

        if p in self.removed_defaults:
            self.removed_defaults.remove(p)

        if p in self.user_patterns:
            self.user_patterns.remove(p)

        self.user_patterns.insert(0, p)
        self.save_patterns()
        return True

    def remove_pattern(self, pattern: str) -> bool:
        """Remove a pattern from session, user patterns, or mark default as removed."""
        p = pattern.strip()
        if not p:
            return False

        changed = False
        if p in self.session_patterns:
            self.session_patterns.remove(p)
            changed = True

        if p in self.user_patterns:
            self.user_patterns.remove(p)
            changed = True

        if p in self.default_patterns:
            self.removed_defaults.add(p)
            changed = True

        if changed:
            self._invalidate_matchers()
            if p not in self.session_patterns:
                self.save_patterns()
        return changed

    def reset_defaults(self):
        """Reset all patterns to default state."""
        self.user_patterns.clear()
        self.removed_defaults.clear()
        self.save_patterns()

    def set_enabled(self, enabled: bool):
        self.is_enabled = enabled
        self.save_patterns()

    def should_ignore_scan(self, name_or_path: str) -> bool:
        """Check if item should be ignored during persistent scan (initial/live scans)."""
        if not self.is_enabled:
            return False
        if self._scan_matcher is None:
            self._scan_matcher = _CompiledMatcher(self.get_scan_patterns())
        return self._scan_matcher.matches(name_or_path)

    def should_ignore_explorer(self, name_or_path: str) -> bool:
        """Check if item should be excluded in Explorer view (persistent + session exclusions)."""
        if not self.is_enabled:
            return False
        if self._explorer_matcher is None:
            self._explorer_matcher = _CompiledMatcher(self.get_explorer_patterns())
        return self._explorer_matcher.matches(name_or_path)

    def should_ignore_export(self, name_or_path: str) -> bool:
        """Check if item should be excluded in Export (persistent + session exclusions)."""
        return self.should_ignore_explorer(name_or_path)

    def should_ignore(self, name_or_path: str) -> bool:
        """General ignore check (defaults to Explorer/Export scoped check)."""
        return self.should_ignore_explorer(name_or_path)


class _CompiledMatcher:
    """High-performance compiled pattern matcher with O(1) set lookups, extension handling, and path normalization."""
    __slots__ = ("exact_names", "ext_suffixes", "exact_paths", "combined_re")

    def __init__(self, patterns: List[str]):
        self.exact_names: Set[str] = set()
        self.ext_suffixes: Set[str] = set()
        self.exact_paths: Set[str] = set()
        regex_parts: List[str] = []

        for p in patterns:
            p_clean = p.strip().lower().replace('\\', '/')
            if not p_clean:
                continue

            # Case 1: *.ext (e.g. *.svg, *.pyc, *.log)
            if p_clean.startswith('*.'):
                suffix = p_clean[1:]  # e.g. .svg
                if '/' not in suffix and '*' not in suffix[1:] and '?' not in suffix:
                    self.ext_suffixes.add(suffix)
                    continue

            # Case 2: .ext (e.g. .svg, .png, .env, .git)
            if p_clean.startswith('.') and '/' not in p_clean and '*' not in p_clean and '?' not in p_clean:
                self.ext_suffixes.add(p_clean)
                self.exact_names.add(p_clean)
                continue

            # Case 3: Simple word without slashes or wildcards (e.g. node_modules, dist, svg)
            if '/' not in p_clean and '*' not in p_clean and '?' not in p_clean:
                self.exact_names.add(p_clean)
                if len(p_clean) <= 6 and not p_clean.startswith('.'):
                    self.ext_suffixes.add('.' + p_clean)
                continue

            # Case 4: Path without wildcards (e.g. assets/files icon)
            if '*' not in p_clean and '?' not in p_clean:
                self.exact_paths.add(p_clean.rstrip('/'))
                continue

            # Case 5: Complex wildcards / globs
            regex_parts.append(fnmatch.translate(p_clean))

        self.combined_re = re.compile('|'.join(regex_parts)) if regex_parts else None

    def matches(self, name_or_path: str) -> bool:
        if not name_or_path:
            return False
        target = name_or_path.strip().lower().replace('\\', '/')
        base_name = os.path.basename(target) or target

        # 1. Check extension (case-insensitive)
        _, ext = os.path.splitext(base_name)
        if ext and ext in self.ext_suffixes:
            return True

        # 2. Check exact base name
        if base_name in self.exact_names:
            return True

        # 3. Check exact path / inside exact path
        for p in self.exact_paths:
            if target == p or target.startswith(p + '/') or target.endswith('/' + p) or ('/' + p + '/') in target:
                return True

        # 4. Check if any parent folder segment matches exact_names
        segments = target.split('/')
        for seg in segments:
            if seg in self.exact_names:
                return True

        # 5. Check regex/glob
        if self.combined_re:
            if self.combined_re.search(target) or self.combined_re.search(base_name):
                return True

        return False

# Global accessor
def get_ignore_manager() -> IgnoreManager:
    return IgnoreManager()
