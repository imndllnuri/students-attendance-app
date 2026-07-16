"""Covers #6: account creation now collects two distinct security
questions (pick 2 of 3) instead of one."""

import views.login_window as lw


class FakeAccountManager:
    def __init__(self):
        self.added = None

    def add_account(self, account):
        self.added = account
        return True


def build_window(qtbot, monkeypatch, account_manager):
    monkeypatch.setattr(lw, "AccountManager", lambda: account_manager)
    monkeypatch.setattr(lw.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(lw.QMessageBox, "warning", lambda *a, **k: None)
    monkeypatch.setattr(lw.QMessageBox, "critical", lambda *a, **k: None)
    window = lw.LoginWindow()
    qtbot.addWidget(window)
    window.show_sign_up_page()
    return window


def fill_common_fields(window):
    window.signup_email_le.setText("new@example.edu")
    window.signup_password_le.setText("Password123")
    window.password_again_le.setText("Password123")
    window.name_le.setText("Ada")
    window.surname_le.setText("Lovelace")


def test_second_security_question_combo_defaults_to_a_different_question(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, FakeAccountManager())

    assert (
        window.security_question_combo.currentText()
        != window.security_question_2_combo.currentText()
    )


def test_create_account_sends_both_questions_and_answers(qtbot, monkeypatch):
    manager = FakeAccountManager()
    window = build_window(qtbot, monkeypatch, manager)
    fill_common_fields(window)
    window.signup_answer_le.setText("Rex")
    window.signup_answer_2_le.setText("London")

    window.create_account()

    assert manager.added is not None
    assert manager.added.answer_1 == "Rex"
    assert manager.added.answer_2 == "London"
    assert manager.added.security_question_1 != manager.added.security_question_2


def test_create_account_rejects_identical_security_questions(qtbot, monkeypatch):
    manager = FakeAccountManager()
    window = build_window(qtbot, monkeypatch, manager)
    fill_common_fields(window)
    window.signup_answer_le.setText("Rex")
    window.signup_answer_2_le.setText("London")
    window.security_question_2_combo.setCurrentIndex(
        window.security_question_combo.currentIndex()
    )

    window.create_account()

    assert manager.added is None
    assert window.security_questions_error_lbl.isVisible() is True


def test_create_account_requires_both_answers(qtbot, monkeypatch):
    manager = FakeAccountManager()
    window = build_window(qtbot, monkeypatch, manager)
    fill_common_fields(window)
    window.signup_answer_le.setText("Rex")
    window.signup_answer_2_le.setText("")

    window.create_account()

    assert manager.added is None
