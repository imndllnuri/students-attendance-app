"""Persists a reusable "session template" per class - the last-saved
default time slot and an optional late-threshold override for Take
Attendance - the same way as the other local preferences (a plain JSON
file next to the app, keyed by class_id)."""

import json
from pathlib import Path

SESSION_TEMPLATES_PATH = Path(".session_templates.json")


def _load_all() -> dict:
    if SESSION_TEMPLATES_PATH.exists():
        try:
            data = json.loads(SESSION_TEMPLATES_PATH.read_text())
        except ValueError:
            return {}
        if isinstance(data, dict):
            return data
    return {}


def load_session_template(class_id: str) -> dict:
    """Returns {"time_slot": str|None, "late_threshold_override": int|None}."""
    template = _load_all().get(class_id, {})
    return {
        "time_slot": template.get("time_slot"),
        "late_threshold_override": template.get("late_threshold_override"),
    }


def save_session_template(class_id: str, time_slot: str, late_threshold_override) -> None:
    all_templates = _load_all()
    all_templates[class_id] = {
        "time_slot": time_slot,
        "late_threshold_override": late_threshold_override,
    }
    SESSION_TEMPLATES_PATH.write_text(json.dumps(all_templates))
