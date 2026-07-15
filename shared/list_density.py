"""Persists the My Classes row-density preference (comfortable/compact),
the same way as the theme/language preferences (a plain text file next
to the app)."""

from pathlib import Path

DENSITY_PREFERENCE_PATH = Path(".list_density_preference")


def load_list_density() -> str:
    if DENSITY_PREFERENCE_PATH.exists() and DENSITY_PREFERENCE_PATH.read_text().strip() == "compact":
        return "compact"
    return "comfortable"


def save_list_density(density: str) -> None:
    DENSITY_PREFERENCE_PATH.write_text(density)
