"""Covers #3: session timeout / auto-logout after inactivity."""

import types

import pytest
from PyQt5.QtWidgets import QApplication

import views.main_window as mw


class FakeClassManager:
    def check_server_health(self, *args, **kwargs):
        return True

    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []


class FakeAccountManager:
    pass


@pytest.fixture
def window(qtbot, monkeypatch):
    monkeypatch.setattr(mw, "ClassManager", FakeClassManager)
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id=1, name="Ada", surname="Lovelace")
    win = mw.MainWindow(user)
    qtbot.addWidget(win)
    yield win
    win._inactivity_timer.stop()
    QApplication.instance().removeEventFilter(win)


def test_inactivity_timer_starts_on_init(window):
    assert window._inactivity_timer.isActive()
    assert window._inactivity_timer.interval() == window.session_timeout_minutes * 60 * 1000


def test_activity_event_resets_the_timer(window):
    window._inactivity_timer.stop()
    assert not window._inactivity_timer.isActive()

    window.eventFilter(window, mw.QEvent(mw.QEvent.KeyPress))
    assert window._inactivity_timer.isActive()
    assert window._inactivity_timer.interval() == window.session_timeout_minutes * 60 * 1000


def test_session_timeout_logs_user_out(window, monkeypatch):
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    logged_out = []
    monkeypatch.setattr(window, "logout", lambda: logged_out.append(True))

    window._handle_session_timeout()

    assert logged_out == [True]
