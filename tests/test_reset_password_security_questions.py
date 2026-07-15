"""Covers #6: password reset now requires answering both of the
account's two security questions, not just one."""

from views.reset_password_window import ResetPasswordWindow


class FakeAccountManager:
    def __init__(self, questions=None, reset_result=(True, "")):
        self.questions = questions or ["What was your first pet's name?", "What city were you born in?"]
        self.reset_result = reset_result
        self.reset_calls = []

    def get_security_questions(self, email):
        return self.questions

    def reset_password(self, email, answer_1, answer_2, new_password):
        self.reset_calls.append((email, answer_1, answer_2, new_password))
        return self.reset_result


def build_window(qtbot, monkeypatch, account_manager):
    monkeypatch.setattr("views.reset_password_window.QMessageBox.information", lambda *a, **k: None)
    monkeypatch.setattr("views.reset_password_window.QMessageBox.warning", lambda *a, **k: None)
    monkeypatch.setattr("views.reset_password_window.QMessageBox.critical", lambda *a, **k: None)
    window = ResetPasswordWindow(account_manager)
    qtbot.addWidget(window)
    return window


def test_fetch_question_shows_both_security_questions(qtbot, monkeypatch):
    manager = FakeAccountManager()
    window = build_window(qtbot, monkeypatch, manager)
    window.email_le.setText("a@b.com")

    window.fetch_question()

    assert window.security_question_lbl.text() == manager.questions[0]
    assert window.security_question_2_lbl.text() == manager.questions[1]
    assert window.steps_stack.currentIndex() == 1


def test_submit_reset_requires_both_answers(qtbot, monkeypatch):
    manager = FakeAccountManager()
    window = build_window(qtbot, monkeypatch, manager)
    window.email_le.setText("a@b.com")
    window.fetch_question()

    window.answer_le.setText("Rex")
    window.answer_2_le.setText("")
    window.new_password_le.setText("NewPass123")
    window.confirm_password_le.setText("NewPass123")

    window.submit_reset()

    assert manager.reset_calls == []


def test_submit_reset_sends_both_answers_to_the_manager(qtbot, monkeypatch):
    manager = FakeAccountManager()
    window = build_window(qtbot, monkeypatch, manager)
    window.email_le.setText("a@b.com")
    window.fetch_question()

    window.answer_le.setText("Rex")
    window.answer_2_le.setText("London")
    window.new_password_le.setText("NewPass123")
    window.confirm_password_le.setText("NewPass123")

    window.submit_reset()

    assert manager.reset_calls == [("a@b.com", "Rex", "London", "NewPass123")]


def test_submit_reset_shows_error_when_an_answer_is_wrong(qtbot, monkeypatch):
    manager = FakeAccountManager(reset_result=(False, "One or more security answers are incorrect"))
    window = build_window(qtbot, monkeypatch, manager)
    window.email_le.setText("a@b.com")
    window.fetch_question()

    window.answer_le.setText("wrong")
    window.answer_2_le.setText("London")
    window.new_password_le.setText("NewPass123")
    window.confirm_password_le.setText("NewPass123")

    window.submit_reset()

    assert window.error_lbl_step2.text() == "One or more security answers are incorrect"
