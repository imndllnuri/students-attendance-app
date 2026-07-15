"""Covers #5: "Today's Classes" widget with a one-click Take Attendance shortcut."""

import types
from datetime import datetime

from PyQt5.QtCore import QTime

import views.main_window as mw
from models.classes import Class, ScheduleSlot


class FakeClassManager:
    def load_classes_for_instructor(self, user_id):
        return []


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def make_class(code, day, selected=True):
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
        schedule={
            day: [
                ScheduleSlot(
                    day=day, start_time=QTime(9, 0), end_time=QTime(10, 50), selected=selected
                )
            ]
        },
        class_id=f"c-{code}",
    )


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


class FixedWednesday(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 7, 15)  # a Wednesday


def test_only_todays_scheduled_classes_are_shown(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw, "datetime", FixedWednesday)

    wednesday_class = make_class("COMP101", "Wednesday")
    thursday_class = make_class("COMP102", "Thursday")
    unselected_wednesday_class = make_class("COMP103", "Wednesday", selected=False)

    window._populate_today_classes([wednesday_class, thursday_class, unselected_wednesday_class])

    assert window.today_classes_layout.count() == 1
    assert not window.no_classes_today_lbl.isVisible()


def test_empty_state_shown_when_nothing_scheduled_today(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw, "datetime", FixedWednesday)

    thursday_class = make_class("COMP102", "Thursday")
    window._populate_today_classes([thursday_class])

    assert window.today_classes_layout.count() == 0
    assert window.no_classes_today_lbl.isVisible()


def test_take_attendance_button_opens_class_and_shows_attendance_page(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw, "datetime", FixedWednesday)

    calls = []

    class FakeClassPage:
        def attendance_page_show(self):
            calls.append("shown")

    monkeypatch.setattr(window, "open_class_window", lambda cls: FakeClassPage())

    wednesday_class = make_class("COMP101", "Wednesday")
    window.open_take_attendance_for(wednesday_class)

    assert calls == ["shown"]
