"""The sidebar's profile block (avatar/name/email, directly above Log Out)
should be a clickable shortcut to the Profile page, not decorative-only."""

import types

from PyQt5.QtWidgets import QApplication

import views.main_window as mw


class FakeClassManager:
    def check_server_health(self, *args, **kwargs):
        return True

    def flush_offline_queue(self, *args, **kwargs):
        return 0

    def get_statistics(self, class_id):
        return {"present": 0, "late": 0, "absent": 0}

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def build_window(qtbot, monkeypatch):
    monkeypatch.setattr(mw, "ClassManager", FakeClassManager)
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace", email="ada@example.edu")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    QApplication.instance().removeEventFilter(window)
    return window


def test_clicking_sidebar_profile_block_opens_profile_page(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    window.show_dashboard()

    window.sidebar_profile_widget.mousePressEvent(None)

    assert window.stackedWidget.currentIndex() == mw.PROFILE_PAGE
