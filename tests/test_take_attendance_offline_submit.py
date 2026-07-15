"""Covers #23: submitting attendance while the server is unreachable queues it locally."""

import types

from views.take_attendance_window import TakeAttendance
from services.api_client import ApiError


class FakeClassObj:
    def __init__(self):
        self.class_id = "c1"
        self.class_code = "COMP101"
        self.class_name = "COMP101"
        self.late_threshold = 15
        self.schedule = {}


class FakeClassWindow:
    def __init__(self):
        self.reloaded = False

    def load_student_list(self):
        self.reloaded = True


class OfflineClassManager:
    def get_roster(self, class_id):
        return [{"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper", "card_id": "CARD-A"}]

    def submit_attendance(self, class_id, records):
        raise ApiError("Could not reach the attendance server.")


def build_window(qtbot, monkeypatch, fake_serial, class_window=None):
    monkeypatch.setattr(
        "views.take_attendance_window.serial.tools.list_ports.comports",
        lambda: [types.SimpleNamespace(device="COM_FAKE", description="RFID Reader")],
    )
    monkeypatch.setattr(
        "views.take_attendance_window.serial.Serial", lambda *a, **k: fake_serial
    )
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.information", lambda *a, **k: None)
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.critical", lambda *a, **k: None)
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.warning", lambda *a, **k: None)

    window = TakeAttendance(FakeClassObj(), class_window=class_window, class_manager=OfflineClassManager())
    qtbot.addWidget(window)
    return window


def test_failed_submit_queues_records_locally(qtbot, monkeypatch, fake_serial, tmp_path):
    import shared.offline_queue as oq
    monkeypatch.setattr(oq, "OFFLINE_QUEUE_PATH", tmp_path / ".offline_attendance_queue.json")

    window = build_window(qtbot, monkeypatch, fake_serial)
    fake_serial.push(b"CARD-A\n")
    window.check_rfid()
    assert window.staged_records

    window.submit_attendance()

    queue = oq.load_queue()
    assert len(queue) == 1
    assert queue[0]["class_id"] == "c1"
    assert window.staged_records == []


def test_failed_submit_warns_the_user(qtbot, monkeypatch, fake_serial, tmp_path):
    import shared.offline_queue as oq
    monkeypatch.setattr(oq, "OFFLINE_QUEUE_PATH", tmp_path / ".offline_attendance_queue.json")

    window = build_window(qtbot, monkeypatch, fake_serial)
    fake_serial.push(b"CARD-A\n")
    window.check_rfid()

    warned = []
    monkeypatch.setattr(
        "views.take_attendance_window.QMessageBox.warning",
        lambda *a, **k: warned.append(True),
    )

    window.submit_attendance()

    assert warned == [True]


def test_failed_submit_does_not_reload_the_roster(qtbot, monkeypatch, fake_serial, tmp_path):
    import shared.offline_queue as oq
    monkeypatch.setattr(oq, "OFFLINE_QUEUE_PATH", tmp_path / ".offline_attendance_queue.json")

    class_window = FakeClassWindow()
    window = build_window(qtbot, monkeypatch, fake_serial, class_window)
    fake_serial.push(b"CARD-A\n")
    window.check_rfid()

    window.submit_attendance()

    # Unlike a successful submit, an offline-queued one has nothing new on
    # the server yet, so the roster view isn't refreshed.
    assert class_window.reloaded is False
