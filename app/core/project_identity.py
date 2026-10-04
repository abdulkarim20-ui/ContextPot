"""
ContextPot Project Identity Detection.

Lightweight, local repository language detection inspired by GitHub Linguist's strategy:
1. Ignore generated/vendor/build/cache/documentation paths.
2. Prefer explicit project manifests.
3. Detect by filename and extension.
4. Use project-level heuristics for frameworks/ecosystems.
5. Weight source files by bytes instead of file count.
6. Return one stable primary project identity.

No AI. No embeddings. No second filesystem scan.
Uses the scanner tree already produced by ContextPot.
"""
from __future__ import annotations

import os
from collections import defaultdict
from typing import Any, Dict, Iterable, Optional, Tuple

# ============================================================
# PATHS THAT SHOULD NOT INFLUENCE PROJECT IDENTITY
# ============================================================
IGNORED_ANALYSIS_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".github",
    ".idea",
    ".vscode",
    # Dependencies
    "node_modules",
    "vendor",
    "packages",
    "Pods",
    # Python environments / cache
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    # Build / generated
    "dist",
    "build",
    "out",
    "target",
    "bin",
    "obj",
    "coverage",
    ".next",
    ".nuxt",
    ".output",
    ".turbo",
    ".cache",
    # ContextPot internal
    "User_Data",
}

# ============================================================
# FILE TYPES
# language, representative icon filename, weight multiplier
# ============================================================
EXTENSION_MAP: Dict[str, Tuple[str, str, float]] = {
    # Python
    ".py": ("Python", "main.py", 1.0),
    ".pyw": ("Python", "main.py", 1.0),
    ".pyi": ("Python", "main.py", 0.8),
    # JavaScript / TypeScript
    ".js": ("JavaScript", "app.js", 1.0),
    ".jsx": ("JavaScript", "app.jsx", 1.0),
    ".mjs": ("JavaScript", "app.js", 1.0),
    ".cjs": ("JavaScript", "app.js", 1.0),
    ".ts": ("TypeScript", "app.ts", 1.0),
    ".tsx": ("TypeScript", "app.tsx", 1.0),
    # Java / JVM
    ".java": ("Java", "Main.java", 1.0),
    ".kt": ("Kotlin", "Main.kt", 1.0),
    ".kts": ("Kotlin", "Main.kt", 1.0),
    # C family
    ".c": ("C", "main.c", 1.0),
    ".h": ("C", "main.c", 0.45),
    ".cpp": ("C++", "main.cpp", 1.0),
    ".cc": ("C++", "main.cpp", 1.0),
    ".cxx": ("C++", "main.cpp", 1.0),
    ".hpp": ("C++", "main.cpp", 0.45),
    # C#
    ".cs": ("C#", "Program.cs", 1.0),
    # Go / Rust
    ".go": ("Go", "main.go", 1.0),
    ".rs": ("Rust", "main.rs", 1.0),
    # PHP / Ruby
    ".php": ("PHP", "index.php", 1.0),
    ".rb": ("Ruby", "main.rb", 1.0),
    # Mobile
    ".swift": ("Swift", "App.swift", 1.0),
    ".dart": ("Dart", "main.dart", 1.0),
    # Web frameworks
    ".vue": ("Vue", "App.vue", 1.0),
    ".svelte": ("Svelte", "App.svelte", 1.0),
    ".astro": ("Astro", "App.astro", 1.0),
    # Web
    ".html": ("HTML", "index.html", 0.35),
    ".htm": ("HTML", "index.html", 0.35),
    ".css": ("CSS", "style.css", 0.25),
    ".scss": ("SCSS", "style.scss", 0.25),
    ".sass": ("Sass", "style.sass", 0.25),
    ".less": ("Less", "style.less", 0.25),
    # Shell
    ".sh": ("Shell", "script.sh", 1.0),
    ".bash": ("Shell", "script.sh", 1.0),
    ".zsh": ("Shell", "script.sh", 1.0),
    ".ps1": ("PowerShell", "script.ps1", 1.0),
    ".bat": ("Batch", "script.bat", 1.0),
    ".cmd": ("Batch", "script.cmd", 1.0),
    # Other programming languages
    ".lua": ("Lua", "script.lua", 1.0),
    ".r": ("R", "script.r", 1.0),
    ".scala": ("Scala", "Main.scala", 1.0),
    ".ex": ("Elixir", "main.ex", 1.0),
    ".exs": ("Elixir", "main.exs", 1.0),
    ".clj": ("Clojure", "main.clj", 1.0),
    ".hs": ("Haskell", "Main.hs", 1.0),
    ".fs": ("F#", "Program.fs", 1.0),
    ".fsx": ("F#", "Program.fsx", 1.0),
    ".zig": ("Zig", "main.zig", 1.0),
}

# ============================================================
# IMPORTANT PROJECT FILES
# ============================================================
SPECIAL_FILENAMES: Dict[str, Tuple[str, str]] = {
    "dockerfile": ("Docker", "dockerfile"),
    "containerfile": ("Docker", "containerfile"),
    "makefile": ("Make", "makefile"),
    "gemfile": ("Ruby", "Gemfile"),
    "rakefile": ("Ruby", "Rakefile"),
    "cmakelists.txt": ("CMake", "CMakeLists.txt"),
}

# ============================================================
# PROJECT MANIFESTS
# Higher confidence than ordinary source files.
# ============================================================
MANIFESTS: Dict[str, Tuple[str, str, int]] = {
    "pyproject.toml": ("Python", "main.py", 100),
    "requirements.txt": ("Python", "main.py", 90),
    "setup.py": ("Python", "main.py", 100),
    "setup.cfg": ("Python", "main.py", 80),
    "pipfile": ("Python", "main.py", 90),
    "package.json": ("Node.js", "package.json", 100),
    "pom.xml": ("Java", "Main.java", 100),
    "build.gradle": ("Java", "Main.java", 100),
    "build.gradle.kts": ("Kotlin", "Main.kt", 100),
    "cargo.toml": ("Rust", "main.rs", 100),
    "go.mod": ("Go", "main.go", 100),
    "composer.json": ("PHP", "index.php", 100),
    "gemfile": ("Ruby", "Gemfile", 100),
    "pubspec.yaml": ("Dart", "main.dart", 100),
    "package.swift": ("Swift", "Package.swift", 100),
    "cmakelists.txt": ("C++", "CMakeLists.txt", 100),
}

# ============================================================
# DOCUMENTATION / DATA FILES
# These should not make a project "Markdown" or "JSON".
# ============================================================
NON_PRIMARY_EXTENSIONS = {
    ".md",
    ".markdown",
    ".rst",
    ".txt",
    ".json",
    ".jsonc",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".csv",
    ".tsv",
    ".sql",
}

# ============================================================
# GENERATED FILE NAME PATTERNS
# ============================================================
GENERATED_NAME_PARTS = {
    ".min.",
    ".bundle.",
    ".generated.",
    ".g.",
    ".designer.",
    ".gen.",
}

# ============================================================
# PUBLIC API
# ============================================================
def detect_project_identity(
    data: Optional[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Detect the primary project identity from ContextPot's already-scanned tree.

    Returns:
        { "name": "Python", "icon_file": "main.py" }
    Unknown projects return:
        { "name": "Unknown", "icon_file": "project" }
    """
    if not isinstance(data, dict):
        return _unknown()

    files = list(_iter_files(data))
    if not files:
        return _unknown()

    language_bytes: Dict[str, float] = defaultdict(float)
    language_files: Dict[str, int] = defaultdict(int)
    representatives: Dict[str, str] = {}
    manifest_scores: Dict[str, float] = defaultdict(float)
    manifest_icons: Dict[str, str] = {}

    has_tsconfig = False
    has_package_json = False
    package_json_content = ""
    has_tsx = False
    has_jsx = False
    has_vue = False
    has_svelte = False

    # --------------------------------------------------------
    # Analyze the already scanned tree.
    # --------------------------------------------------------
    for node in files:
        name = str(node.get("name", "")).strip()
        if not name:
            continue

        path = str(
            node.get("path", "")
        ).replace("\\", "/")
        if _is_ignored_path(path):
            continue

        lower_name = name.lower()

        # ----------------------------------------------------
        # Important project files
        # ----------------------------------------------------
        if lower_name == "tsconfig.json":
            has_tsconfig = True
        if lower_name == "package.json":
            has_package_json = True
            # Scanner intentionally reads content lazily.
            # Only use content if it already exists.
            package_json_content = str(
                node.get("content") or ""
            ).lower()

        manifest = MANIFESTS.get(lower_name)
        if manifest:
            language, icon, score = manifest
            manifest_scores[language] += score
            manifest_icons[language] = icon

        # ----------------------------------------------------
        # Framework signals
        # ----------------------------------------------------
        if lower_name.endswith(".tsx"):
            has_tsx = True
        elif lower_name.endswith(".jsx"):
            has_jsx = True
        elif lower_name.endswith(".vue"):
            has_vue = True
        elif lower_name.endswith(".svelte"):
            has_svelte = True

        # ----------------------------------------------------
        # Special filenames
        # ----------------------------------------------------
        if lower_name in SPECIAL_FILENAMES:
            language, icon = SPECIAL_FILENAMES[lower_name]
            if language not in representatives:
                representatives[language] = icon
            language_files[language] += 1
            # Small signal only; manifest is stronger.
            language_bytes[language] += 500
            continue

        # ----------------------------------------------------
        # Extension detection
        # ----------------------------------------------------
        _, extension = os.path.splitext(lower_name)
        info = EXTENSION_MAP.get(extension)
        if not info:
            continue

        language, icon, multiplier = info
        size = _safe_size(node)
        # Prevent tiny files from dominating.
        effective_size = max(size, 32) * multiplier

        language_bytes[language] += effective_size
        language_files[language] += 1
        representatives.setdefault(language, icon)

    # ========================================================
    # HIGH-CONFIDENCE FRAMEWORK DETECTION
    # ========================================================
    # Vue / Svelte are unambiguous.
    if has_vue:
        return {
            "name": "Vue",
            "icon_file": "app.vue",
        }
    if has_svelte:
        return {
            "name": "Svelte",
            "icon_file": "app.svelte",
        }

    # React requires JSX/TSX.
    if has_tsx or has_jsx:
        if _package_mentions(package_json_content, "react"):
            return {
                "name": "React",
                "icon_file": ("app.tsx" if has_tsx else "app.jsx"),
            }
        # TSX/JSX itself is a strong React signal.
        return {
            "name": "React",
            "icon_file": ("app.tsx" if has_tsx else "app.jsx"),
        }

    # ========================================================
    # NODE.JS
    # ========================================================
    if has_package_json:
        if _package_mentions(
            package_json_content,
            "express",
            "fastify",
            "nestjs",
            "koa",
            "hono",
            "node",
        ):
            return {
                "name": "Node.js",
                "icon_file": "package.json",
            }

    # ========================================================
    # MANIFEST OVERRIDE
    # A strong root manifest should beat a random majority
    # caused by configuration/documentation files.
    # ========================================================
    if manifest_scores:
        strongest_manifest = max(
            manifest_scores.items(), key=lambda item: item[1]
        )
        manifest_language, manifest_score = strongest_manifest

        # Require actual source code for most manifests.
        # This prevents an empty package.json from claiming
        # an otherwise empty project.
        if language_files.get(manifest_language, 0) > 0:
            return {
                "name": manifest_language,
                "icon_file": manifest_icons[manifest_language],
            }

    # ========================================================
    # BYTE-WEIGHTED PRIMARY LANGUAGE
    # ========================================================
    if language_bytes:
        ranked = sorted(
            language_bytes.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        primary_language = ranked[0][0]
        return {
            "name": primary_language,
            "icon_file": representatives.get(
                primary_language, _default_icon(primary_language)
            ),
        }

    return _unknown()


# ============================================================
# TREE ITERATION
# ============================================================
def _iter_files(root: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """
    Iteratively walk the scanner tree.
    Avoids recursion depth issues.
    """
    stack = [root]
    while stack:
        node = stack.pop()
        for child in node.get("children", []):
            node_type = child.get("type", "file")
            if node_type == "folder":
                name = str(child.get("name", "")).lower()
                if name in {item.lower() for item in IGNORED_ANALYSIS_DIRS}:
                    continue
                stack.append(child)
            elif node_type == "file":
                yield child


# ============================================================
# PATH FILTERING
# ============================================================
def _is_ignored_path(path: str) -> bool:
    normalized = str(path or "").replace("\\", "/").lower()
    parts = {part for part in normalized.split("/") if part}
    if parts & {item.lower() for item in IGNORED_ANALYSIS_DIRS}:
        return True

    filename = os.path.basename(normalized)

    # Generated/minified files.
    for marker in GENERATED_NAME_PARTS:
        if marker in filename:
            return True

    # Common source-map artifacts.
    if filename.endswith((".map", ".lock")):
        return True

    return False


# ============================================================
# SIZE
# ============================================================
def _safe_size(node: Dict[str, Any]) -> int:
    for key in ("size_bytes", "size"):
        value = node.get(key)
        try:
            value = int(value)
            if value >= 0:
                return value
        except (TypeError, ValueError):
            pass
    return 0


# ============================================================
# PACKAGE.JSON SIGNAL
# ============================================================
def _package_mentions(content: str, *names: str) -> bool:
    if not content:
        return False
    return any(f'"{name}"' in content for name in names)


# ============================================================
# FALLBACKS
# ============================================================
def _default_icon(language: str) -> str:
    return {
        "Python": "main.py",
        "JavaScript": "app.js",
        "TypeScript": "app.ts",
        "Java": "Main.java",
        "Kotlin": "Main.kt",
        "C": "main.c",
        "C++": "main.cpp",
        "C#": "Program.cs",
        "Go": "main.go",
        "Rust": "main.rs",
        "PHP": "index.php",
        "Ruby": "main.rb",
        "Swift": "App.swift",
        "Dart": "main.dart",
        "Lua": "script.lua",
        "R": "script.r",
    }.get(language, "project")


def _unknown() -> Dict[str, str]:
    return {
        "name": "Unknown",
        "icon_file": "project",
    }
