"""Covers #6: updating security questions from Settings now requires two
distinct questions/answers instead of one."""

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
    def __init__(self, update_result=(True, "")):
        self.update_result = update_result
        self.update_calls = []

    def get_login_history(self, user_id, limit=10):
        return []

    def update_security_questions(
        self, user_id, current_password,
        security_question_1, answer_1, security_question_2, answer_2,
    ):
        self.update_calls.append((
            user_id, current_password,
            security_question_1, answer_1, security_question_2, answer_2,
        ))
        return self.update_result


def build_window(qtbot, monkeypatch, account_manager):
    monkeypatch.setattr(mw, "ClassManager", FakeClassManager)
    monkeypatch.setattr(mw, "AccountManager", lambda: account_manager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    window.account_manager = account_manager
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def test_settings_second_combo_defaults_to_a_different_question(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, FakeAccountManager())

    assert (
        window.settings_security_question_combo.currentText()
        != window.settings_security_question_2_combo.currentText()
    )


def test_update_security_questions_sends_both_pairs(qtbot, monkeypatch):
    manager = FakeAccountManager()
    window = build_window(qtbot, monkeypatch, manager)
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    window.settings_current_password_for_question_le.setText("current-pass")
    window.settings_answer_le.setText("Rex")
    window.settings_answer_2_le.setText("London")

    window.update_security_questions()

    assert len(manager.update_calls) == 1
    call = manager.update_calls[0]
    assert call[0] == "u1"
    assert call[1] == "current-pass"
    assert call[2] != call[4]  # the two questions must differ
    assert call[3] == "Rex"
    assert call[5] == "London"


def test_update_security_questions_rejects_identical_questions(qtbot, monkeypatch):
    manager = FakeAccountManager()
    window = build_window(qtbot, monkeypatch, manager)
    window.show()
    window.show_settings()

    window.settings_current_password_for_question_le.setText("current-pass")
    window.settings_answer_le.setText("Rex")
    window.settings_answer_2_le.setText("London")
    window.settings_security_question_2_combo.setCurrentIndex(
        window.settings_security_question_combo.currentIndex()
    )

    window.update_security_questions()

    assert manager.update_calls == []
    assert window.security_question_error_lbl.isVisible() is True


def test_update_security_questions_requires_both_answers(qtbot, monkeypatch):
    manager = FakeAccountManager()
    window = build_window(qtbot, monkeypatch, manager)

    window.settings_current_password_for_question_le.setText("current-pass")
    window.settings_answer_le.setText("Rex")
    window.settings_answer_2_le.setText("")

    window.update_security_questions()

    assert manager.update_calls == []


def test_update_security_questions_shows_error_on_failure(qtbot, monkeypatch):
    manager = FakeAccountManager(update_result=(False, "Current password is incorrect"))
    window = build_window(qtbot, monkeypatch, manager)
    errors = []
    monkeypatch.setattr(mw.QMessageBox, "critical", lambda self, title, msg: errors.append(msg))

    window.settings_current_password_for_question_le.setText("wrong-pass")
    window.settings_answer_le.setText("Rex")
    window.settings_answer_2_le.setText("London")

    window.update_security_questions()

    assert errors == ["Current password is incorrect"]
