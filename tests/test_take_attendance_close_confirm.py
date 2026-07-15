"""Covers #28: confirm closing Take Attendance with unsubmitted records."""

import types

from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMessageBox

from views.take_attendance_window import TakeAttendance


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


class FakeClassManager:
    def __init__(self, roster):
        self._roster = roster
        self.submitted = None

    def get_roster(self, class_id):
        return self._roster

    def submit_attendance(self, class_id, records):
        self.submitted = records


def build_window(qtbot, monkeypatch, fake_serial, roster, class_window=None):
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

    class_manager = FakeClassManager(roster)
    window = TakeAttendance(FakeClassObj(), class_window=class_window, class_manager=class_manager)
    qtbot.addWidget(window)
    return window, class_manager


def make_roster():
    return [{"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper", "card_id": "CARD-A"}]


def test_closing_with_no_staged_records_closes_immediately(qtbot, monkeypatch, fake_serial):
    window, _ = build_window(qtbot, monkeypatch, fake_serial, make_roster())
    event = QCloseEvent()

    window.closeEvent(event)

    assert event.isAccepted()


def test_closing_with_staged_records_prompts_and_can_be_cancelled(qtbot, monkeypatch, fake_serial):
    window, _ = build_window(qtbot, monkeypatch, fake_serial, make_roster())
    fake_serial.push(b"CARD-A\n")
    window.check_rfid()
    assert window.staged_records

    monkeypatch.setattr("views.take_attendance_window.QMessageBox.question", lambda *a, **k: QMessageBox.No)
    event = QCloseEvent()

    window.closeEvent(event)

    assert not event.isAccepted()


def test_closing_with_staged_records_confirmed_proceeds(qtbot, monkeypatch, fake_serial):
    window, _ = build_window(qtbot, monkeypatch, fake_serial, make_roster())
    fake_serial.push(b"CARD-A\n")
    window.check_rfid()
    assert window.staged_records

    monkeypatch.setattr("views.take_attendance_window.QMessageBox.question", lambda *a, **k: QMessageBox.Yes)
    event = QCloseEvent()

    window.closeEvent(event)

    assert event.isAccepted()


def test_successful_submit_clears_staged_records_before_close(qtbot, monkeypatch, fake_serial):
    class_window = FakeClassWindow()
    window, class_manager = build_window(qtbot, monkeypatch, fake_serial, make_roster(), class_window)
    fake_serial.push(b"CARD-A\n")
    window.check_rfid()
    assert window.staged_records

    window.submit_attendance()

    assert window.staged_records == []
    assert class_manager.submitted is not None
    assert class_window.reloaded is True
