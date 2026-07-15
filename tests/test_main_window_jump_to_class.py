"""Covers #12: "Jump to Class" command-palette shortcut (Ctrl+K)."""

import types

import views.main_window as mw
from models.classes import Class


class FakeClassManager:
    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def __init__(self, classes):
        self._classes = classes

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return self._classes


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


def test_no_classes_shows_a_message_and_opens_nothing(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, [])
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    opened = []
    monkeypatch.setattr(window, "open_class_window", lambda c: opened.append(c))

    window.jump_to_class()

    assert opened == []


def test_selecting_a_class_opens_it(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101"), make_class("c2", "COMP102")]
    window = build_window(qtbot, monkeypatch, classes)

    monkeypatch.setattr(
        mw.QInputDialog, "getItem", lambda *a, **k: ("COMP102 Name (COMP102)", True)
    )
    opened = []
    monkeypatch.setattr(window, "open_class_window", lambda c: opened.append(c))

    window.jump_to_class()

    assert opened == [classes[1]]


def test_cancelling_the_dialog_opens_nothing(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101")]
    window = build_window(qtbot, monkeypatch, classes)

    monkeypatch.setattr(mw.QInputDialog, "getItem", lambda *a, **k: ("COMP101 Name (COMP101)", False))
    opened = []
    monkeypatch.setattr(window, "open_class_window", lambda c: opened.append(c))

    window.jump_to_class()

    assert opened == []
