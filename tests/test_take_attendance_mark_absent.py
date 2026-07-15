"""Covers #24: bulk "Mark Selected Absent" for cancelled sessions."""

import types

from PyQt5.QtWidgets import QDialog, QListWidget, QListWidgetItem

from views.take_attendance_window import TakeAttendance


class FakeClassObj:
    def __init__(self):
        self.class_id = "c1"
        self.class_code = "COMP101"
        self.class_name = "COMP101"
        self.late_threshold = 15
        self.schedule = {}


class FakeClassManager:
    def get_roster(self, class_id):
        return [
            {"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper", "card_id": None},
            {"student_id": 2, "student_number": "2", "name_surname": "Alan Turing", "card_id": None},
        ]


def build_window(qtbot, monkeypatch, fake_serial):
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

    window = TakeAttendance(FakeClassObj(), class_window=None, class_manager=FakeClassManager())
    qtbot.addWidget(window)
    return window


def test_confirming_dialog_with_selection_marks_absent(qtbot, monkeypatch, fake_serial):
    window = build_window(qtbot, monkeypatch, fake_serial)
    monkeypatch.setattr(QDialog, "exec_", lambda self: QDialog.Accepted)
    monkeypatch.setattr(
        QListWidget, "selectedItems", lambda self: [QListWidgetItem("Grace Hopper")]
    )

    window.mark_selected_absent()

    assert window.take_attendance_tableWidget.rowCount() == 1
    assert window.take_attendance_tableWidget.item(0, 0).text() == "Grace Hopper"
    assert window.take_attendance_tableWidget.item(0, 4).text() == "Absent"
    assert 1 in window.staged_student_ids


def test_cancelling_dialog_marks_nobody(qtbot, monkeypatch, fake_serial):
    window = build_window(qtbot, monkeypatch, fake_serial)
    monkeypatch.setattr(QDialog, "exec_", lambda self: QDialog.Rejected)

    window.mark_selected_absent()

    assert window.take_attendance_tableWidget.rowCount() == 0


def test_confirming_with_no_selection_marks_nobody(qtbot, monkeypatch, fake_serial):
    window = build_window(qtbot, monkeypatch, fake_serial)
    monkeypatch.setattr(QDialog, "exec_", lambda self: QDialog.Accepted)
    monkeypatch.setattr(QListWidget, "selectedItems", lambda self: [])

    window.mark_selected_absent()

    assert window.take_attendance_tableWidget.rowCount() == 0


def test_nothing_to_mark_when_everyone_already_recorded(qtbot, monkeypatch, fake_serial):
    window = build_window(qtbot, monkeypatch, fake_serial)
    informed = []
    monkeypatch.setattr(
        "views.take_attendance_window.QMessageBox.information",
        lambda *a, **k: informed.append(True),
    )
    window.staged_student_ids = {1, 2}

    window.mark_selected_absent()

    assert informed == [True]
