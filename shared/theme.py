"""Light/dark theme preference, persisted across launches the same way
login_window.py remembers the last-used email (a plain text file next to
the app)."""

from pathlib import Path

THEME_PREFERENCE_PATH = Path(".theme_preference")

LIGHT_QSS_PATH = "resources/styles/theme.qss"
DARK_QSS_PATH = "resources/styles/theme_dark.qss"


def load_theme_preference() -> str:
    if THEME_PREFERENCE_PATH.exists() and THEME_PREFERENCE_PATH.read_text().strip() == "dark":
        return "dark"
    return "light"


def save_theme_preference(theme: str) -> None:
    THEME_PREFERENCE_PATH.write_text(theme)


def stylesheet_path(theme: str) -> str:
    return DARK_QSS_PATH if theme == "dark" else LIGHT_QSS_PATH
