"""Tracks whether the "What's New" dialog should be shown once per app
version bump, persisting the last-seen version the same way as the
other local preferences (a plain text file next to the app)."""

from pathlib import Path

LAST_SEEN_VERSION_PATH = Path(".last_seen_version")

APP_VERSION = "1.1.0"

CHANGELOG = [
    "Dark mode and adjustable font size in Settings",
    "Archive, pin/favorite, and drag-to-reorder your classes",
    "Duplicate classes/rosters, plus a merge-students tool for accidental duplicates",
    "Attendance trend chart, heatmap, cross-class comparison, and PDF reports",
    "Offline queueing: attendance submissions retry automatically if the server is unreachable",
]


def load_last_seen_version() -> str:
    if LAST_SEEN_VERSION_PATH.exists():
        return LAST_SEEN_VERSION_PATH.read_text().strip()
    return ""


def save_last_seen_version(version: str) -> None:
    LAST_SEEN_VERSION_PATH.write_text(version)


def should_show_whats_new() -> bool:
    return load_last_seen_version() != APP_VERSION
