"""Covers #31: downloadable PDF statistics report."""

import types

import views.main_window as mw
from models.classes import Class


class FakeClassManager:
    def __init__(self, stats, table):
        self._stats = stats
        self._table = table

    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []

    def get_statistics(self, class_id):
        return self._stats

    def get_student_table(self, class_id):
        return self._table


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def make_class():
    # total_hours=42, attendance_policy=70 -> failure=13, safe=6.5
    return Class(
        class_code="COMP101", class_name="Intro to Programming", instructor_id="u1",
        section="1", attendance_policy=70, late_threshold=15, total_weeks=14,
        total_hours=42, weekly_hours=3, schedule={}, class_id="c1",
    )


def build_window(qtbot, monkeypatch, stats, table):
    monkeypatch.setattr(mw, "ClassManager", lambda: FakeClassManager(stats, table))
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def empty_table():
    return {"columns": ["Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours"], "rows": []}


def test_no_class_selected_shows_a_message(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, {"present": 0, "late": 0, "absent": 0}, empty_table())
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    save_dialog_called = []
    monkeypatch.setattr(mw.QFileDialog, "getSaveFileName", lambda *a, **k: save_dialog_called.append(True))

    window.export_statistics_pdf()

    assert save_dialog_called == []


def test_export_writes_a_real_pdf_file(qtbot, monkeypatch, tmp_path):
    table = {
        "columns": ["Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours"],
        "rows": [["1", "Grace Hopper", 8, 5], ["2", "Alan Turing", 2, 11]],
    }
    window = build_window(qtbot, monkeypatch, {"present": 15, "late": 3, "absent": 2}, table)
    window.statistics_class_combo.addItem("COMP101 Name (COMP101)", make_class())
    window.statistics_class_combo.setCurrentIndex(0)

    out_file = tmp_path / "report.pdf"
    monkeypatch.setattr(mw.QFileDialog, "getSaveFileName", lambda *a, **k: (str(out_file), "PDF Files (*.pdf)"))
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    window.export_statistics_pdf()

    assert out_file.exists()
    assert out_file.stat().st_size > 0
    assert out_file.read_bytes().startswith(b"%PDF")


def test_export_cancelled_dialog_does_not_write_file(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch, {"present": 0, "late": 0, "absent": 0}, empty_table())
    window.statistics_class_combo.addItem("COMP101 Name (COMP101)", make_class())
    window.statistics_class_combo.setCurrentIndex(0)
    monkeypatch.setattr(mw.QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))

    window.export_statistics_pdf()  # should not raise


def test_at_risk_lines_use_class_threshold(qtbot, monkeypatch):
    table = {
        "columns": ["Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours"],
        "rows": [
            ["1", "Grace Hopper", 8, 5],   # at risk (safe=6.5, failure=13)
            ["2", "Alan Turing", 15, 2],   # failing risk
            ["3", "Katherine Johnson", 2, 11],  # safe, excluded
        ],
    }
    window = build_window(qtbot, monkeypatch, {"present": 0, "late": 0, "absent": 0}, table)

    lines = window._at_risk_lines_for_report(make_class(), table)

    assert len(lines) == 2
    assert any("FAILING RISK" in line and "Alan Turing" in line for line in lines)
    assert any("at risk" in line and "Grace Hopper" in line for line in lines)
    assert not any("Katherine Johnson" in line for line in lines)
