"""Covers #23: local queue for attendance submissions made while offline."""

import shared.offline_queue as oq


def test_defaults_to_empty_queue_when_no_file(monkeypatch, tmp_path):
    monkeypatch.setattr(oq, "OFFLINE_QUEUE_PATH", tmp_path / "missing")
    assert oq.load_queue() == []


def test_enqueue_then_load_round_trips(monkeypatch, tmp_path):
    path = tmp_path / ".offline_attendance_queue.json"
    monkeypatch.setattr(oq, "OFFLINE_QUEUE_PATH", path)

    oq.enqueue("c1", [{"student_id": 1, "status": "Present"}])

    assert oq.load_queue() == [{"class_id": "c1", "records": [{"student_id": 1, "status": "Present"}]}]


def test_multiple_enqueues_accumulate(monkeypatch, tmp_path):
    path = tmp_path / ".offline_attendance_queue.json"
    monkeypatch.setattr(oq, "OFFLINE_QUEUE_PATH", path)

    oq.enqueue("c1", [{"student_id": 1}])
    oq.enqueue("c2", [{"student_id": 2}])

    assert len(oq.load_queue()) == 2


def test_invalid_json_falls_back_to_empty_list(tmp_path, monkeypatch):
    path = tmp_path / ".offline_attendance_queue.json"
    path.write_text("not json")
    monkeypatch.setattr(oq, "OFFLINE_QUEUE_PATH", path)

    assert oq.load_queue() == []
