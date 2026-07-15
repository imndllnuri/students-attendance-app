"""Covers #26: session countdown/timer display on Take Attendance."""

import types
from datetime import datetime

from PyQt5.QtCore import QTime

from views.take_attendance_window import TakeAttendance


class FakeSlot:
    def __init__(self, start_time, end_time, selected=True):
        self.start_time = start_time
        self.end_time = end_time
        self.selected = selected


class FakeClassObj:
    def __init__(self, schedule=None):
        self.class_id = "c1"
        self.class_code = "COMP101"
        self.class_name = "COMP101"
        self.late_threshold = 15
        self.schedule = schedule or {}


class FakeClassManager:
    def get_roster(self, class_id):
        return []


def build_window(qtbot, monkeypatch, fake_serial, schedule=None):
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

    window = TakeAttendance(FakeClassObj(schedule), class_window=None, class_manager=FakeClassManager())
    qtbot.addWidget(window)
    return window


def test_no_time_slot_selected_shows_no_countdown(qtbot, monkeypatch, fake_serial):
    window = build_window(qtbot, monkeypatch, fake_serial, schedule={})
    assert window.session_countdown_lbl.text() == ""


def test_session_already_ended_shows_ended_message(qtbot, monkeypatch, fake_serial):
    today_name = datetime.now().strftime("%A")
    schedule = {today_name: [FakeSlot(QTime(0, 0), QTime(0, 1))]}
    window = build_window(qtbot, monkeypatch, fake_serial, schedule)

    assert window.session_countdown_lbl.text() == "Session ended"


def test_session_in_progress_shows_minutes_remaining(qtbot, monkeypatch, fake_serial):
    today_name = datetime.now().strftime("%A")
    schedule = {today_name: [FakeSlot(QTime(0, 0), QTime(23, 59))]}
    window = build_window(qtbot, monkeypatch, fake_serial, schedule)

    text = window.session_countdown_lbl.text()
    assert text.startswith("Time remaining:")
    assert "min" in text
