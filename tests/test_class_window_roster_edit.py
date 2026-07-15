"""Covers #12: add/remove individual roster students after class creation."""

import types

from PyQt5.QtCore import QTime

from models.classes import Class, ScheduleSlot
from views.class_window import ClassWindow


class FakeClassManager:
    def __init__(self, roster):
        self._roster = roster
        self.added = None
        self.removed_ids = []

    def get_student_table(self, class_id):
        return {"columns": ["Student Number", "Student Name Surname"], "rows": []}

    def get_roster(self, class_id):
        return self._roster

    def add_student(self, class_id, student_number, name_surname):
        self.added = (class_id, student_number, name_surname)
        return {"student_id": 99, "student_number": student_number, "name_surname": name_surname}

    def remove_student(self, student_id):
        self.removed_ids.append(student_id)
        return True


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


def test_add_student_calls_manager_and_clears_fields(qtbot, monkeypatch):
    window = build_window(qtbot, roster=[])
    monkeypatch.setattr("views.class_window.QMessageBox.warning", lambda *a, **k: None)

    window.new_student_number_le.setText("20230099")
    window.new_student_name_le.setText("New Student")
    window.add_roster_student()

    assert window.class_manager.added == ("c1", "20230099", "New Student")
    assert window.new_student_number_le.text() == ""
    assert window.new_student_name_le.text() == ""


def test_add_student_rejects_missing_fields(qtbot, monkeypatch):
    window = build_window(qtbot, roster=[])
    warned = []
    monkeypatch.setattr(
        "views.class_window.QMessageBox.warning", lambda *a, **k: warned.append(True)
    )

    window.new_student_number_le.setText("")
    window.new_student_name_le.setText("New Student")
    window.add_roster_student()

    assert window.class_manager.added is None
    assert warned == [True]


def test_remove_selected_student_removes_matching_roster_entry(qtbot, monkeypatch):
    from PyQt5.QtWidgets import QMessageBox

    roster = [{"student_id": 5, "student_number": "20230001", "name_surname": "Grace Hopper"}]
    window = build_window(qtbot, roster=roster)
    monkeypatch.setattr(
        "views.class_window.QMessageBox.question", lambda *a, **k: QMessageBox.Yes
    )

    window.student_list_tableWidget.setRowCount(1)
    window.student_list_tableWidget.setColumnCount(1)
    from PyQt5.QtWidgets import QTableWidgetItem
    window.student_list_tableWidget.setItem(0, 0, QTableWidgetItem("20230001"))
    window.student_list_tableWidget.setCurrentCell(0, 0)

    window.remove_selected_student()

    assert window.class_manager.removed_ids == [5]


def test_remove_selected_student_requires_a_selection(qtbot, monkeypatch):
    window = build_window(qtbot, roster=[])
    warned = []
    monkeypatch.setattr(
        "views.class_window.QMessageBox.warning", lambda *a, **k: warned.append(True)
    )

    window.remove_selected_student()

    assert window.class_manager.removed_ids == []
    assert warned == [True]
