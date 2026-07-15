"""Covers the Kintsugi-redesign Info panel (collapsible right-hand panel on
My Classes, added in Phase 2 of .claude/plans/wild-jingling-unicorn.md)."""

import types

import views.main_window as mw
from models.classes import Class


class FakeClassManager:
    def __init__(self, classes=None):
        self._classes = classes or []

    def check_server_health(self, *args, **kwargs):
        return True

    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def load_classes_for_instructor(self, user_id, include_archived=False):
        if include_archived:
            return self._classes
        return [c for c in self._classes if not c.archived]


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def make_class(class_id, code, pinned=False, archived=False):
    return Class(
        class_code=code, class_name=f"{code} Name", instructor_id="u1", section="1",
        attendance_policy=70, late_threshold=15, total_weeks=14, total_hours=42,
        weekly_hours=3, schedule={}, class_id=class_id, pinned=pinned, archived=archived,
    )


def build_window(qtbot, monkeypatch, classes=None):
    monkeypatch.setattr(mw, "ClassManager", lambda: FakeClassManager(classes))
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace", email="ada@agu.edu.tr")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    window._health_check_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def test_info_panel_starts_expanded(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    assert window._info_panel_expanded is True
    assert window.info_panel_widget.isVisible() or not window.isVisible()


def test_toggle_collapses_then_expands(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)

    window.toggle_info_panel()
    assert window._info_panel_expanded is False
    assert window.info_panel_collapse_btn.text() == "«"

    window.toggle_info_panel()
    assert window._info_panel_expanded is True
    assert window.info_panel_collapse_btn.text() == "»"
    assert window.info_panel_widget.isVisible()


def test_set_info_panel_content_populates_stats_properties_and_tags(qtbot, monkeypatch):
    from PyQt5.QtWidgets import QLabel

    window = build_window(qtbot, monkeypatch)

    window.set_info_panel_content(
        stats=[("Attendance Rate", "82%", 82, None)],
        properties=[("Section", "1"), ("Weekly Hours", "3")],
        tags=[("COMP101", "indigo")],
    )

    assert window.info_panel_stats_layout.count() == 1
    assert window.info_panel_properties_layout.count() == 2
    # tags_layout has 1 pill + 1 trailing stretch item
    assert window.info_panel_tags_layout.count() == 2

    stat_card = window.info_panel_stats_layout.itemAt(0).widget()
    assert any(lbl.text() == "82%" for lbl in stat_card.findChildren(QLabel))


def test_set_info_panel_content_clears_previous_content(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)

    window.set_info_panel_content(
        stats=[("A", "1", 10, None)], properties=[("X", "1")], tags=[("T1", "sky")],
    )
    window.set_info_panel_content(stats=[], properties=[], tags=[])

    assert window.info_panel_stats_layout.count() == 0
    assert window.info_panel_properties_layout.count() == 0
    # tags_layout always keeps a trailing stretch to left-align pills, even
    # when there are no tags to show.
    assert window.info_panel_tags_layout.count() == 1


def test_pinned_items_button_navigates_to_my_classes(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    window.show_settings()

    window.show_pinned_classes()

    assert window.stackedWidget.currentIndex() == mw.MY_CLASSES_PAGE


def test_my_classes_info_panel_shows_aggregate_counts(qtbot, monkeypatch):
    from PyQt5.QtWidgets import QLabel

    classes = [
        make_class("c1", "COMP101", pinned=True),
        make_class("c2", "COMP202", pinned=False),
        make_class("c3", "MATH150", archived=True),
    ]
    window = build_window(qtbot, monkeypatch, classes)

    window.load_classes()

    assert window.info_panel_stats_layout.count() == 2
    active_card = window.info_panel_stats_layout.itemAt(0).widget()
    pinned_card = window.info_panel_stats_layout.itemAt(1).widget()
    assert any(lbl.text() == "2" for lbl in active_card.findChildren(QLabel))  # 2 active
    assert any(lbl.text() == "1" for lbl in pinned_card.findChildren(QLabel))  # 1 pinned

    properties_text = [
        w.text() for i in range(window.info_panel_properties_layout.count())
        for w in window.info_panel_properties_layout.itemAt(i).widget().findChildren(QLabel)
    ]
    assert "Ada Lovelace" in properties_text
    assert "3" in properties_text  # total classes
    assert "1" in properties_text  # archived count


def test_my_classes_info_panel_handles_zero_classes_without_dividing_by_zero(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, classes=[])

    window.load_classes()  # must not raise ZeroDivisionError

    assert window.info_panel_stats_layout.count() == 2
