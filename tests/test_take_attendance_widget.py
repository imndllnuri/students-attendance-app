"""Widget-level test for the RFID dedup fix: scanning card A, then card B,
then card A again used to insert a second staged row for A. Runs against a
FakeSerial and a fake ClassManager, so no real hardware or server needed.
"""

import types

from views.take_attendance_window import TakeAttendance


class FakeClassObj:
    def __init__(self):
        self.class_id = "c1"
        self.class_name = "COMP101"
        self.late_threshold = 15
        self.schedule = {}


class FakeClassManager:
    def __init__(self, roster):
        self._roster = roster
        self.submitted = None

    def get_roster(self, class_id):
        return self._roster

    def register_card(self, student_id, card_id):
        pass

    def submit_attendance(self, class_id, records):
        self.submitted = records


def make_roster():
    return [
        {"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper", "card_id": "CARD-A"},
        {"student_id": 2, "student_number": "2", "name_surname": "Alan Turing", "card_id": "CARD-B"},
    ]


def build_window(qtbot, monkeypatch, fake_serial, roster):
    monkeypatch.setattr(
        "views.take_attendance_window.serial.tools.list_ports.comports",
        lambda: [types.SimpleNamespace(device="COM_FAKE", description="RFID Reader")],
    )
    monkeypatch.setattr(
        "views.take_attendance_window.serial.Serial", lambda *a, **k: fake_serial
    )
    # These would otherwise pop up blocking modal dialogs during the test.
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.information", lambda *a, **k: None)
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.critical", lambda *a, **k: None)
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.warning", lambda *a, **k: None)

    class_manager = FakeClassManager(roster)
    window = TakeAttendance(FakeClassObj(), class_window=None, class_manager=class_manager)
    qtbot.addWidget(window)
    return window, class_manager


def test_rescanning_a_card_does_not_duplicate_attendance_row(qtbot, monkeypatch, fake_serial):
    window, _ = build_window(qtbot, monkeypatch, fake_serial, make_roster())

    fake_serial.push(b"CARD-A\n")
    window.check_rfid()
    fake_serial.push(b"CARD-B\n")
    window.check_rfid()
    fake_serial.push(b"CARD-A\n")
    window.check_rfid()

    assert window.take_attendance_tableWidget.rowCount() == 2
    assert len(window.staged_records) == 2
    assert {r["student_id"] for r in window.staged_records} == {1, 2}


def test_malformed_serial_bytes_do_not_crash_check_rfid(qtbot, monkeypatch, fake_serial):
    window, _ = build_window(qtbot, monkeypatch, fake_serial, make_roster())

    fake_serial.push(b"\xff\xfe\x00")  # not valid utf-8
    window.check_rfid()  # must not raise

    assert window.take_attendance_tableWidget.rowCount() == 0
