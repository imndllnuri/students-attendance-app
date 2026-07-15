"""Local queue for attendance submissions that failed because the server
was unreachable (#23), persisted as JSON next to the app so a retry can
happen on a later run even if the app was closed in between."""

import json
from pathlib import Path

OFFLINE_QUEUE_PATH = Path(".offline_attendance_queue.json")


def load_queue() -> list:
    if OFFLINE_QUEUE_PATH.exists():
        try:
            data = json.loads(OFFLINE_QUEUE_PATH.read_text())
        except ValueError:
            return []
        if isinstance(data, list):
            return data
    return []


def save_queue(queue: list) -> None:
    OFFLINE_QUEUE_PATH.write_text(json.dumps(queue))


def enqueue(class_id, records: list) -> None:
    queue = load_queue()
    queue.append({"class_id": class_id, "records": records})
    save_queue(queue)
