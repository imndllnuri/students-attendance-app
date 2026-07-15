"""Covers #36: configurable session-timeout duration."""

import types

from PyQt5.QtWidgets import QApplication

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
    return window


def teardown(window):
    window._inactivity_timer.stop()
    QApplication.instance().removeEventFilter(window)


def test_combo_reflects_saved_preference(qtbot, monkeypatch, tmp_path):
    pref_path = tmp_path / ".session_timeout_preference"
    pref_path.write_text("30")
    monkeypatch.setattr(mw, "load_session_timeout_minutes", lambda: 30)

    window = build_window(qtbot, monkeypatch)
    try:
        assert window.session_timeout_minutes == 30
        assert window.session_timeout_combo.currentData() == 30
        assert window._inactivity_timer.interval() == 30 * 60 * 1000
    finally:
        teardown(window)


def test_changing_timeout_saves_preference_and_restarts_timer(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    try:
        saved = []
        monkeypatch.setattr(mw, "save_session_timeout_minutes", lambda minutes: saved.append(minutes))

        five_min_index = window.session_timeout_combo.findData(5)
        window.session_timeout_combo.setCurrentIndex(five_min_index)

        assert saved == [5]
        assert window.session_timeout_minutes == 5
        assert window._inactivity_timer.interval() == 5 * 60 * 1000
    finally:
        teardown(window)


def test_never_option_stops_the_timer(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    try:
        monkeypatch.setattr(mw, "save_session_timeout_minutes", lambda minutes: None)
        never_index = window.session_timeout_combo.findData(0)
        window.session_timeout_combo.setCurrentIndex(never_index)

        assert window.session_timeout_minutes == 0
        assert not window._inactivity_timer.isActive()
    finally:
        teardown(window)
