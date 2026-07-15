"""Covers #11: class list density toggle (comfortable vs compact)."""

import types

import views.main_window as mw
from models.classes import Class


class FakeClassManager:
    def check_server_health(self, *args, **kwargs):
        return True

    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return [make_class()]


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def make_class():
    return Class(
        class_code="COMP101",
        class_name="Intro to Programming",
        instructor_id="u1",
        section="1",
        attendance_policy=70,
        late_threshold=15,
        total_weeks=14,
        total_hours=42,
        weekly_hours=3,
        schedule={},
        class_id="c1",
    )


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


def test_defaults_to_comfortable_with_visible_caption(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    window.show()
    assert window.compact_view_cb.isChecked() is False

    row = window.class_btns_layout.itemAt(0).widget()
    from PyQt5.QtWidgets import QLabel
    caption = row.findChild(QLabel, "class_row_caption_lbl")
    assert caption.isVisible() is True


def test_checkbox_reflects_saved_preference(qtbot, monkeypatch):
    monkeypatch.setattr(mw, "load_list_density", lambda: "compact")
    window = build_window(qtbot, monkeypatch)
    assert window.compact_view_cb.isChecked() is True


def test_enabling_compact_saves_preference_and_hides_captions(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)

    saved = []
    monkeypatch.setattr(mw, "save_list_density", lambda density: saved.append(density))

    window.compact_view_cb.setChecked(True)

    assert saved == ["compact"]
    row = window.class_btns_layout.itemAt(0).widget()
    from PyQt5.QtWidgets import QLabel
    caption = row.findChild(QLabel, "class_row_caption_lbl")
    assert caption.isVisible() is False
