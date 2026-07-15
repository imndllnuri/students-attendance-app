"""Covers #27: dark mode toggle in Settings."""

import types

import views.main_window as mw


class FakeClassManager:
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


def test_dark_mode_checkbox_reflects_saved_preference(qtbot, monkeypatch):
    monkeypatch.setattr(mw, "load_theme_preference", lambda: "dark")
    window = build_window(qtbot, monkeypatch)
    assert window.dark_mode_cb.isChecked() is True


def test_toggling_dark_mode_saves_preference_and_restyles_app(qtbot, monkeypatch, tmp_path):
    from PyQt5.QtWidgets import QApplication

    window = build_window(qtbot, monkeypatch)
    app = QApplication.instance()
    original_stylesheet = app.styleSheet()

    saved = []
    monkeypatch.setattr(mw, "save_theme_preference", lambda theme: saved.append(theme))

    fake_qss = tmp_path / "fake.qss"
    fake_qss.write_text("QWidget { color: red; }")
    monkeypatch.setattr(mw, "stylesheet_path", lambda theme: str(fake_qss))

    try:
        window.dark_mode_cb.setChecked(True)

        assert saved == ["dark"]
        assert "color: red" in app.styleSheet()
    finally:
        app.setStyleSheet(original_stylesheet)
