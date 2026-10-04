"""
Markdown Exporter for ContextPot.

Produces clean, LLM-optimized Markdown exports:
- Tree only: {Project}_tree.md
- Whole code + Tree: {Project}_full.md

Features:
- Structured Markdown header with project metadata
- Project structure tree enclosed in a fenced text block
- Syntax-highlighted fenced code blocks per language
- File size limit: 10 MB per text/source file
- Lightweight binary sniffing to prevent dumping binary data into Markdown
- Secret sanitization to redact API keys and passwords
- Respects project ignore patterns and internal exclusions
"""

import os
import re
from typing import Any, Dict, List, Optional

INTERNAL_NAMES = {"User_Data"}

# 10 MB limit per file
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
BINARY_SNIFF_BYTES = 8192

# ============================================================
# LANGUAGE & BINARY MAPPINGS
# ============================================================

FILENAME_LANGUAGE_MAP = {
    "dockerfile": "dockerfile",
    "containerfile": "dockerfile",
    "makefile": "makefile",
    "gnumakefile": "makefile",
    "cmakelists.txt": "cmake",
    "jenkinsfile": "groovy",
    "gemfile": "ruby",
    "rakefile": "ruby",
    "vagrantfile": "ruby",
    "procfile": "yaml",
    ".gitignore": "gitignore",
    ".gitattributes": "gitattributes",
    ".editorconfig": "editorconfig",
    ".env": "bash",
    ".env.example": "bash",
    ".env.local": "bash",
}

LANGUAGE_MAP = {
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "jsx",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".json": "json",
    ".jsonc": "jsonc",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".svg": "xml",
    ".sql": "sql",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".ps1": "powershell",
    ".psm1": "powershell",
    ".bat": "batch",
    ".cmd": "batch",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".cs": "csharp",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".dart": "dart",
    ".lua": "lua",
    ".r": "r",
    ".scala": "scala",
    ".pl": "perl",
    ".pm": "perl",
    ".md": "markdown",
    ".markdown": "markdown",
    ".rst": "rst",
    ".tex": "latex",
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "ini",
    ".properties": "properties",
    ".proto": "protobuf",
    ".graphql": "graphql",
    ".gql": "graphql",
    ".vue": "vue",
    ".svelte": "svelte",
    ".astro": "astro",
    ".zig": "zig",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hrl": "erlang",
    ".clj": "clojure",
    ".hs": "haskell",
    ".fs": "fsharp",
    ".v": "verilog",
    ".sv": "systemverilog",
    ".txt": "text",
    ".log": "text",
    ".csv": "csv",
    ".tsv": "tsv",
}

BINARY_EXTENSIONS = {
    # Images
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp', '.tiff', '.tif', '.psd',
    # Audio & Video
    '.mp3', '.mp4', '.wav', '.avi', '.mov', '.flac', '.ogg', '.mkv', '.webm', '.m4a',
    # Archives & Compressed
    '.zip', '.tar', '.gz', '.7z', '.rar', '.bz2', '.xz', '.tgz',
    # Executables & Libraries
    '.exe', '.dll', '.so', '.dylib', '.bin', '.iso', '.dmg', '.msi',
    # Bytecode & Compilations
    '.pyc', '.pyo', '.pyd', '.class',
    # Fonts
    '.woff', '.woff2', '.ttf', '.eot', '.otf',
    # Databases & Big Data
    '.db', '.sqlite', '.sqlite3', '.parquet', '.npy', '.npz',
    # Documents
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
}

# ============================================================
# PATH & FILENAME HELPERS
# ============================================================

def get_unique_path(path: str) -> str:
    """
    If path exists, appends an incrementing number to the filename until a unique path is found.
    Example: 'file.md' -> 'file_1.md' -> 'file_2.md'
    """
    if not os.path.exists(path):
        return path

    base, ext = os.path.splitext(path)
    counter = 1
    while True:
        new_path = f"{base}_{counter}{ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def _get_markdown_language(file_name: str, file_path: str = "") -> str:
    """Determine the Markdown fenced-code language."""
    name = os.path.basename(file_name or file_path or "").lower()
    if name in FILENAME_LANGUAGE_MAP:
        return FILENAME_LANGUAGE_MAP[name]
    # Special extension-like names
    if name.endswith(".dockerfile"):
        return "dockerfile"
    _, ext = os.path.splitext(name)
    return LANGUAGE_MAP.get(ext, "text")


def _escape_markdown_path(path: str) -> str:
    """Make a file path safe for a Markdown heading."""
    if not path:
        return "unknown"
    return path.replace("`", "\\`")


def _looks_binary(path: str) -> bool:
    """
    Lightweight binary detection.
    Inspects extension first, then up to 8KB prefix without loading the full file into memory.
    """
    _, ext = os.path.splitext(path.lower())
    if ext in BINARY_EXTENSIONS:
        return True

    try:
        with open(path, "rb") as f:
            chunk = f.read(BINARY_SNIFF_BYTES)
        if not chunk:
            return False

        # Null bytes indicate binary data
        if b"\x00" in chunk:
            return True

        # Check for invalid text decodings and high ratio of non-printable control characters
        try:
            chunk.decode("utf-8")
        except UnicodeDecodeError:
            control_chars = bytearray({7, 8, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31})
            if any(b in control_chars for b in chunk):
                return True
        return False
    except Exception:
        return True


def _format_fenced_code_block(code: str, language: str) -> str:
    """Format code in a Markdown fence, dynamically extending backticks if code contains fences."""
    max_ticks = 3
    for match in re.finditer(r'`{3,}', code):
        max_ticks = max(max_ticks, len(match.group(0)) + 1)
    fence = '`' * max_ticks
    return f"{fence}{language}\n{code}\n{fence}\n"


# ============================================================
# SECRET SANITIZATION & FILTERING
# ============================================================

SENSITIVE_KEYS = ['api_key', 'token', 'secret', 'password', 'private_key', 'auth']


def sanitize_content(text: str) -> str:
    """Redact sensitive values matching common secret patterns."""
    if not text:
        return text

    for key in SENSITIVE_KEYS:
        text = re.sub(
            rf'({key}\s*[:=]\s*[\'"][^\'"]+[\'"])',
            r'/* REDACTED SENSITIVE VALUE */',
            text,
            flags=re.IGNORECASE
        )
    return text


def _filter_data_for_export(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Defensive export-time filtering.

    Applies persistent scan ignore rules and Explorer session exclusions,
    and unconditionally excludes User_Data.
    """
    from app.core.ignore_manager import get_ignore_manager

    manager = get_ignore_manager()

    def clean(node: Dict[str, Any], is_root: bool = False) -> Optional[Dict[str, Any]]:
        if not isinstance(node, dict):
            return None

        if not is_root:
            name = node.get("name", "")
            abs_path = node.get("abs_path", "")
            rel_path = node.get("path", "")
            if (
                name.startswith(".")
                or name in INTERNAL_NAMES
                or manager.should_ignore_export(name)
                or (rel_path and manager.should_ignore_export(rel_path))
                or (abs_path and manager.should_ignore_export(abs_path))
            ):
                return None

        result = dict(node)
        children = []
        for child in node.get("children", []):
            cleaned = clean(child)
            if cleaned is not None:
                children.append(cleaned)
        result["children"] = children
        return result

    return clean(data, is_root=True) or {}


# ============================================================
# TREE BUILDING
# ============================================================

def _build_tree_string(node: Dict[str, Any], prefix: str = '', depth: int = 0, max_depth: int = 50) -> str:
    """Build tree string with depth limit."""
    if depth > max_depth:
        return f"{prefix}... (truncated - too deep)"

    output = []
    children = node.get('children', [])
    if not children:
        return ''

    sorted_children = sorted(children, key=lambda x: (x.get('type') != 'folder', x.get('name', '').lower()))
    for index, child in enumerate(sorted_children):
        is_last = index == len(sorted_children) - 1
        connector = '└── ' if is_last else '├── '
        new_prefix = prefix + ('    ' if is_last else '│   ')

        name = child.get('name', 'unknown')
        if child.get('type') == 'folder':
            output.append(f"{prefix}{connector}📁 {name}/")
            subtree = _build_tree_string(child, new_prefix, depth + 1, max_depth)
            if subtree:
                output.append(subtree)
        else:
            output.append(f"{prefix}{connector}📄 {name}")
    return '\n'.join(output)


def _collect_all_files(data: Dict[str, Any], max_files: int = 5000) -> List[Dict[str, Any]]:
    """Iteratively collect all files from data structure, sorted by path."""
    all_files = []
    stack = [data]

    while stack and len(all_files) < max_files:
        node = stack.pop(0)
        for child in node.get('children', []):
            if child.get('type') == 'folder':
                stack.append(child)
            elif child.get('type') == 'file':
                all_files.append(child)
                if len(all_files) >= max_files:
                    break

    all_files.sort(key=lambda f: f.get('path', f.get('name', '')).lower())
    return all_files


# ============================================================
# MARKDOWN GENERATION
# ============================================================

def generate_tree_markdown(data: Dict[str, Any]) -> str:
    """Generate Markdown export for 'Tree only' mode."""
    if not data:
        return ""

    root_name = data.get('name', 'Project')
    root_path = data.get('abs_path', data.get('path', ''))

    tree_body = _build_tree_string(data)
    tree_text = f"📁 {root_name}/\n{tree_body}" if tree_body else f"📁 {root_name}/"

    output = [
        f"# {root_name}",
        "> Generated by ContextPot",
        "",
        "## Project Information",
        f"- **Project:** `{root_name}`",
        f"- **Root:** `{root_path}`",
        "- **Export format:** Markdown",
        "- **Purpose:** LLM-ready project context",
        "",
        "```text",
        tree_text,
        "```",
        ""
    ]
    return '\n'.join(output)


def generate_full_markdown(data: Dict[str, Any]) -> str:
    """Generate Markdown export for 'Whole code + Tree' mode."""
    if not data:
        return ""

    root_name = data.get('name', 'Project')
    root_path = data.get('abs_path', data.get('path', ''))

    tree_body = _build_tree_string(data)
    tree_text = f"📁 {root_name}/\n{tree_body}" if tree_body else f"📁 {root_name}/"

    output = [
        f"# {root_name}",
        "> Generated by ContextPot",
        "",
        "## Project Information",
        f"- **Project:** `{root_name}`",
        f"- **Root:** `{root_path}`",
        "- **Export format:** Markdown",
        "- **Purpose:** LLM-ready project context",
        "",
        "```text",
        tree_text,
        "```",
        "",
        "## Code & File Contents",
    ]

    all_files = _collect_all_files(data)

    for file_node in all_files:
        abs_p = file_node.get('abs_path', file_node.get('path', ''))
        rel_p = file_node.get('path', file_node.get('name', ''))
        rel_p = rel_p.replace('\\', '/')
        display_path = _escape_markdown_path(rel_p)
        name = file_node.get('name', os.path.basename(rel_p))

        # Check file size (10 MB limit)
        size_bytes = 0
        if abs_p and os.path.exists(abs_p):
            try:
                size_bytes = os.path.getsize(abs_p)
            except OSError:
                size_bytes = file_node.get('size', 0)
        else:
            size_bytes = file_node.get('size', 0)

        # Check 10 MB limit
        if size_bytes > MAX_FILE_SIZE_BYTES:
            output.append(f"\n### {display_path}\n")
            output.append("> *[File skipped: Exceeds 10 MB limit]*\n")
            continue

        # Check binary
        if abs_p and os.path.exists(abs_p) and _looks_binary(abs_p):
            output.append(f"\n### {display_path}\n")
            output.append("> *[Binary file excluded from text export]*\n")
            continue

        # Read content
        content = file_node.get('content')
        if content is None and abs_p and os.path.exists(abs_p):
            try:
                with open(abs_p, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except Exception as e:
                output.append(f"\n### {display_path}\n")
                output.append(f"> *[Error reading file: {e}]*\n")
                continue

        if content is None:
            content = ""

        sanitized = sanitize_content(content)
        lang = _get_markdown_language(name, abs_p)
        fenced_code = _format_fenced_code_block(sanitized, lang)

        output.append(f"\n### {display_path}\n")
        output.append(fenced_code)

    return '\n'.join(output)


# Backwards compatibility aliases
generate_tree_text = generate_tree_markdown
generate_full_text = generate_full_markdown


# ============================================================
# EXPORT ENTRY POINT
# ============================================================

def export_project_data(data: Dict[str, Any], target_dir: str, mode: str = "Whole code + Tree") -> List[str]:
    """
    Exports scanned project data into the target directory in Markdown format.
    Modes:
    - 'Whole code + Tree' -> {base_name}_full.md
    - 'Tree only'         -> {base_name}_tree.md
    """
    if not data:
        raise ValueError("No project data to export.")

    # Re-apply ignore rules at the exact moment of export
    data = _filter_data_for_export(data)

    if not target_dir or not os.path.isdir(target_dir):
        raise ValueError(f"Target directory does not exist: {target_dir}")

    base_name = data.get('name', 'Project')
    base_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_', '.')).strip()
    if not base_name:
        base_name = 'Project'

    created_files = []

    if "tree" in mode.lower() and "code" not in mode.lower():
        # Tree only -> {base_name}_tree.md
        target_path = get_unique_path(os.path.join(target_dir, f"{base_name}_tree.md"))
        text = generate_tree_markdown(data)
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(text)
        created_files.append(target_path)
    else:
        # Whole code + Tree -> {base_name}_full.md
        target_path = get_unique_path(os.path.join(target_dir, f"{base_name}_full.md"))
        text = generate_full_markdown(data)
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(text)
        created_files.append(target_path)

    return created_files
