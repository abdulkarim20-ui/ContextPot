from typing import Dict, Tuple
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

# Canonical name mappings for programming languages
LANGUAGE_DISPLAY_NAMES: Dict[str, str] = {
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "js": "JavaScript",
    "ts": "TypeScript",
    "html": "HTML",
    "css": "CSS",
    "cpp": "C++",
    "c++": "C++",
    "c": "C",
    "csharp": "C#",
    "c#": "C#",
    "rust": "Rust",
    "go": "Go",
    "golang": "Go",
    "java": "Java",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "php": "PHP",
    "ruby": "Ruby",
    "shell": "Shell",
    "bash": "Bash",
    "markdown": "Markdown",
    "json": "JSON",
    "yaml": "YAML",
    "sql": "SQL",
    "vue": "Vue",
    "react": "React",
}

# Optional language-specific color palette (background, text_color)
LANGUAGE_COLORS: Dict[str, Tuple[str, str]] = {
    "python": ("rgba(37, 99, 235, 0.10)", "#1d4ed8"),
    "javascript": ("rgba(202, 138, 4, 0.12)", "#a16207"),
    "typescript": ("rgba(37, 99, 235, 0.12)", "#2563eb"),
    "rust": ("rgba(194, 65, 12, 0.12)", "#c2410c"),
    "go": ("rgba(14, 165, 233, 0.12)", "#0284c7"),
    "java": ("rgba(220, 38, 38, 0.12)", "#b91c1c"),
    "cpp": ("rgba(79, 70, 229, 0.12)", "#4338ca"),
    "csharp": ("rgba(147, 51, 234, 0.12)", "#7e22ce"),
}

DEFAULT_BADGE_STYLE = ("rgba(37, 99, 235, 0.10)", "#1d4ed8")


def format_language_name(lang: str) -> str:
    """Format raw language identifier with proper casing and uppercase rules."""
    key = str(lang or "").strip().lower()
    if key in LANGUAGE_DISPLAY_NAMES:
        return LANGUAGE_DISPLAY_NAMES[key]
    return key.capitalize() if key else "Unknown"


class LanguageBadge(QLabel):
    """
    Modular badge pill displaying repository language with capitalized first character
    and tailored, accessible tag styling.
    """
    def __init__(self, language: str = "Python", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.set_language(language)

    def set_language(self, language: str):
        formatted_name = format_language_name(language)
        self.setText(formatted_name)

        key = str(language or "").strip().lower()
        bg_color, text_color = LANGUAGE_COLORS.get(key, DEFAULT_BADGE_STYLE)

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                font-size: 11px;
                font-weight: 600;
                border-radius: 5px;
                padding: 1px 7px;
                border: none;
            }}
        """)
