"""Covers #4: recent logins log on the Profile page."""

import types

import views.main_window as mw


class FakeClassManager:
    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []


class FakeAccountManager:
    def __init__(self, history=None):
        self._history = history if history is not None else []

    def get_login_history(self, user_id, limit=10):
        return self._history[:limit]


def build_window(qtbot, monkeypatch, history):
    monkeypatch.setattr(mw, "ClassManager", FakeClassManager)
    monkeypatch.setattr(mw, "AccountManager", lambda: FakeAccountManager(history))

    user = types.SimpleNamespace(
        user_id="u1", name="Ada", surname="Lovelace", email="ada@agu.edu.tr"
    )
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def test_shows_placeholder_when_no_history(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, history=[])
    window.show_profile()
    assert window.recent_logins_lbl.text() == "No login history yet."


def test_formats_login_timestamps(qtbot, monkeypatch):
    window = build_window(
        qtbot, monkeypatch, history=["2026-07-14T10:00:00+00:00", "2026-07-13T09:30:00+00:00"]
    )
    window.show_profile()
    text = window.recent_logins_lbl.text()
    assert text.count("\n") == 1
    assert "2026" in text
