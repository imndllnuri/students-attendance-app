"""Covers #8: archive a class instead of hard delete."""

import types

from PyQt5.QtWidgets import QApplication

import views.main_window as mw
from models.classes import Class


class FakeClassManager:
    def __init__(self):
        self.archived_ids = []
        self.unarchived_ids = []

    def load_classes_for_instructor(self, user_id, include_archived=False):
        active = make_class("COMP101", archived=False)
        archived = make_class("COMP102", archived=True)
        if include_archived:
            return [active, archived]
        return [active]

    def archive_class(self, class_id):
        self.archived_ids.append(class_id)
        return True

    def unarchive_class(self, class_id):
        self.unarchived_ids.append(class_id)
        return True


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def make_class(code, archived):
    return Class(
        class_code=code,
        class_name=f"{code} Name",
        instructor_id="u1",
        section="1",
        attendance_policy=70,
        late_threshold=15,
        total_weeks=14,
        total_hours=42,
        weekly_hours=3,
        schedule={},
        class_id=f"c-{code}",
        archived=archived,
    )


def build_window(qtbot, monkeypatch):
    monkeypatch.setattr(mw, "ClassManager", FakeClassManager)
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    QApplication.instance().removeEventFilter(window)
    return window


def test_default_view_shows_only_active_classes(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    assert window.class_btns_layout.count() == 1
    assert window.create_new_class_btn.isVisible()


def test_show_archived_toggles_to_archived_only_view(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    window.show_archived_cb.setChecked(True)

    assert window.class_btns_layout.count() == 1
    assert not window.create_new_class_btn.isVisible()

    row_widget = window.class_btns_layout.itemAt(0).widget()
    button_texts = [
        w.text() for w in row_widget.findChildren(type(window.create_new_class_btn))
    ]
    assert "Unarchive" in button_texts
    assert "Delete Permanently" in button_texts


def test_archive_button_calls_manager_and_reloads(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw.QMessageBox, "question", lambda *a, **k: mw.QMessageBox.Yes)

    cls = make_class("COMP101", archived=False)
    window.archive_class(cls)

    assert window.class_manager.archived_ids == ["c-COMP101"]


def test_unarchive_button_calls_manager(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    cls = make_class("COMP102", archived=True)
    window.unarchive_class(cls)

    assert window.class_manager.unarchived_ids == ["c-COMP102"]


def test_duplicate_button_opens_add_new_class_window_with_duplicate_from(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    cls = make_class("COMP101", archived=False)

    window.open_duplicate_class_window(cls)

    assert window.duplicate_class_window.existing_class is None
    assert window.duplicate_class_window.class_name_le.text() == "COMP101 Name"
