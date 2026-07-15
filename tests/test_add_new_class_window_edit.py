"""Covers #11: Edit Class (was previously create-only)."""

from PyQt5.QtCore import QTime

import views.add_new_class_window as acw
from models.classes import Class, ScheduleSlot


class FakeClassManager:
    def __init__(self):
        self.updated = None

    def update_class(self, class_id, fields):
        self.updated = (class_id, fields)
        return {"class_id": class_id, **fields}


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
                ScheduleSlot(
                    day="Monday", start_time=QTime(9, 0), end_time=QTime(10, 50), selected=True
                )
            ]
        },
        class_id="c1",
    )


def build_window(qtbot, monkeypatch, cls):
    monkeypatch.setattr(acw, "ClassManager", FakeClassManager)
    monkeypatch.setattr(acw.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(acw.QMessageBox, "warning", lambda *a, **k: None)
    window = acw.AddNewClassWindow("instr-1", existing_class=cls)
    qtbot.addWidget(window)
    return window


def test_prefills_fields_and_schedule_for_editing(qtbot, monkeypatch):
    cls = make_class()
    window = build_window(qtbot, monkeypatch, cls)

    assert window.class_code_le.text() == "COMP101"
    assert window.class_code_le.isReadOnly()
    assert window.class_name_le.text() == "Intro to Programming"
    assert window.create_class_btn.text() == "Save Changes"
    assert window.monday_cb.isChecked()
    assert window.time_slots["Monday"][0][0].time() == QTime(9, 0)
    assert not window.spreadsheet_file_btn.isVisible()


def test_saving_edits_calls_update_class_not_create(qtbot, monkeypatch):
    cls = make_class()
    window = build_window(qtbot, monkeypatch, cls)

    window.class_name_le.setText("Advanced Programming")
    window.late_threshold_le.setText("20")

    window.create_class()

    class_id, fields = window.class_manager.updated
    assert class_id == "c1"
    assert fields["class_name"] == "Advanced Programming"
    assert fields["late_threshold"] == 20
    assert fields["schedule"]["Monday"][0]["start_time"] == "09:00"
