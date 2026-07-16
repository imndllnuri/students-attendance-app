"""Covers #15: correct/edit a past attendance record."""

import types

from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import QTableWidgetItem

from models.classes import Class, ScheduleSlot
from views.class_window import ClassWindow


class FakeClassManager:
    def __init__(self, roster):
        self._roster = roster
        self.corrections = []

    def get_student_table(self, class_id):
        return {"columns": ["Student Number", "Student Name Surname"], "rows": []}

    def get_roster(self, class_id):
        return self._roster

    def correct_attendance(self, class_id, student_id, date, time_slot, status):
        self.corrections.append((class_id, student_id, date, time_slot, status))
        return {"deleted": status == "Absent"}


def make_class():
    return Class(
        class_code="COMP101",
        class_name="Intro to Programming",
        instructor_id="instr-1",
        section="1",
        attendance_policy=70,
        late_threshold=15,
        total_weeks=14,
        total_hours=42,
        weekly_hours=3,
        schedule={
            "Monday": [
                ScheduleSlot(day="Monday", start_time=QTime(9, 0), end_time=QTime(10, 50), selected=True)
            ]
        },
        class_id="c1",
    )


def build_window(qtbot, roster):
    cls = make_class()
    manager = FakeClassManager(roster)
    main_window = types.SimpleNamespace(load_classes=lambda: None, set_info_panel_content=lambda **k: None)
    window = ClassWindow(cls, main_window, manager)
    qtbot.addWidget(window)
    return window


def _set_up_table(window, header, cell_text):
    table = window.student_list_tableWidget
    table.setColumnCount(5)
    table.setRowCount(1)
    table.setHorizontalHeaderLabels(
        ["Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours", header]
    )
    table.setItem(0, 0, QTableWidgetItem("20230001"))
    table.setItem(0, 1, QTableWidgetItem("Grace Hopper"))
    table.setItem(0, 4, QTableWidgetItem(cell_text))


def test_double_clicking_a_non_session_column_does_nothing(qtbot, monkeypatch):
    roster = [{"student_id": 5, "student_number": "20230001", "name_surname": "Grace Hopper"}]
    window = build_window(qtbot, roster)
    _set_up_table(window, "01-09-2025 - 09:00-10:50", "1 Present")

    window.correct_attendance_cell(0, 0)  # Student Number column

    assert window.class_manager.corrections == []


def test_double_clicking_a_session_cell_prompts_and_corrects(qtbot, monkeypatch):
    roster = [{"student_id": 5, "student_number": "20230001", "name_surname": "Grace Hopper"}]
    window = build_window(qtbot, roster)
    _set_up_table(window, "01-09-2025 - 09:00-10:50", "1 Present")

    monkeypatch.setattr(
        "views.class_window.ChoiceDialog.get_item",
        lambda *a, **k: ("Late", True),
    )

    window.correct_attendance_cell(0, 4)

    assert window.class_manager.corrections == [
        ("c1", 5, "01-09-2025", "09:00-10:50", "Late")
    ]


def test_cancelling_the_dialog_does_not_correct(qtbot, monkeypatch):
    roster = [{"student_id": 5, "student_number": "20230001", "name_surname": "Grace Hopper"}]
    window = build_window(qtbot, roster)
    _set_up_table(window, "01-09-2025 - 09:00-10:50", "1 Present")

    monkeypatch.setattr(
        "views.class_window.ChoiceDialog.get_item",
        lambda *a, **k: ("Late", False),
    )

    window.correct_attendance_cell(0, 4)

    assert window.class_manager.corrections == []


def test_marking_absent_deletes_the_record(qtbot, monkeypatch):
    roster = [{"student_id": 5, "student_number": "20230001", "name_surname": "Grace Hopper"}]
    window = build_window(qtbot, roster)
    _set_up_table(window, "01-09-2025 - 09:00-10:50", "1 Present")

    monkeypatch.setattr(
        "views.class_window.ChoiceDialog.get_item",
        lambda *a, **k: ("Absent", True),
    )

    window.correct_attendance_cell(0, 4)

    assert window.class_manager.corrections == [
        ("c1", 5, "01-09-2025", "09:00-10:50", "Absent")
    ]
