"""Covers #24: "At-Risk Students" list using the existing failure/safe threshold."""

import types

from models.classes import Class
from views.class_window import ClassWindow


class FakeClassManager:
    def __init__(self, rows):
        self._rows = rows

    def get_student_table(self, class_id):
        columns = ["Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours"]
        return {"columns": columns, "rows": self._rows}


def make_class():
    # total_hours=42, attendance_policy=70 -> failure = ceil(42*0.30) = 13, safe = 6.5
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
        schedule={},
        class_id="c1",
    )


def build_window(qtbot, rows):
    main_window = types.SimpleNamespace(load_classes=lambda: None, add_notification=lambda msg: None)
    window = ClassWindow(make_class(), main_window, FakeClassManager(rows))
    qtbot.addWidget(window)
    window.show()
    return window


def test_no_students_at_risk_hides_the_panel(qtbot):
    rows = [["20230001", "Grace Hopper", 2, 10]]
    window = build_window(qtbot, rows)
    assert window.at_risk_widget.isVisible() is False


def test_students_over_safe_threshold_are_listed_worst_first(qtbot):
    rows = [
        ["20230001", "Grace Hopper", 8, 5],   # at risk (safe=6.5, failure=13)
        ["20230002", "Alan Turing", 15, 2],   # failing risk (>= failure=13)
        ["20230003", "Katherine Johnson", 2, 11],  # safe, not listed
    ]
    window = build_window(qtbot, rows)

    text = window.at_risk_students_lbl.text()
    lines = text.split("\n")

    assert lines[0].startswith("Alan Turing")
    assert "FAILING RISK" in lines[0]
    assert lines[1].startswith("Grace Hopper")
    assert "at risk" in lines[1] and "FAILING RISK" not in lines[1]
    assert "Katherine Johnson" not in text


def test_at_risk_widget_hidden_when_roster_empty(qtbot):
    window = build_window(qtbot, rows=[])
    assert window.at_risk_widget.isVisible() is False


def test_at_risk_summary_notifies_main_window(qtbot):
    notified = []
    main_window = types.SimpleNamespace(
        load_classes=lambda: None, add_notification=lambda msg: notified.append(msg)
    )
    rows = [
        ["20230001", "Grace Hopper", 8, 5],
        ["20230002", "Alan Turing", 15, 2],
        ["20230003", "Katherine Johnson", 2, 11],
    ]
    window = ClassWindow(make_class(), main_window, FakeClassManager(rows))
    qtbot.addWidget(window)

    assert notified == ["2 student(s) at risk in COMP101"]
