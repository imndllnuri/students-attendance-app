"""Covers #9: "Duplicate Class" (copy schedule/policy into a new class)."""

from PyQt5.QtCore import QTime

import views.add_new_class_window as acw
from models.classes import Class, ScheduleSlot


class FakeClassManager:
    def __init__(self):
        self.added = None

    def add_class(self, new_class):
        self.added = new_class
        new_class.class_id = "new-id"


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


def build_window(qtbot, monkeypatch, cls):
    monkeypatch.setattr(acw, "ClassManager", FakeClassManager)
    monkeypatch.setattr(acw.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(acw.QMessageBox, "warning", lambda *a, **k: None)
    window = acw.AddNewClassWindow("instr-1", duplicate_from=cls)
    qtbot.addWidget(window)
    window.show()
    return window


def test_prefills_schedule_and_policy_but_leaves_class_code_blank(qtbot, monkeypatch):
    cls = make_class()
    window = build_window(qtbot, monkeypatch, cls)

    assert window.class_code_le.text() == ""
    assert not window.class_code_le.isReadOnly()
    assert window.class_name_le.text() == "Intro to Programming"
    assert window.create_class_btn.text() == "Create New Class"  # unchanged from create-mode default
    assert window.monday_cb.isChecked()
    assert window.time_slots["Monday"][0][0].time() == QTime(9, 0)
    assert window.spreadsheet_file_btn.isVisible()


def test_saving_creates_a_new_class_not_an_update(qtbot, monkeypatch):
    cls = make_class()
    window = build_window(qtbot, monkeypatch, cls)
    window.class_code_le.setText("COMP101-B")

    window.create_class()

    added = window.class_manager.added
    assert added is not None
    assert added.class_code == "COMP101-B"
    assert added.attendance_policy == 70
    assert "Monday" in added.schedule
