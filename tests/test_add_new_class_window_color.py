"""Covers #20: manual class tag color override."""

from PyQt5.QtCore import QTime
from PyQt5.QtGui import QColor

import views.add_new_class_window as acw
from models.classes import Class, ScheduleSlot


class FakeClassManager:
    def __init__(self):
        self.added = None
        self.updated = None

    def add_class(self, new_class):
        self.added = new_class
        new_class.class_id = "new-id"

    def update_class(self, class_id, fields):
        self.updated = (class_id, fields)
        return {"class_id": class_id, **fields}


def make_class(color=None):
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
        color=color,
    )


def build_window(qtbot, monkeypatch, **kwargs):
    monkeypatch.setattr(acw, "ClassManager", FakeClassManager)
    monkeypatch.setattr(acw.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(acw.QMessageBox, "warning", lambda *a, **k: None)
    window = acw.AddNewClassWindow("instr-1", **kwargs)
    qtbot.addWidget(window)
    return window


def test_choosing_a_color_sets_selected_color(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(acw.QColorDialog, "getColor", lambda *a, **k: QColor("#FF0000"))

    window.choose_class_color()

    assert window.selected_color == "#ff0000"
    assert "ff0000" in window.class_color_swatch.styleSheet().lower()


def test_cancelling_the_color_dialog_leaves_color_unset(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(acw.QColorDialog, "getColor", lambda *a, **k: QColor())  # invalid color

    window.choose_class_color()

    assert window.selected_color is None


def test_reset_color_clears_selection(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    window.selected_color = "#ff0000"

    window.reset_class_color()

    assert window.selected_color is None
    assert "ff0000" not in window.class_color_swatch.styleSheet().lower()


def test_editing_a_class_prefills_its_existing_color(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, existing_class=make_class(color="#00ff00"))
    assert window.selected_color == "#00ff00"


def test_creating_a_class_includes_selected_color(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, duplicate_from=make_class())
    window.class_code_le.setText("COMP102")
    window.selected_color = "#123456"

    window.create_class()

    assert window.class_manager.added.color == "#123456"


def test_saving_edits_includes_selected_color(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, existing_class=make_class())
    window.selected_color = "#abcdef"

    window.create_class()

    class_id, fields = window.class_manager.updated
    assert fields["color"] == "#abcdef"
