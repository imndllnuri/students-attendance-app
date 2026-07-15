"""Covers #43: server connectivity health indicator."""

import types

import views.main_window as mw


class FakeClassManager:
    def __init__(self, healthy=True):
        self._healthy = healthy

    def check_server_health(self, *args, **kwargs):
        return self._healthy

    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def build_window(qtbot, monkeypatch, healthy=True):
    monkeypatch.setattr(mw, "ClassManager", lambda: FakeClassManager(healthy))
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    window._health_check_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def test_healthy_server_shows_connected(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, healthy=True)
    assert window.server_health_lbl.text() == "● Connected"


def test_unreachable_server_shows_offline(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, healthy=False)
    assert window.server_health_lbl.text() == "● Offline"


def test_indicator_updates_on_recheck(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, healthy=True)
    assert window.server_health_lbl.text() == "● Connected"

    window.class_manager._healthy = False
    window.update_server_health_indicator()

    assert window.server_health_lbl.text() == "● Offline"
