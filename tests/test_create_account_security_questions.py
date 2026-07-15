"""Covers #6: account creation now collects two distinct security
questions (pick 2 of 3) instead of one."""

from views.create_account_window import CreateAccountWindow


class FakeAccountManager:
    def __init__(self):
        self.added = None

    def add_account(self, account):
        self.added = account
        return True


def build_window(qtbot, monkeypatch, account_manager):
    monkeypatch.setattr("views.create_account_window.QMessageBox.information", lambda *a, **k: None)
    monkeypatch.setattr("views.create_account_window.QMessageBox.warning", lambda *a, **k: None)
    monkeypatch.setattr("views.create_account_window.QMessageBox.critical", lambda *a, **k: None)
    window = CreateAccountWindow(account_manager)
    qtbot.addWidget(window)
    return window


def fill_common_fields(window):
    window.email_le.setText("new@example.edu")
    window.password_le.setText("Password123")
    window.password_again_le.setText("Password123")
    window.name_le.setText("Ada")
    window.surname_le.setText("Lovelace")


def test_second_security_question_combo_defaults_to_a_different_question(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch, FakeAccountManager())

    assert (
        window.security_question_ComboBox.currentText()
        != window.security_question_2_ComboBox.currentText()
    )


def test_create_account_sends_both_questions_and_answers(qtbot, monkeypatch):
    manager = FakeAccountManager()
    window = build_window(qtbot, monkeypatch, manager)
    fill_common_fields(window)
    window.answer_le.setText("Rex")
    window.answer_2_le.setText("London")

    window.create_account()

    assert manager.added is not None
    assert manager.added.answer_1 == "Rex"
    assert manager.added.answer_2 == "London"
    assert manager.added.security_question_1 != manager.added.security_question_2


def test_create_account_rejects_identical_security_questions(qtbot, monkeypatch):
    manager = FakeAccountManager()
    window = build_window(qtbot, monkeypatch, manager)
    fill_common_fields(window)
    window.answer_le.setText("Rex")
    window.answer_2_le.setText("London")
    window.security_question_2_ComboBox.setCurrentIndex(
        window.security_question_ComboBox.currentIndex()
    )

    window.create_account()

    assert manager.added is None
    assert window.security_questions_error_lbl.isVisible() is True


def test_create_account_requires_both_answers(qtbot, monkeypatch):
    manager = FakeAccountManager()
    window = build_window(qtbot, monkeypatch, manager)
    fill_common_fields(window)
    window.answer_le.setText("Rex")
    window.answer_2_le.setText("")

    window.create_account()

    assert manager.added is None
