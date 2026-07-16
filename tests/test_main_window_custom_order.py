"""Covers #7: drag-and-drop reordering of class cards (Custom Order mode)."""

import types

from PyQt5.QtCore import Qt

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

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return self._classes


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


def test_default_sort_mode_shows_the_grid_not_the_list(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101")]
    window = build_window(qtbot, monkeypatch, classes)
    window.show()

    assert window.class_grid_widget.isVisible() is True
    assert window.custom_order_listWidget.isVisible() is False


def test_custom_order_mode_shows_list_with_saved_order(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101"), make_class("c2", "COMP102")]
    monkeypatch.setattr(mw, "load_class_order", lambda: ["c2", "c1"])
    window = build_window(qtbot, monkeypatch, classes)

    custom_index = window.class_sort_combo.findText("Custom Order")
    window.class_sort_combo.setCurrentIndex(custom_index)

    assert window.custom_order_listWidget.count() == 2
    assert window.custom_order_listWidget.item(0).data(Qt.UserRole) == "c2"
    assert window.custom_order_listWidget.item(1).data(Qt.UserRole) == "c1"


def test_unsaved_classes_appended_after_the_saved_order(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101"), make_class("c2", "COMP102")]
    monkeypatch.setattr(mw, "load_class_order", lambda: ["c1"])
    window = build_window(qtbot, monkeypatch, classes)

    custom_index = window.class_sort_combo.findText("Custom Order")
    window.class_sort_combo.setCurrentIndex(custom_index)

    assert window.custom_order_listWidget.item(0).data(Qt.UserRole) == "c1"
    assert window.custom_order_listWidget.item(1).data(Qt.UserRole) == "c2"


def test_reordering_saves_the_new_order(qtbot, monkeypatch):
    classes = [make_class("c1", "COMP101"), make_class("c2", "COMP102")]
    window = build_window(qtbot, monkeypatch, classes)

    saved = []
    monkeypatch.setattr(mw, "save_class_order", lambda ids: saved.append(ids))

    custom_index = window.class_sort_combo.findText("Custom Order")
    window.class_sort_combo.setCurrentIndex(custom_index)

    # Simulate the drag having reordered the list (drop is handled by Qt;
    # we just move the underlying item and call the persistence hook the
    # rowsMoved signal invokes).
    item = window.custom_order_listWidget.takeItem(0)
    window.custom_order_listWidget.insertItem(1, item)
    window._save_custom_order()

    assert saved == [["c2", "c1"]]
