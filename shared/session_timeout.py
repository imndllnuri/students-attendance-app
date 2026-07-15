"""Configurable inactivity-logout duration, persisted the same way as the
theme/language preferences (a plain text file next to the app)."""

from pathlib import Path

SESSION_TIMEOUT_PREFERENCE_PATH = Path(".session_timeout_preference")
DEFAULT_TIMEOUT_MINUTES = 15
TIMEOUT_OPTIONS = [5, 15, 30, 0]  # 0 means "never"


def load_session_timeout_minutes() -> int:
    if SESSION_TIMEOUT_PREFERENCE_PATH.exists():
        try:
            value = int(SESSION_TIMEOUT_PREFERENCE_PATH.read_text().strip())
        except ValueError:
            return DEFAULT_TIMEOUT_MINUTES
        if value in TIMEOUT_OPTIONS:
            return value
    return DEFAULT_TIMEOUT_MINUTES


def save_session_timeout_minutes(minutes: int) -> None:
    SESSION_TIMEOUT_PREFERENCE_PATH.write_text(str(minutes))
