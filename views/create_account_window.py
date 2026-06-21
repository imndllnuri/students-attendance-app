import re

import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QGraphicsDropShadowEffect, QLineEdit, QMessageBox

from models.accounts import Account

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


class CreateAccountWindow(QDialog):
    def __init__(self, account_manager):
        super().__init__()
        uic.loadUi("ui/create_account_window.ui", self)
        self.account_manager = account_manager

        self.sign_up_btn.clicked.connect(self.create_account)
        self.show_password_btn.toggled.connect(
            lambda checked: self._toggle_echo(self.password_le, self.show_password_btn, checked)
        )
        self.show_password_again_btn.toggled.connect(
            lambda checked: self._toggle_echo(
                self.password_again_le, self.show_password_again_btn, checked
            )
        )

        self.email_le.textChanged.connect(self.validate_email)
        self.password_le.textChanged.connect(self.validate_password)
        self.password_again_le.textChanged.connect(self.validate_password_match)

        security_questions = ["What is your mother's maiden name?",
                              "What was your first pet's name?"]
        self.security_question_ComboBox.addItems(security_questions)

        for btn in (self.show_password_btn, self.show_password_again_btn):
            btn.setText("")
            btn.setIcon(qta.icon("fa5s.eye", color="#64748B"))
            btn.setAccessibleName("Toggle password visibility")
            btn.setToolTip("Show password")

        shadow = QGraphicsDropShadowEffect(self.card_frame)
        shadow.setBlurRadius(24)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(15, 23, 42, 40))
        self.card_frame.setGraphicsEffect(shadow)

        self.show()

    def _toggle_echo(self, line_edit, button, checked):
        line_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        button.setIcon(qta.icon("fa5s.eye-slash" if checked else "fa5s.eye", color="#64748B"))
        button.setToolTip("Hide password" if checked else "Show password")

    def validate_email(self):
        email = self.email_le.text().strip()
        if email and not EMAIL_RE.match(email):
            self._set_error(self.email_le, self.email_error_lbl, "Enter a valid email address.")
            return False
        self._clear_error(self.email_le, self.email_error_lbl)
        return True

    def validate_password(self):
        password = self.password_le.text()
        if password and not (
            len(password) >= MIN_PASSWORD_LENGTH
            and any(c.isalpha() for c in password)
            and any(c.isdigit() for c in password)
        ):
            self._set_error(
                self.password_le,
                self.password_error_lbl,
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters "
                "and include both letters and numbers.",
            )
            self.validate_password_match()
            return False
        self._clear_error(self.password_le, self.password_error_lbl)
        self.validate_password_match()
        return True

    def validate_password_match(self):
        if self.password_again_le.text() and self.password_again_le.text() != self.password_le.text():
            self._set_error(self.password_again_le, self.password_again_error_lbl, "Passwords do not match.")
            return False
        self._clear_error(self.password_again_le, self.password_again_error_lbl)
        return True

    def _set_error(self, line_edit, label, message):
        label.setText(message)
        label.setProperty("error", True)
        label.setVisible(True)
        label.style().unpolish(label)
        label.style().polish(label)
        line_edit.setProperty("error", True)
        line_edit.style().unpolish(line_edit)
        line_edit.style().polish(line_edit)

    def _clear_error(self, line_edit, label):
        label.setVisible(False)
        line_edit.setProperty("error", False)
        line_edit.style().unpolish(line_edit)
        line_edit.style().polish(line_edit)

    def create_account(self):
        email = self.email_le.text().strip()
        password = self.password_le.text()
        password_again = self.password_again_le.text()
        name = self.name_le.text().strip()
        surname = self.surname_le.text().strip()
        security_question = self.security_question_ComboBox.currentText()
        answer = self.answer_le.text()

        email_ok = self.validate_email()
        password_ok = self.validate_password()
        match_ok = self.validate_password_match()

        if not (email_ok and password_ok and match_ok):
            return
        if not email or not password or not name or not surname or not answer:
            QMessageBox.warning(self, "Missing Information", "Please fill in all fields.")
            return

        new_account = Account(email, password, name, surname, security_question, answer)
        if not self.account_manager.add_account(new_account):
            QMessageBox.warning(self, "Account Exists", "An account with this email already exists!")
            return

        QMessageBox.information(self, "Account Created", "Your account has been created successfully!")
        self.close()
