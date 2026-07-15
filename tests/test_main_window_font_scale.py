"""Covers #35: font size selector in Settings."""

import types

import views.main_window as mw


class FakeClassManager:
    def check_server_health(self, *args, **kwargs):
        return True

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


def test_combo_reflects_saved_preference(qtbot, monkeypatch):
    monkeypatch.setattr(mw, "load_font_scale", lambda: "large")
    window = build_window(qtbot, monkeypatch)
    assert window.font_scale_combo.currentData() == "large"


def test_changing_scale_saves_preference_and_updates_app_font(qtbot, monkeypatch):
    from PyQt5.QtWidgets import QApplication

    window = build_window(qtbot, monkeypatch)
    app = QApplication.instance()
    original_point_size = app.font().pointSize()

    saved = []
    monkeypatch.setattr(mw, "save_font_scale", lambda scale: saved.append(scale))

    try:
        large_index = window.font_scale_combo.findData("large")
        window.font_scale_combo.setCurrentIndex(large_index)

        assert saved == ["large"]
        assert app.font().pointSize() == mw.point_size_for_scale("large")
    finally:
        font = app.font()
        font.setPointSize(original_point_size)
        app.setFont(font)
