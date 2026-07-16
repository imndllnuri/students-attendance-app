"""Covers #18: merge student tool for accidental duplicate roster entries."""

import types

from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import QMessageBox

from models.classes import Class, ScheduleSlot
from views.class_window import ClassWindow


class FakeClassManager:
    def __init__(self, roster):
        self._roster = roster
        self.merged = None

    def get_student_table(self, class_id):
        return {"columns": ["Student Number", "Student Name Surname"], "rows": []}

    def get_roster(self, class_id):
        return self._roster

    def merge_students(self, keep_student_id, remove_student_id):
        self.merged = (keep_student_id, remove_student_id)
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
            "Monday": [ScheduleSlot(day="Monday", start_time=QTime(9, 0), end_time=QTime(10, 50), selected=True)]
        },
        class_id="c1",
    )


def build_window(qtbot, roster):
    manager = FakeClassManager(roster)
    main_window = types.SimpleNamespace(load_classes=lambda: None, set_info_panel_content=lambda **k: None)
    window = ClassWindow(make_class(), main_window, manager)
    qtbot.addWidget(window)
    return window, manager


def test_fewer_than_two_students_shows_nothing_to_merge(qtbot, monkeypatch):
    roster = [{"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper"}]
    window, manager = build_window(qtbot, roster)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)

    window.merge_students()

    assert manager.merged is None


def test_merging_two_students_calls_manager_with_keep_and_remove_ids(qtbot, monkeypatch):
    roster = [
        {"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper"},
        {"student_id": 2, "student_number": "2", "name_surname": "Grace H."},
    ]
    window, manager = build_window(qtbot, roster)

    responses = iter([
        ("Grace Hopper (1)", True),
        ("Grace H. (2)", True),
    ])
    monkeypatch.setattr(
        "views.class_window.ChoiceDialog.get_item", lambda *a, **k: next(responses)
    )
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)

    window.merge_students()

    assert manager.merged == (1, 2)


def test_declining_confirmation_does_not_merge(qtbot, monkeypatch):
    roster = [
        {"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper"},
        {"student_id": 2, "student_number": "2", "name_surname": "Grace H."},
    ]
    window, manager = build_window(qtbot, roster)

    responses = iter([
        ("Grace Hopper (1)", True),
        ("Grace H. (2)", True),
    ])
    monkeypatch.setattr(
        "views.class_window.ChoiceDialog.get_item", lambda *a, **k: next(responses)
    )
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.No)

    window.merge_students()

    assert manager.merged is None


def test_cancelling_first_pick_does_not_merge(qtbot, monkeypatch):
    roster = [
        {"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper"},
        {"student_id": 2, "student_number": "2", "name_surname": "Grace H."},
    ]
    window, manager = build_window(qtbot, roster)

    monkeypatch.setattr(
        "views.class_window.ChoiceDialog.get_item",
        lambda *a, **k: ("Grace Hopper (1)", False),
    )

    window.merge_students()

    assert manager.merged is None
