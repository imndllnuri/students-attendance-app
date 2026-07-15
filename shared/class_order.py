"""Persists the instructor's drag-and-drop custom class ordering, the
same way as the theme/language preferences (a plain text file next to
the app), storing a JSON list of class_ids in display order."""

import json
from pathlib import Path

CLASS_ORDER_PREFERENCE_PATH = Path(".class_order_preference")


def load_class_order() -> list:
    if CLASS_ORDER_PREFERENCE_PATH.exists():
        try:
            data = json.loads(CLASS_ORDER_PREFERENCE_PATH.read_text())
        except ValueError:
            return []
        if isinstance(data, list):
            return data
    return []


def save_class_order(class_ids: list) -> None:
    CLASS_ORDER_PREFERENCE_PATH.write_text(json.dumps(class_ids))
