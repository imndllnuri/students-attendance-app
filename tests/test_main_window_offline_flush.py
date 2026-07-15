"""Covers #23: MainWindow retries any queued offline attendance on startup."""

import types

import views.main_window as mw


class FakeClassManager:
    def check_server_health(self, *args, **kwargs):
        return True

    def __init__(self, flushed_count):
        self._flushed_count = flushed_count

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []

    def flush_offline_queue(self):
        return self._flushed_count


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def build_window(qtbot, monkeypatch, flushed_count):
    monkeypatch.setattr(mw, "ClassManager", lambda: FakeClassManager(flushed_count))
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def test_no_queued_records_adds_no_notification(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, flushed_count=0)
    assert window.notifications == []


def test_flushed_records_add_a_notification(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, flushed_count=3)
    assert len(window.notifications) == 1
    assert "3" in window.notifications[0][1]
