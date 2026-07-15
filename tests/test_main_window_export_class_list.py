"""Covers #13: CSV export of the class list."""

import types

from PyQt5.QtCore import QTime

import views.main_window as mw
from models.classes import Class, ScheduleSlot


class FakeClassManager:
    def __init__(self, classes):
        self._classes = classes

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return self._classes


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def make_class():
    return Class(
        class_code="COMP101",
        class_name="Intro to Programming",
        instructor_id="u1",
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


def build_window(qtbot, monkeypatch, classes):
    monkeypatch.setattr(mw, "ClassManager", lambda: FakeClassManager(classes))
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def test_export_with_no_classes_shows_nothing_to_export(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, [])
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    save_dialog_called = []
    monkeypatch.setattr(mw.QFileDialog, "getSaveFileName", lambda *a, **k: save_dialog_called.append(True))

    window.export_class_list()

    assert save_dialog_called == []


def test_export_writes_class_rows_to_csv(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch, [make_class()])
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    out_file = tmp_path / "classes.csv"
    monkeypatch.setattr(mw.QFileDialog, "getSaveFileName", lambda *a, **k: (str(out_file), "CSV Files (*.csv)"))

    window.export_class_list()

    assert out_file.exists()
    content = out_file.read_text()
    assert "COMP101" in content
    assert "Intro to Programming" in content
    assert "Monday: 09:00-10:50" in content


def test_export_cancelled_dialog_does_not_write_file(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch, [make_class()])
    monkeypatch.setattr(mw.QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))

    window.export_class_list()  # should not raise
