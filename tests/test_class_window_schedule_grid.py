"""Covers #16: visual weekly schedule grid (replacing plain text)."""

import types

from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import QLabel

from models.classes import Class, ScheduleSlot
from views.class_window import ClassWindow


class FakeClassManager:
    def get_student_table(self, class_id):
        return {"columns": ["Student Number", "Student Name Surname"], "rows": []}


def make_class(schedule):
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
        schedule=schedule,
        class_id="c1",
    )


def build_window(qtbot, schedule):
    cls = make_class(schedule)
    main_window = types.SimpleNamespace(load_classes=lambda: None, set_info_panel_content=lambda **k: None)
    window = ClassWindow(cls, main_window, FakeClassManager())
    qtbot.addWidget(window)
    return window


def _grid_labels(window):
    return window.schedule_grid_widget.findChildren(QLabel)


def test_no_schedule_shows_placeholder(qtbot):
    window = build_window(qtbot, schedule={})
    labels = [lbl.text() for lbl in _grid_labels(window)]
    assert labels == ["No schedule set"]


def test_grid_shows_a_column_per_scheduled_day_with_time_chips(qtbot):
    schedule = {
        "Monday": [
            ScheduleSlot(day="Monday", start_time=QTime(9, 0), end_time=QTime(10, 50), selected=True)
        ],
        "Wednesday": [
            ScheduleSlot(day="Wednesday", start_time=QTime(13, 0), end_time=QTime(14, 50), selected=True),
            ScheduleSlot(day="Wednesday", start_time=QTime(15, 0), end_time=QTime(16, 0), selected=True),
        ],
        "Friday": [
            ScheduleSlot(day="Friday", start_time=QTime(8, 0), end_time=QTime(9, 0), selected=False)
        ],
    }
    window = build_window(qtbot, schedule)
    labels = [lbl.text() for lbl in _grid_labels(window)]

    assert "Monday" in labels
    assert "Wednesday" in labels
    assert "Friday" not in labels  # unselected slot -> day is not shown
    assert "09:00 - 10:50" in labels
    assert "13:00 - 14:50" in labels
    assert "15:00 - 16:00" in labels


def test_reload_after_edit_re_renders_the_grid(qtbot):
    window = build_window(qtbot, schedule={
        "Monday": [ScheduleSlot(day="Monday", start_time=QTime(9, 0), end_time=QTime(10, 50), selected=True)]
    })
    assert "09:00 - 10:50" in [lbl.text() for lbl in _grid_labels(window)]

    window.render_schedule_grid({
        "Tuesday": [ScheduleSlot(day="Tuesday", start_time=QTime(11, 0), end_time=QTime(12, 0), selected=True)]
    })
    qtbot.wait(50)  # let deleteLater() from render_schedule_grid's clear step process
    labels = [lbl.text() for lbl in _grid_labels(window)]
    assert "Monday" not in labels
    assert "Tuesday" in labels
    assert "11:00 - 12:00" in labels
