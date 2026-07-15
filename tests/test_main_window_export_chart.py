"""Covers #26: export the statistics chart as PNG/PDF."""

import types

import views.main_window as mw


class FakeClassManager:
    def check_server_health(self, *args, **kwargs):
        return True

    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []

    def get_statistics(self, class_id):
        return {"present": 5, "late": 1, "absent": 0}

    def get_student_table(self, class_id):
        return {"columns": ["Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours"],
                "rows": []}


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def build_window(qtbot, monkeypatch):
    monkeypatch.setattr(mw, "ClassManager", FakeClassManager)
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def test_export_with_no_chart_shows_nothing_to_export(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    assert window.statistics_canvas is None

    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)
    save_dialog_called = []
    monkeypatch.setattr(
        mw.QFileDialog, "getSaveFileName", lambda *a, **k: save_dialog_called.append(True)
    )

    window.export_statistics_chart()

    assert save_dialog_called == []


def test_export_saves_the_current_figure(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch)

    import types as t
    cls = t.SimpleNamespace(
        class_id="c1", class_code="COMP101", class_name="Intro",
        section="1", total_weeks=14, weekly_hours=3, archived=False,
    )
    window.statistics_class_combo.addItem("Intro (COMP101)", cls)
    window.render_statistics()
    assert window.statistics_canvas is not None

    out_file = tmp_path / "chart.png"
    monkeypatch.setattr(
        mw.QFileDialog, "getSaveFileName", lambda *a, **k: (str(out_file), "PNG Image (*.png)")
    )
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    window.export_statistics_chart()

    assert out_file.exists()
    assert out_file.stat().st_size > 0


def test_export_cancelled_dialog_does_not_write_file(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch)

    import types as t
    cls = t.SimpleNamespace(
        class_id="c1", class_code="COMP101", class_name="Intro",
        section="1", total_weeks=14, weekly_hours=3, archived=False,
    )
    window.statistics_class_combo.addItem("Intro (COMP101)", cls)
    window.render_statistics()

    monkeypatch.setattr(mw.QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))

    window.export_statistics_chart()  # should not raise
