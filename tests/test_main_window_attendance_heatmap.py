"""Covers #32: attendance heatmap by day-of-week/time-slot."""

import types

import views.main_window as mw
from models.classes import Class


class FakeClassManager:
    def __init__(self, table):
        self._table = table

    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []

    def get_student_table(self, class_id):
        return self._table

    def get_statistics(self, class_id):
        return {"present": 0, "late": 0, "absent": 0}


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def make_class(class_id="c1", code="COMP101"):
    return Class(
        class_code=code, class_name=f"{code} Name", instructor_id="u1", section="1",
        attendance_policy=70, late_threshold=15, total_weeks=14, total_hours=42,
        weekly_hours=3, schedule={}, class_id=class_id,
    )


def build_window(qtbot, monkeypatch, table):
    monkeypatch.setattr(mw, "ClassManager", lambda: FakeClassManager(table))
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    window.show_statistics()
    return window


def test_no_class_selected_shows_a_message(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, table={"columns": [], "rows": []})
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    window.show_attendance_heatmap()

    assert window.statistics_canvas is None


def test_heatmap_averages_sessions_sharing_day_and_slot(qtbot, monkeypatch):
    # 01-09-2025 is a Monday, 08-09-2025 is also a Monday.
    columns = [
        "Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours",
        "01-09-2025 - 09:00-10:50", "08-09-2025 - 09:00-10:50",
    ]
    rows = [
        ["1", "Grace Hopper", 0, 2, "1 Present", "1 Present"],
        ["2", "Alan Turing", 1, 1, "1 Present", 0],
    ]
    window = build_window(qtbot, monkeypatch, table={"columns": columns, "rows": rows})
    window.statistics_class_combo.addItem("COMP101 Name (COMP101)", make_class())
    window.statistics_class_combo.setCurrentIndex(0)

    window.show_attendance_heatmap()

    assert window.statistics_canvas is not None
    axes = window.statistics_canvas.figure.axes[0]
    grid = axes.images[0].get_array()
    # Session 1: 2/2 present = 100%; Session 2: 1/2 present = 50%; averaged = 75%.
    assert grid[0, 0] == 75.0


def test_no_sessions_shows_empty_state(qtbot, monkeypatch):
    columns = ["Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours"]
    rows = [["1", "Grace Hopper", 0, 0]]
    window = build_window(qtbot, monkeypatch, table={"columns": columns, "rows": rows})
    window.statistics_class_combo.addItem("COMP101 Name (COMP101)", make_class())
    window.statistics_class_combo.setCurrentIndex(0)

    window.show_attendance_heatmap()

    assert window.statistics_canvas is None
    assert window.statistics_empty_lbl.isVisible() is True
