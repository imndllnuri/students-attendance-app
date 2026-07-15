"""Covers #29: cross-class attendance comparison view."""

import types

import views.main_window as mw
from models.classes import Class


class FakeClassManager:
    def check_server_health(self, *args, **kwargs):
        return True

    def __init__(self, classes, stats_by_id):
        self._classes = classes
        self._stats_by_id = stats_by_id

    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return self._classes

    def get_statistics(self, class_id):
        return self._stats_by_id[class_id]


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def make_class(class_id, code):
    return Class(
        class_code=code,
        class_name=f"{code} Name",
        instructor_id="u1",
        section="1",
        attendance_policy=70,
        late_threshold=15,
        total_weeks=14,
        total_hours=42,
        weekly_hours=3,
        schedule={},
        class_id=class_id,
    )


def build_window(qtbot, monkeypatch, classes, stats_by_id):
    monkeypatch.setattr(mw, "ClassManager", lambda: FakeClassManager(classes, stats_by_id))
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    window.show()
    return window


def test_no_classes_shows_a_message(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, [], {})
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    window.show_class_comparison()

    assert window.statistics_canvas is None


def test_comparison_bar_chart_shows_one_bar_per_class_with_data(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101"), make_class("c2", "COMP102"), make_class("c3", "COMP103")]
    stats = {
        "c1": {"present": 8, "late": 2, "absent": 0},
        "c2": {"present": 5, "late": 0, "absent": 5},
        "c3": {"present": 0, "late": 0, "absent": 0},  # no sessions yet -> excluded
    }
    window = build_window(qtbot, monkeypatch, classes, stats)

    window.show_class_comparison()

    assert window.statistics_canvas is not None
    axes = window.statistics_canvas.figure.axes[0]
    assert len(axes.patches) == 2  # COMP101 and COMP102 bars; COMP103 excluded (no data)


def test_no_classes_have_any_data_shows_empty_state(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101")]
    stats = {"c1": {"present": 0, "late": 0, "absent": 0}}
    window = build_window(qtbot, monkeypatch, classes, stats)
    window.show_statistics()

    window.show_class_comparison()

    assert window.statistics_canvas is None
    assert window.statistics_empty_lbl.isVisible() is True
