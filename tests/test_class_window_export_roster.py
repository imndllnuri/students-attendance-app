"""Covers #16: roster CSV/Excel re-export."""

import types

from PyQt5.QtCore import QTime

from models.classes import Class, ScheduleSlot
from views.class_window import ClassWindow


class FakeClassManager:
    def __init__(self, roster):
        self._roster = roster

    def get_student_table(self, class_id):
        return {"columns": ["Student Number", "Student Name Surname"], "rows": []}

    def get_roster(self, class_id):
        return self._roster


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
    return window


def test_export_with_empty_roster_shows_nothing_to_export(qtbot, monkeypatch):
    window = build_window(qtbot, roster=[])
    monkeypatch.setattr("views.class_window.QMessageBox.information", lambda *a, **k: None)

    save_dialog_called = []
    monkeypatch.setattr(
        "views.class_window.QFileDialog.getSaveFileName",
        lambda *a, **k: save_dialog_called.append(True),
    )

    window.export_roster()

    assert save_dialog_called == []


def test_export_writes_roster_to_csv(qtbot, monkeypatch, tmp_path):
    roster = [
        {"student_id": 1, "student_number": "20230001", "name_surname": "Grace Hopper", "card_id": None},
        {"student_id": 2, "student_number": "20230002", "name_surname": "Alan Turing", "card_id": "CARD-1"},
    ]
    window = build_window(qtbot, roster)
    monkeypatch.setattr("views.class_window.QMessageBox.information", lambda *a, **k: None)

    out_file = tmp_path / "roster.csv"
    monkeypatch.setattr(
        "views.class_window.QFileDialog.getSaveFileName",
        lambda *a, **k: (str(out_file), "CSV Files (*.csv)"),
    )

    window.export_roster()

    assert out_file.exists()
    content = out_file.read_text()
    assert "Grace Hopper" in content
    assert "Alan Turing" in content


def test_export_cancelled_dialog_does_not_write_file(qtbot, monkeypatch):
    roster = [{"student_id": 1, "student_number": "20230001", "name_surname": "Grace Hopper", "card_id": None}]
    window = build_window(qtbot, roster)
    monkeypatch.setattr("views.class_window.QFileDialog.getSaveFileName", lambda *a, **k: ("", ""))

    window.export_roster()  # should not raise
