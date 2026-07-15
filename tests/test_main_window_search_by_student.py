"""Covers #10: search by student name, not just class name/code."""

import types

from models.classes import Class
import views.main_window as mw


class FakeClassManager:
    def check_server_health(self, *args, **kwargs):
        return True

    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def __init__(self, classes, rosters):
        self._classes = classes
        self._rosters = rosters

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return self._classes

    def get_roster(self, class_id):
        return self._rosters.get(class_id, [])


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def make_class(code):
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
        class_id=f"c-{code}",
    )


def build_window(qtbot, monkeypatch, classes, rosters):
    monkeypatch.setattr(mw, "ClassManager", lambda: FakeClassManager(classes, rosters))
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def test_search_matches_class_containing_a_student_by_name(qtbot, monkeypatch):
    comp101 = make_class("COMP101")
    comp102 = make_class("COMP102")
    rosters = {
        "c-COMP101": [{"student_id": 1, "name_surname": "Grace Hopper"}],
        "c-COMP102": [{"student_id": 2, "name_surname": "Alan Turing"}],
    }
    window = build_window(qtbot, monkeypatch, [comp101, comp102], rosters)

    window.search_bar_le.setText("hopper")
    window.show_search()

    assert window.search_status_lbl.text() == "1 class(es) found:"
    assert window.search_results_layout.count() == 1


def test_search_still_matches_by_class_code(qtbot, monkeypatch):
    comp101 = make_class("COMP101")
    window = build_window(qtbot, monkeypatch, [comp101], rosters={})

    window.search_bar_le.setText("comp101")
    window.show_search()

    assert window.search_results_layout.count() == 1


def test_search_with_no_matches(qtbot, monkeypatch):
    comp101 = make_class("COMP101")
    rosters = {"c-COMP101": [{"student_id": 1, "name_surname": "Grace Hopper"}]}
    window = build_window(qtbot, monkeypatch, [comp101], rosters)

    window.search_bar_le.setText("nonexistent")
    window.show_search()

    assert window.search_status_lbl.text() == "No matching classes found."
