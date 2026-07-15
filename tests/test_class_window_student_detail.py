"""Covers #23: per-student detail statistics."""

import types

from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import QTableWidgetItem

from models.classes import Class, ScheduleSlot
from views.class_window import ClassWindow


class FakeClassManager:
    def get_student_table(self, class_id):
        return {"columns": ["Student Number", "Student Name Surname"], "rows": []}


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
            "Monday": [ScheduleSlot(day="Monday", start_time=QTime(9, 0), end_time=QTime(10, 50), selected=True)]
        },
        class_id="c1",
    )


def build_window(qtbot):
    main_window = types.SimpleNamespace(load_classes=lambda: None)
    window = ClassWindow(make_class(), main_window, FakeClassManager())
    qtbot.addWidget(window)
    return window


def _set_up_table(window):
    table = window.student_list_tableWidget
    table.setColumnCount(6)
    table.setRowCount(1)
    table.setHorizontalHeaderLabels([
        "Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours",
        "01-09-2025 - 09:00-10:50", "08-09-2025 - 09:00-10:50",
    ])
    table.setItem(0, 0, QTableWidgetItem("20230001"))
    table.setItem(0, 1, QTableWidgetItem("Grace Hopper"))
    table.setItem(0, 2, QTableWidgetItem("1"))
    table.setItem(0, 3, QTableWidgetItem("1"))
    table.setItem(0, 4, QTableWidgetItem("1 Present"))
    table.setItem(0, 5, QTableWidgetItem("0"))


def test_double_clicking_name_column_shows_detail_dialog(qtbot, monkeypatch):
    window = build_window(qtbot)
    _set_up_table(window)

    shown = {}
    monkeypatch.setattr(
        "views.class_window.QMessageBox.information",
        lambda self, title, text: shown.update(title=title, text=text),
    )

    window.handle_roster_cell_double_click(0, 1)

    assert shown["title"] == "Student Detail"
    assert "Grace Hopper (20230001)" in shown["text"]
    assert "Attendance Rate: 50%" in shown["text"]
    assert "01-09-2025 - 09:00-10:50: Present" in shown["text"]
    assert "08-09-2025 - 09:00-10:50: Absent" in shown["text"]


def test_double_clicking_a_session_column_still_opens_correction(qtbot, monkeypatch):
    window = build_window(qtbot)
    _set_up_table(window)

    corrections = []
    monkeypatch.setattr(window, "correct_attendance_cell", lambda row, col: corrections.append((row, col)))

    window.handle_roster_cell_double_click(0, 4)

    assert corrections == [(0, 4)]
