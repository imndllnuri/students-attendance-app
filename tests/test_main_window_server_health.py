"""Covers #43: server connectivity health indicator."""

import types

import views.main_window as mw
from shared.dialogs import ServerConnectionDialog


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


def test_server_connection_button_rebuilds_managers_and_saves_on_accept(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch, healthy=True)
    original_class_manager = window.class_manager
    original_account_manager = window.account_manager

    monkeypatch.setattr(mw, "load_backend_config", lambda: {"backend": "server", "base_url": "http://127.0.0.1:5000", "api_key": ""})
    saved = {}
    monkeypatch.setattr(mw, "save_backend_config", lambda config: saved.update(config))
    monkeypatch.setattr(ServerConnectionDialog, "exec_", lambda self: ServerConnectionDialog.Accepted)
    monkeypatch.setattr(ServerConnectionDialog, "base_url", lambda self: "http://192.168.1.42:5000")
    monkeypatch.setattr(ServerConnectionDialog, "api_key", lambda self: "secret-token")

    window.server_connection_btn.click()

    assert saved["base_url"] == "http://192.168.1.42:5000"
    assert saved["api_key"] == "secret-token"
    assert window.class_manager is not original_class_manager
    assert window.account_manager is not original_account_manager
