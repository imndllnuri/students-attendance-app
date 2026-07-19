"""Covers the login screen's gear icon: lets the user point the app at a
TapIn server before logging in, since AccountManager() is built before any
user interaction and the only in-app Settings screen otherwise lives
inside MainWindow, unreachable without a successful login first."""

import views.login_window as lw
from shared.dialogs import ServerConnectionDialog


class FakeAccountManager:
    pass


def build_window(qtbot, monkeypatch):
    monkeypatch.setattr(lw, "AccountManager", FakeAccountManager)
    window = lw.LoginWindow()
    qtbot.addWidget(window)
    return window


def test_server_settings_button_opens_dialog_and_saves_on_accept(qtbot, monkeypatch, tmp_path):
    config_path = tmp_path / ".backend_config.json"
    monkeypatch.setattr(lw, "load_backend_config", lambda: {"backend": "server", "base_url": "http://127.0.0.1:5000", "api_key": ""})
    saved = {}
    monkeypatch.setattr(lw, "save_backend_config", lambda config: saved.update(config))
    monkeypatch.setattr(ServerConnectionDialog, "exec_", lambda self: ServerConnectionDialog.Accepted)
    monkeypatch.setattr(ServerConnectionDialog, "base_url", lambda self: "http://192.168.1.42:5000")
    monkeypatch.setattr(ServerConnectionDialog, "api_key", lambda self: "secret-token")

    window = build_window(qtbot, monkeypatch)
    original_manager = window.account_manager

    window.show_server_connection_dialog()

    assert saved["base_url"] == "http://192.168.1.42:5000"
    assert saved["api_key"] == "secret-token"
    assert window.account_manager is not original_manager


def test_server_settings_button_does_nothing_on_cancel(qtbot, monkeypatch):
    monkeypatch.setattr(lw, "load_backend_config", lambda: {"backend": "server", "base_url": "http://127.0.0.1:5000", "api_key": ""})
    saved = {}
    monkeypatch.setattr(lw, "save_backend_config", lambda config: saved.update(config))
    monkeypatch.setattr(ServerConnectionDialog, "exec_", lambda self: ServerConnectionDialog.Rejected)

    window = build_window(qtbot, monkeypatch)
    original_manager = window.account_manager

    window.show_server_connection_dialog()

    assert saved == {}
    assert window.account_manager is original_manager
