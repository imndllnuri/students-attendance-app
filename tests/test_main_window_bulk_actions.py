"""Covers #9: bulk actions on the class list (multi-select archive)."""

import types

from PyQt5.QtWidgets import QCheckBox

import views.main_window as mw
from models.classes import Class


class FakeClassManager:
    def check_server_health(self, *args, **kwargs):
        return True

    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def get_statistics(self, class_id):
        return {"present": 0, "late": 0, "absent": 0}

    def __init__(self, classes):
        self._classes = classes
        self.archived_ids = []
        self.fail_ids = set()

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return self._classes

    def archive_class(self, class_id):
        if class_id in self.fail_ids:
            return False
        self.archived_ids.append(class_id)
        return True


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def make_class(class_id, code):
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
        class_id=class_id,
    )


def build_window(qtbot, monkeypatch, classes):
    manager = FakeClassManager(classes)
    monkeypatch.setattr(mw, "ClassManager", lambda: manager)
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window, manager


def test_nothing_selected_shows_a_message(qtbot, monkeypatch):
    window, manager = build_window(qtbot, monkeypatch, [make_class("c1", "COMP101")])
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    window.bulk_archive_selected()

    assert manager.archived_ids == []


def test_selecting_rows_and_archiving_calls_manager_for_each(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101"), make_class("c2", "COMP102")]
    window, manager = build_window(qtbot, monkeypatch, classes)
    monkeypatch.setattr(mw.QMessageBox, "question", lambda *a, **k: mw.QMessageBox.Yes)

    for i in range(window.class_btns_layout.count()):
        row = window.class_btns_layout.itemAt(i).widget()
        row.findChild(QCheckBox).setChecked(True)

    window.bulk_archive_selected()

    assert sorted(manager.archived_ids) == ["c1", "c2"]


def test_declining_confirmation_archives_nothing(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101")]
    window, manager = build_window(qtbot, monkeypatch, classes)
    monkeypatch.setattr(mw.QMessageBox, "question", lambda *a, **k: mw.QMessageBox.No)

    row = window.class_btns_layout.itemAt(0).widget()
    row.findChild(QCheckBox).setChecked(True)

    window.bulk_archive_selected()

    assert manager.archived_ids == []


def test_partial_failures_are_reported(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101"), make_class("c2", "COMP102")]
    window, manager = build_window(qtbot, monkeypatch, classes)
    manager.fail_ids = {"c2"}
    monkeypatch.setattr(mw.QMessageBox, "question", lambda *a, **k: mw.QMessageBox.Yes)

    for i in range(window.class_btns_layout.count()):
        row = window.class_btns_layout.itemAt(i).widget()
        row.findChild(QCheckBox).setChecked(True)

    warned = []
    monkeypatch.setattr(mw.QMessageBox, "warning", lambda *a, **k: warned.append(True))

    window.bulk_archive_selected()

    assert manager.archived_ids == ["c1"]
    assert warned == [True]


def test_selection_resets_after_reload(qtbot, monkeypatch):
    window, manager = build_window(qtbot, monkeypatch, [make_class("c1", "COMP101")])

    row = window.class_btns_layout.itemAt(0).widget()
    row.findChild(QCheckBox).setChecked(True)
    assert window.selected_class_ids == {"c1"}

    window.load_classes()

    assert window.selected_class_ids == set()
