"""Covers #25: attendance trend over time (line chart) on the Statistics page."""

import types

from matplotlib.figure import Figure

import views.main_window as mw


class FakeClassManager:
    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def __init__(self, table):
        self._table = table

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []

    def get_student_table(self, class_id):
        return self._table


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def build_window(qtbot, monkeypatch, table):
    monkeypatch.setattr(mw, "ClassManager", lambda: FakeClassManager(table))
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def make_table():
    columns = [
        "Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours",
        "01-09-2025 - 09:00-10:50", "08-09-2025 - 09:00-10:50",
    ]
    rows = [
        ["1", "Grace Hopper", 0, 2, "1 Present", "1 Late"],
        ["2", "Alan Turing", 1, 1, "1 Present", 0],
    ]
    return {"columns": columns, "rows": rows}


def test_trend_plots_per_session_attendance_rate(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, make_table())
    cls = types.SimpleNamespace(class_id="c1")

    figure = Figure()
    axes = figure.add_subplot(111)
    window._render_attendance_trend(axes, cls)

    assert len(axes.lines) == 1
    y_data = list(axes.lines[0].get_ydata())
    assert y_data == [100.0, 50.0]  # session 1: both present/late; session 2: only 1/2


def test_trend_turns_axis_off_when_no_sessions(qtbot, monkeypatch):
    table = {
        "columns": ["Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours"],
        "rows": [["1", "Grace Hopper", 0, 0]],
    }
    window = build_window(qtbot, monkeypatch, table)
    cls = types.SimpleNamespace(class_id="c1")

    figure = Figure()
    axes = figure.add_subplot(111)
    window._render_attendance_trend(axes, cls)

    assert len(axes.lines) == 0
