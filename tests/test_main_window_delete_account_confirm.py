"""Covers #38: type-your-email confirmation before permanent account deletion."""

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
    def __init__(self):
        self.deleted = False

    def delete_account(self, user_id):
        self.deleted = True
        return True, ""

    def get_login_history(self, user_id, limit=10):
        return []


def build_window(qtbot, monkeypatch):
    monkeypatch.setattr(mw, "ClassManager", FakeClassManager)
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(
        user_id="u1", name="Ada", surname="Lovelace", email="ada@agu.edu.tr"
    )
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def test_matching_email_confirms_deletion(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw.QMessageBox, "question", lambda *a, **k: mw.QMessageBox.Yes)
    monkeypatch.setattr(mw.QInputDialog, "getText", lambda *a, **k: ("ada@agu.edu.tr", True))
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(window, "logout", lambda: None)

    window.confirm_delete_account()

    assert window.account_manager.deleted is True


def test_mismatched_email_cancels_deletion(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw.QMessageBox, "question", lambda *a, **k: mw.QMessageBox.Yes)
    monkeypatch.setattr(mw.QInputDialog, "getText", lambda *a, **k: ("wrong@example.com", True))
    monkeypatch.setattr(mw.QMessageBox, "warning", lambda *a, **k: None)

    window.confirm_delete_account()

    assert window.account_manager.deleted is False


def test_cancelling_the_email_prompt_cancels_deletion(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)
    monkeypatch.setattr(mw.QMessageBox, "question", lambda *a, **k: mw.QMessageBox.Yes)
    monkeypatch.setattr(mw.QInputDialog, "getText", lambda *a, **k: ("", False))

    window.confirm_delete_account()

    assert window.account_manager.deleted is False
