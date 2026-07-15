"""Persists the app-wide font size preference (accessibility scaling),
the same way as the theme/language preferences (a plain text file next
to the app)."""

from pathlib import Path

FONT_SCALE_PREFERENCE_PATH = Path(".font_scale_preference")

BASE_POINT_SIZE = 10
SCALE_FACTORS = {"small": 0.9, "normal": 1.0, "large": 1.15, "extra_large": 1.3}
SCALE_LABELS = {"small": "Small", "normal": "Normal", "large": "Large", "extra_large": "Extra Large"}


def load_font_scale() -> str:
    if FONT_SCALE_PREFERENCE_PATH.exists():
        value = FONT_SCALE_PREFERENCE_PATH.read_text().strip()
        if value in SCALE_FACTORS:
            return value
    return "normal"


def save_font_scale(scale: str) -> None:
    FONT_SCALE_PREFERENCE_PATH.write_text(scale)


def point_size_for_scale(scale: str) -> int:
    return round(BASE_POINT_SIZE * SCALE_FACTORS.get(scale, 1.0))
