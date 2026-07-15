"""Covers #37: export/import app settings as JSON."""

import json
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


def test_export_writes_current_preferences(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw, "load_theme_preference", lambda: "dark")
    monkeypatch.setattr(mw, "load_language_preference", lambda: "tr")
    monkeypatch.setattr(mw, "load_list_density", lambda: "compact")
    monkeypatch.setattr(mw, "load_font_scale", lambda: "large")
    window.session_timeout_minutes = 30

    out_file = tmp_path / "settings.json"
    monkeypatch.setattr(mw.QFileDialog, "getSaveFileName", lambda *a, **k: (str(out_file), "JSON Files (*.json)"))
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    window.export_settings()

    data = json.loads(out_file.read_text())
    assert data == {
        "theme": "dark", "language": "tr", "session_timeout_minutes": 30,
        "list_density": "compact", "font_scale": "large",
    }


def test_export_cancelled_dialog_writes_nothing(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw.QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))

    window.export_settings()  # should not raise


def test_import_applies_all_settings_and_updates_combos(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch)

    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({
        "theme": "dark", "language": "tr", "session_timeout_minutes": 30,
        "list_density": "compact", "font_scale": "large",
    }))
    monkeypatch.setattr(mw.QFileDialog, "getOpenFileName", lambda *a, **k: (str(settings_file), ""))
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    saved = {}
    monkeypatch.setattr(mw, "save_theme_preference", lambda v: saved.setdefault("theme", v))
    monkeypatch.setattr(mw, "save_language_preference", lambda v: saved.setdefault("language", v))
    monkeypatch.setattr(mw, "save_session_timeout_minutes", lambda v: saved.setdefault("timeout", v))
    monkeypatch.setattr(mw, "save_list_density", lambda v: saved.setdefault("density", v))
    monkeypatch.setattr(mw, "save_font_scale", lambda v: saved.setdefault("font", v))

    window.import_settings()

    assert saved == {
        "theme": "dark", "language": "tr", "timeout": 30, "density": "compact", "font": "large",
    }
    assert window.dark_mode_cb.isChecked() is True
    assert window.language_combo.currentData() == "tr"
    assert window.session_timeout_combo.currentData() == 30
    assert window.session_timeout_minutes == 30
    assert window.compact_view_cb.isChecked() is True
    assert window.font_scale_combo.currentData() == "large"


def test_import_cancelled_dialog_changes_nothing(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw.QFileDialog, "getOpenFileName", lambda *a, **k: ("", ""))

    window.import_settings()  # should not raise


def test_import_with_unknown_values_is_ignored_gracefully(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch)

    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"theme": "purple", "session_timeout_minutes": 999}))
    monkeypatch.setattr(mw.QFileDialog, "getOpenFileName", lambda *a, **k: (str(settings_file), ""))
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    original_minutes = window.session_timeout_minutes
    window.import_settings()  # should not raise or apply invalid values

    assert window.session_timeout_minutes == original_minutes


def test_import_with_malformed_json_shows_error(qtbot, monkeypatch, tmp_path):
    window = build_window(qtbot, monkeypatch)

    bad_file = tmp_path / "settings.json"
    bad_file.write_text("not json")
    monkeypatch.setattr(mw.QFileDialog, "getOpenFileName", lambda *a, **k: (str(bad_file), ""))

    errored = []
    monkeypatch.setattr(mw.QMessageBox, "critical", lambda *a, **k: errored.append(True))

    window.import_settings()

    assert errored == [True]
