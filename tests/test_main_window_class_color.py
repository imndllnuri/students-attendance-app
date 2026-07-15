"""Covers #20: manual class tag color override on the My Classes row chip."""

import types

import views.main_window as mw
from models.classes import Class
from shared.palette import class_tag_color


class FakeClassManager:
    def check_server_health(self, *args, **kwargs):
        return True

    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def make_class(color=None):
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
        schedule={},
        class_id="c1",
        color=color,
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


def test_card_illustration_uses_manual_color_override_when_set(qtbot, monkeypatch):
    from PyQt5.QtGui import QColor
    from PyQt5.QtWidgets import QPushButton
    window = build_window(qtbot, monkeypatch)
    card = window._make_class_card_widget(make_class(color="#123456"))
    illustration = card.findChild(QPushButton, "class_card_illustration_btn")
    expected_tint = QColor("#123456").lighter(175).name()
    assert expected_tint in illustration.styleSheet()


def test_card_illustration_falls_back_to_auto_color_when_unset(qtbot, monkeypatch):
    from PyQt5.QtGui import QColor
    from PyQt5.QtWidgets import QPushButton
    window = build_window(qtbot, monkeypatch)
    card = window._make_class_card_widget(make_class(color=None))
    illustration = card.findChild(QPushButton, "class_card_illustration_btn")
    expected_tint = QColor(class_tag_color("COMP101")).lighter(175).name()
    assert expected_tint in illustration.styleSheet()
