"""Covers #23: ClassManager.flush_offline_queue() retries queued submissions."""

import shared.offline_queue as oq
from models.classes import ClassManager
from services.api_client import ApiError


class FakeApiClient:
    def __init__(self, fail_class_ids=frozenset()):
        self.fail_class_ids = fail_class_ids
        self.submitted = []

    def submit_attendance(self, class_id, records):
        if class_id in self.fail_class_ids:
            raise ApiError("still offline")
        self.submitted.append((class_id, records))


def test_flush_with_empty_queue_returns_zero(monkeypatch, tmp_path):
    monkeypatch.setattr(oq, "OFFLINE_QUEUE_PATH", tmp_path / "missing")
    manager = ClassManager(api_client=FakeApiClient())

    assert manager.flush_offline_queue() == 0


def test_flush_resubmits_all_queued_entries_and_clears_the_queue(monkeypatch, tmp_path):
    path = tmp_path / ".offline_attendance_queue.json"
    monkeypatch.setattr(oq, "OFFLINE_QUEUE_PATH", path)
    oq.enqueue("c1", [{"student_id": 1, "status": "Present"}])
    oq.enqueue("c2", [{"student_id": 2, "status": "Late"}])

    fake = FakeApiClient()
    manager = ClassManager(api_client=fake)

    assert manager.flush_offline_queue() == 2
    assert len(fake.submitted) == 2
    assert oq.load_queue() == []


def test_flush_keeps_entries_that_still_fail(monkeypatch, tmp_path):
    path = tmp_path / ".offline_attendance_queue.json"
    monkeypatch.setattr(oq, "OFFLINE_QUEUE_PATH", path)
    oq.enqueue("c1", [{"student_id": 1}])
    oq.enqueue("c2", [{"student_id": 2}])

    fake = FakeApiClient(fail_class_ids={"c2"})
    manager = ClassManager(api_client=fake)

    assert manager.flush_offline_queue() == 1
    remaining = oq.load_queue()
    assert len(remaining) == 1
    assert remaining[0]["class_id"] == "c2"
