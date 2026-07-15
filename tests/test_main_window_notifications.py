"""Covers #29: in-app notification/activity feed."""

import types

import views.main_window as mw


class FakeClassManager:
    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []


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


def test_badge_hidden_with_no_notifications(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    assert window.notifications_badge_lbl.isVisible() is False


def test_adding_a_notification_shows_the_badge_count(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)

    window.add_notification("Roster upload failed: bad file")

    assert window.notifications_badge_lbl.text() == "1"
    assert len(window.notifications) == 1


def test_duplicate_consecutive_notifications_are_not_spammed(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)

    window.add_notification("3 student(s) at risk in COMP101")
    window.add_notification("3 student(s) at risk in COMP101")
    window.add_notification("3 student(s) at risk in COMP101")

    assert len(window.notifications) == 1


def test_clear_notifications_resets_the_badge(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    window.add_notification("Something happened")

    window.clear_notifications()

    assert window.notifications == []
    assert window.notifications_badge_lbl.isVisible() is False


def test_roster_upload_failure_signal_adds_a_notification(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)

    class FakeAddNewClassWindow:
        class_created = types.SimpleNamespace(connect=lambda *a, **k: None)

        def __init__(self, *a, **k):
            self.roster_load_failed = _FakeSignal()

        def show(self):
            pass

    class _FakeSignal:
        def __init__(self):
            self._slot = None

        def connect(self, slot):
            self._slot = slot

        def emit(self, *args):
            self._slot(*args)

    monkeypatch.setattr(mw, "AddNewClassWindow", FakeAddNewClassWindow)
    window.open_add_new_class_window()
    window.add_new_class_window.roster_load_failed.emit("bad header row")

    assert window.notifications[-1][1] == "Roster upload failed: bad header row"
