"""Covers #40: What's New dialog wiring on MainWindow / LoginWindow."""

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


def test_constructing_main_window_does_not_show_the_dialog(qtbot, monkeypatch):
    # Regression guard: this must NOT be wired into __init__, since every
    # test that constructs MainWindow directly would otherwise hit a real
    # blocking QMessageBox.
    shown = []
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: shown.append(True))

    build_window(qtbot, monkeypatch)

    assert shown == []


def test_maybe_show_whats_new_shows_dialog_when_due(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw, "should_show_whats_new", lambda: True)

    shown = []
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: shown.append(a))
    saved = []
    monkeypatch.setattr(mw, "save_last_seen_version", lambda v: saved.append(v))

    window._maybe_show_whats_new()

    assert len(shown) == 1
    assert saved == [mw.APP_VERSION]


def test_maybe_show_whats_new_skips_when_already_seen(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw, "should_show_whats_new", lambda: False)

    shown = []
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: shown.append(True))
    saved = []
    monkeypatch.setattr(mw, "save_last_seen_version", lambda v: saved.append(v))

    window._maybe_show_whats_new()

    assert shown == []
    assert saved == []
