"""Covers #8: pin/favorite classes."""

import types

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton

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
        self.updated = None

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return self._classes

    def update_class(self, class_id, fields):
        self.updated = (class_id, fields)
        return {"class_id": class_id, **fields}


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def make_class(class_id, code, pinned=False):
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
        pinned=pinned,
    )


def build_window(qtbot, monkeypatch, classes):
    monkeypatch.setattr(mw, "ClassManager", lambda: FakeClassManager(classes))
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    window.show_my_classes()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def test_pinned_class_sorts_before_unpinned_by_class_code(qtbot, monkeypatch):
    classes = [make_class("c1", "AAA", pinned=False), make_class("c2", "ZZZ", pinned=True)]
    window = build_window(qtbot, monkeypatch, classes)

    row0 = window.class_btns_layout.itemAt(0).widget()
    label = row0.findChild(QPushButton, "class_row_name_btn")
    assert "ZZZ" in label.text()


def test_toggle_pin_class_calls_update_class_and_reloads(qtbot, monkeypatch):
    cls = make_class("c1", "COMP101", pinned=False)
    window = build_window(qtbot, monkeypatch, [cls])
    monkeypatch.setattr(mw.QMessageBox, "critical", lambda *a, **k: None)

    window.toggle_pin_class(cls)

    assert window.class_manager.updated == ("c1", {"pinned": True})


def test_custom_order_list_shows_pinned_first_with_star(qtbot, monkeypatch):
    classes = [make_class("c1", "AAA", pinned=False), make_class("c2", "ZZZ", pinned=True)]
    monkeypatch.setattr(mw, "load_class_order", lambda: [])
    window = build_window(qtbot, monkeypatch, classes)

    custom_index = window.class_sort_combo.findText("Custom Order")
    window.class_sort_combo.setCurrentIndex(custom_index)

    first_item = window.custom_order_listWidget.item(0)
    assert first_item.data(Qt.UserRole) == "c2"
    assert first_item.text().startswith("★")
