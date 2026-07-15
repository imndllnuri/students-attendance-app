"""Covers #25: warn before overwriting a student's already-registered card."""

import types

from PyQt5.QtWidgets import QMessageBox

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
        self.registered = None

    def get_roster(self, class_id):
        return self._roster

    def register_card(self, student_id, card_id):
        self.registered = (student_id, card_id)


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
    monkeypatch.setattr(QMessageBox, "exec_", lambda self: None)

    class_manager = FakeClassManager(roster)
    window = TakeAttendance(FakeClassObj(), class_window=None, class_manager=class_manager)
    qtbot.addWidget(window)
    return window, class_manager


def test_registering_a_fresh_card_needs_no_confirmation(qtbot, monkeypatch, fake_serial):
    roster = [{"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper", "card_id": None}]
    window, class_manager = build_window(qtbot, monkeypatch, fake_serial, roster)

    asked = []
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.question", lambda *a, **k: asked.append(True))

    window.register_card("CARD-NEW")

    assert asked == []
    assert class_manager.registered == (1, "CARD-NEW")


def test_overwriting_an_existing_card_requires_confirmation(qtbot, monkeypatch, fake_serial):
    roster = [{"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper", "card_id": "CARD-OLD"}]
    window, class_manager = build_window(qtbot, monkeypatch, fake_serial, roster)
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.question", lambda *a, **k: QMessageBox.Yes)

    window.register_card("CARD-NEW")

    assert class_manager.registered == (1, "CARD-NEW")


def test_declining_the_overwrite_confirmation_cancels_registration(qtbot, monkeypatch, fake_serial):
    roster = [{"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper", "card_id": "CARD-OLD"}]
    window, class_manager = build_window(qtbot, monkeypatch, fake_serial, roster)
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.question", lambda *a, **k: QMessageBox.No)

    window.register_card("CARD-NEW")

    assert class_manager.registered is None
