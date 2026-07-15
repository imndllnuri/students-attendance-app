"""Covers #14: import multiple classes at once from one spreadsheet."""

import types

import pandas as pd

import views.main_window as mw
from models.classes import Class
from services.api_client import ApiError


class FakeClassManager:
    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def __init__(self):
        self.added = []
        self.fail_codes = set()

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []

    def add_class(self, new_class):
        if new_class.class_code in self.fail_codes:
            raise ApiError("Class code already exists")
        self.added.append(new_class)
        new_class.class_id = f"id-{new_class.class_code}"


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def build_window(qtbot, monkeypatch):
    manager = FakeClassManager()
    monkeypatch.setattr(mw, "ClassManager", lambda: manager)
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window, manager


def make_df(rows):
    return pd.DataFrame(rows, columns=[
        "class_code", "class_name", "section", "attendance_policy",
        "late_threshold", "total_weeks", "total_hours", "weekly_hours",
    ])


def test_cancelled_file_dialog_does_nothing(qtbot, monkeypatch):
    window, manager = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw.QFileDialog, "getOpenFileName", lambda *a, **k: ("", ""))

    window.import_classes_from_spreadsheet()

    assert manager.added == []


def test_missing_required_columns_shows_error(qtbot, monkeypatch):
    window, manager = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw.QFileDialog, "getOpenFileName", lambda *a, **k: ("classes.csv", ""))
    monkeypatch.setattr(mw.pd, "read_csv", lambda *a, **k: pd.DataFrame({"class_code": ["COMP101"]}))

    critical = []
    monkeypatch.setattr(mw.QMessageBox, "critical", lambda *a, **k: critical.append(True))

    window.import_classes_from_spreadsheet()

    assert manager.added == []
    assert critical == [True]


def test_valid_spreadsheet_creates_a_class_per_row(qtbot, monkeypatch):
    window, manager = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw.QFileDialog, "getOpenFileName", lambda *a, **k: ("classes.csv", ""))
    monkeypatch.setattr(mw.pd, "read_csv", lambda *a, **k: make_df([
        ["COMP101", "Intro to Programming", "1", 70, 15, 14, 42, 3],
        ["COMP102", "Data Structures", "1", 70, 15, 14, 42, 3],
    ]))
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    window.import_classes_from_spreadsheet()

    assert [c.class_code for c in manager.added] == ["COMP101", "COMP102"]
    assert manager.added[0].instructor_id == "u1"
    assert manager.added[0].schedule == {}


def test_partial_failures_are_reported(qtbot, monkeypatch):
    window, manager = build_window(qtbot, monkeypatch)
    manager.fail_codes = {"COMP102"}
    monkeypatch.setattr(mw.QFileDialog, "getOpenFileName", lambda *a, **k: ("classes.csv", ""))
    monkeypatch.setattr(mw.pd, "read_csv", lambda *a, **k: make_df([
        ["COMP101", "Intro to Programming", "1", 70, 15, 14, 42, 3],
        ["COMP102", "Data Structures", "1", 70, 15, 14, 42, 3],
    ]))

    warned = []
    monkeypatch.setattr(mw.QMessageBox, "warning", lambda *a, **k: warned.append(True))

    window.import_classes_from_spreadsheet()

    assert [c.class_code for c in manager.added] == ["COMP101"]
    assert warned == [True]
