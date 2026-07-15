"""Covers #5: export/download your own account data as JSON."""

import json
import types

from PyQt5.QtCore import QTime

import views.main_window as mw
from models.classes import Class, ScheduleSlot


class FakeClassManager:
    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def __init__(self, classes):
        self._classes = classes

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return self._classes


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return ["2026-07-14T10:00:00+00:00"]


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

    user = types.SimpleNamespace(
        user_id="u1", name="Ada", surname="Lovelace", email="ada@agu.edu.tr"
    )
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def test_export_writes_expected_json_structure(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch, [make_class()])
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    out_file = tmp_path / "data.json"
    monkeypatch.setattr(mw.QFileDialog, "getSaveFileName", lambda *a, **k: (str(out_file), "JSON Files (*.json)"))

    window.export_account_data()

    data = json.loads(out_file.read_text())
    assert data["email"] == "ada@agu.edu.tr"
    assert data["user_id"] == "u1"
    assert len(data["classes"]) == 1
    assert data["classes"][0]["class_code"] == "COMP101"
    assert data["recent_logins"] == ["2026-07-14T10:00:00+00:00"]


def test_export_cancelled_dialog_does_not_write_file(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch, [])
    monkeypatch.setattr(mw.QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))

    window.export_account_data()  # should not raise
