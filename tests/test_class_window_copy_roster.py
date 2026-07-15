"""Covers #21: copy roster from another class."""

import types

from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import QMessageBox

from models.classes import Class, ScheduleSlot
from services.api_client import ApiError
from views.class_window import ClassWindow


class FakeClassManager:
    def __init__(self, classes, rosters):
        self._classes = classes
        self._rosters = rosters
        self.added = []

    def get_student_table(self, class_id):
        return {"columns": ["Student Number", "Student Name Surname"], "rows": []}

    def load_classes_for_instructor(self, instructor_id, include_archived=False):
        return self._classes

    def get_roster(self, class_id):
        return self._rosters.get(class_id, [])

    def add_student(self, class_id, student_number, name_surname):
        self.added.append((class_id, student_number, name_surname))


def make_class(class_id, code):
    return Class(
        class_code=code,
        class_name=f"{code} Name",
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
        class_id=class_id,
    )


def build_window(qtbot, classes, rosters):
    manager = FakeClassManager(classes, rosters)
    main_window = types.SimpleNamespace(load_classes=lambda: None, set_info_panel_content=lambda **k: None)
    window = ClassWindow(classes[0], main_window, manager)
    qtbot.addWidget(window)
    return window, manager


def test_no_other_classes_shows_nothing_to_copy(qtbot, monkeypatch):
    window, manager = build_window(qtbot, [make_class("c1", "COMP101")], {})
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)

    window.copy_roster_from_class()

    assert manager.added == []


def test_copying_a_roster_adds_each_student(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101"), make_class("c2", "COMP102")]
    rosters = {"c2": [
        {"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper"},
        {"student_id": 2, "student_number": "2", "name_surname": "Alan Turing"},
    ]}
    window, manager = build_window(qtbot, classes, rosters)

    monkeypatch.setattr(
        "views.class_window.QInputDialog.getItem",
        lambda *a, **k: ("COMP102 Name (COMP102)", True),
    )
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)

    window.copy_roster_from_class()

    assert manager.added == [
        ("c1", "1", "Grace Hopper"),
        ("c1", "2", "Alan Turing"),
    ]


def test_declining_confirmation_copies_nothing(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101"), make_class("c2", "COMP102")]
    rosters = {"c2": [{"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper"}]}
    window, manager = build_window(qtbot, classes, rosters)

    monkeypatch.setattr(
        "views.class_window.QInputDialog.getItem",
        lambda *a, **k: ("COMP102 Name (COMP102)", True),
    )
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.No)

    window.copy_roster_from_class()

    assert manager.added == []


def test_partial_failures_are_reported(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101"), make_class("c2", "COMP102")]
    rosters = {"c2": [
        {"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper"},
        {"student_id": 2, "student_number": "2", "name_surname": "Alan Turing"},
    ]}
    window, manager = build_window(qtbot, classes, rosters)

    def flaky_add_student(class_id, number, name):
        if name == "Alan Turing":
            raise ApiError("boom")
        manager.added.append((class_id, number, name))

    manager.add_student = flaky_add_student

    monkeypatch.setattr(
        "views.class_window.QInputDialog.getItem",
        lambda *a, **k: ("COMP102 Name (COMP102)", True),
    )
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.Yes)

    warned = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: warned.append(True))

    window.copy_roster_from_class()

    assert manager.added == [("c1", "1", "Grace Hopper")]
    assert warned == [True]
