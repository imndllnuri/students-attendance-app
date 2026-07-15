"""Covers #19: class notes/memo field."""

import types

from PyQt5.QtCore import QTime

from models.classes import Class, ScheduleSlot
from views.class_window import ClassWindow


class FakeClassManager:
    def __init__(self):
        self.updated = None

    def get_student_table(self, class_id):
        return {"columns": ["Student Number", "Student Name Surname"], "rows": []}

    def update_class(self, class_id, fields):
        self.updated = (class_id, fields)
        return {"class_id": class_id, **fields}


def make_class(notes=""):
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
        notes=notes,
    )


def build_window(qtbot, cls):
    manager = FakeClassManager()
    main_window = types.SimpleNamespace(load_classes=lambda: None, set_info_panel_content=lambda **k: None)
    window = ClassWindow(cls, main_window, manager)
    qtbot.addWidget(window)
    return window, manager


def test_existing_notes_are_shown_on_load(qtbot):
    window, _ = build_window(qtbot, make_class(notes="TA covers Thursdays."))
    assert window.class_notes_edit.toPlainText() == "TA covers Thursdays."


def test_saving_notes_calls_update_class(qtbot, monkeypatch):
    window, manager = build_window(qtbot, make_class())
    monkeypatch.setattr("views.class_window.QMessageBox.information", lambda *a, **k: None)

    window.class_notes_edit.setPlainText("New note.")
    window.save_class_notes()

    assert manager.updated == ("c1", {"notes": "New note."})
    assert window.class_obj.notes == "New note."
