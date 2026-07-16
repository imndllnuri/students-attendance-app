"""Covers #10: "Recently Viewed Classes" quick-access list."""

import types

import views.main_window as mw
from models.classes import Class


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


def test_no_history_shows_placeholder(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    window._populate_recently_viewed([make_class("c1", "COMP101")])

    assert window.no_recently_viewed_lbl.isVisible() is True
    assert window.recently_viewed_layout.count() == 0


def test_tracking_a_class_moves_it_to_the_front(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    c1, c2 = make_class("c1", "COMP101"), make_class("c2", "COMP102")

    window._track_recently_viewed(c1)
    window._track_recently_viewed(c2)
    window._track_recently_viewed(c1)  # re-viewing c1 should bump it back to front

    assert window.recently_viewed_class_ids == ["c1", "c2"]


def test_list_is_capped_at_five(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    for i in range(7):
        window._track_recently_viewed(make_class(f"c{i}", f"COMP{i}"))

    assert len(window.recently_viewed_class_ids) == 5
    assert window.recently_viewed_class_ids[0] == "c6"  # most recent first


def test_populate_shows_tracked_classes_that_still_exist(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    c1 = make_class("c1", "COMP101")
    window._track_recently_viewed(c1)

    window._populate_recently_viewed([c1])

    assert window.no_recently_viewed_lbl.isVisible() is False
    assert window.recently_viewed_layout.count() == 1


def test_open_class_window_tracks_the_class(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    c1 = make_class("c1", "COMP101")
    monkeypatch.setattr(window, "find_class_tab", lambda code: 0)
    fake_class_page = types.SimpleNamespace()
    monkeypatch.setattr(window, "stackedWidget", types.SimpleNamespace(
        setCurrentIndex=lambda i: None,
        widget=lambda i: fake_class_page,
    ))

    window.open_class_window(c1)

    assert window.recently_viewed_class_ids == ["c1"]
