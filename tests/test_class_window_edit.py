"""Covers #11: Edit Class button on the class detail page."""

import types

from PyQt5.QtCore import QTime

from models.classes import Class, ScheduleSlot
from views.class_window import ClassWindow


class FakeClassManager:
    def __init__(self, classes):
        self._classes = classes

    def get_student_table(self, class_id):
        return {"columns": ["Student Number", "Student Name Surname"], "rows": []}

    def load_classes_for_instructor(self, instructor_id, include_archived=False):
        return self._classes


def make_class(class_name="Intro to Programming", late_threshold=15):
    return Class(
        class_code="COMP101",
        class_name=class_name,
        instructor_id="instr-1",
        section="1",
        attendance_policy=70,
        late_threshold=late_threshold,
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


def test_edit_button_opens_add_new_class_window_in_edit_mode(qtbot, monkeypatch):
    cls = make_class()
    manager = FakeClassManager([cls])
    main_window = types.SimpleNamespace(load_classes=lambda: None, set_info_panel_content=lambda **k: None)
    window = ClassWindow(cls, main_window, manager)
    qtbot.addWidget(window)

    window.open_edit_class_window()

    assert window.edit_class_window.existing_class is cls
    assert window.edit_class_window.class_code_le.isReadOnly()


def test_reload_after_edit_refreshes_class_details(qtbot, monkeypatch):
    cls = make_class()
    manager = FakeClassManager([cls])
    calls = []
    main_window = types.SimpleNamespace(
        load_classes=lambda: calls.append("reloaded"), set_info_panel_content=lambda **k: None
    )
    window = ClassWindow(cls, main_window, manager)
    qtbot.addWidget(window)

    updated_cls = make_class(class_name="Advanced Programming", late_threshold=20)
    updated_cls.class_id = "c1"
    manager._classes = [updated_cls]

    window._reload_after_edit()

    assert window.class_obj.class_name == "Advanced Programming"
    assert window.class_name_header_lbl.text() == "Advanced Programming"
    assert calls == ["reloaded"]
