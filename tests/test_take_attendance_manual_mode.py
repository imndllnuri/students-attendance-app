"""Covers #17: manual attendance mode (mark by clicking, no RFID needed)."""

import types

from views.take_attendance_window import TakeAttendance


class FakeClassObj:
    def __init__(self):
        self.class_id = "c1"
        self.class_code = "COMP101"
        self.class_name = "COMP101"
        self.late_threshold = 15
        self.schedule = {}


class FakeClassManager:
    def __init__(self, roster):
        self._roster = roster
        self.submitted = None

    def get_roster(self, class_id):
        return self._roster


def make_roster():
    return [
        {"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper", "card_id": None},
        {"student_id": 2, "student_number": "2", "name_surname": "Alan Turing", "card_id": None},
    ]


def build_window(qtbot, monkeypatch, fake_serial, roster):
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
    window = TakeAttendance(FakeClassObj(), class_window=None, class_manager=class_manager)
    qtbot.addWidget(window)
    return window, class_manager


def test_manual_entry_stages_a_present_record(qtbot, monkeypatch, fake_serial):
    window, _ = build_window(qtbot, monkeypatch, fake_serial, make_roster())

    responses = iter([("Grace Hopper", True), ("Present", True)])
    monkeypatch.setattr(
        "views.take_attendance_window.QInputDialog.getItem",
        lambda *a, **k: next(responses),
    )

    window.manual_attendance_entry()

    assert window.take_attendance_tableWidget.rowCount() == 1
    assert 1 in window.staged_student_ids


def test_manual_entry_marking_absent_stages_nothing(qtbot, monkeypatch, fake_serial):
    window, _ = build_window(qtbot, monkeypatch, fake_serial, make_roster())

    responses = iter([("Alan Turing", True), ("Absent", True)])
    monkeypatch.setattr(
        "views.take_attendance_window.QInputDialog.getItem",
        lambda *a, **k: next(responses),
    )

    window.manual_attendance_entry()

    assert window.take_attendance_tableWidget.rowCount() == 0
    assert window.staged_student_ids == set()


def test_manual_entry_cancelled_student_pick_does_nothing(qtbot, monkeypatch, fake_serial):
    window, _ = build_window(qtbot, monkeypatch, fake_serial, make_roster())

    monkeypatch.setattr(
        "views.take_attendance_window.QInputDialog.getItem",
        lambda *a, **k: ("Grace Hopper", False),
    )

    window.manual_attendance_entry()

    assert window.take_attendance_tableWidget.rowCount() == 0


def test_manual_entry_only_offers_unstaged_students(qtbot, monkeypatch, fake_serial):
    window, _ = build_window(qtbot, monkeypatch, fake_serial, make_roster())
    window.staged_student_ids.add(1)  # Grace Hopper already recorded

    calls = []

    def fake_get_item(self, title, label, items, index, editable):
        calls.append(list(items))
        return (items[0], True) if items else ("", False)

    monkeypatch.setattr(
        "views.take_attendance_window.QInputDialog.getItem", fake_get_item
    )

    window.manual_attendance_entry()

    assert calls[0] == ["Alan Turing"]  # student-picker only offered the unstaged one
