import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QLineEdit, QMessageBox

from shared.qt_style import set_dynamic_property
from shared.shadow import apply_card_shadow
from shared.validation import MIN_PASSWORD_LENGTH, is_valid_password, password_strength


class ResetPasswordWindow(QDialog):
    def __init__(self, account_manager):
        super().__init__()
        uic.loadUi("ui/reset_password_window.ui", self)
        self.account_manager = account_manager
        self._email = None

        set_dynamic_property(self.next_btn, "variant", "primary")
        set_dynamic_property(self.cancel_btn, "variant", "secondary")
        set_dynamic_property(self.back_btn, "variant", "secondary")
        set_dynamic_property(self.reset_btn, "variant", "primary")

        self.next_btn.clicked.connect(self.fetch_question)
        self.cancel_btn.clicked.connect(self.reject)
        self.back_btn.clicked.connect(lambda: self.steps_stack.setCurrentIndex(0))
        self.reset_btn.clicked.connect(self.submit_reset)
        self.new_password_le.textChanged.connect(self._update_password_strength)

        self._password_toggle = self.new_password_le.addAction(
            qta.icon("fa5s.eye", color="#6B6B76"), QLineEdit.TrailingPosition
        )
        self._password_toggle.setCheckable(True)
        self._password_toggle.setToolTip("Show password")
        self._password_toggle.toggled.connect(self.toggle_password_visibility)

        apply_card_shadow(self.card_frame, strength="lg")

    def fetch_question(self):
        email = self.email_le.text().strip()
        if not email:
            self._show_error(self.error_lbl_step1, "Please enter your email.")
            return

        questions = self.account_manager.get_security_questions(email)
        if not questions:
            self._show_error(self.error_lbl_step1, "No account found with this email.")
            return

        self._email = email
        self.error_lbl_step1.setVisible(False)
        self.security_question_lbl.setText(questions[0])
        self.security_question_2_lbl.setText(questions[1])
        self.steps_stack.setCurrentIndex(1)

    def submit_reset(self):
        answer_1 = self.answer_le.text().strip()
        answer_2 = self.answer_2_le.text().strip()
        new_password = self.new_password_le.text()
        confirm_password = self.confirm_password_le.text()

        if not answer_1 or not answer_2:
            self._show_error(self.error_lbl_step2, "Please answer both security questions.")
            return
        if not is_valid_password(new_password):
            self._show_error(
                self.error_lbl_step2,
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters "
                "and include both letters and numbers.",
            )
            return
        if new_password != confirm_password:
            self._show_error(self.error_lbl_step2, "Passwords do not match.")
            return

        success, error_message = self.account_manager.reset_password(
            self._email, answer_1, answer_2, new_password
        )
        if not success:
            self._show_error(self.error_lbl_step2, error_message)
            return

        QMessageBox.information(
            self, "Password Reset", "Your password has been reset successfully!"
        )
        self.accept()

    def _update_password_strength(self):
        strength = password_strength(self.new_password_le.text())
        self.new_password_strength_lbl.setText(strength.capitalize() if strength else "")
        self.new_password_strength_lbl.setProperty("strength", strength)
        self.new_password_strength_lbl.style().unpolish(self.new_password_strength_lbl)
        self.new_password_strength_lbl.style().polish(self.new_password_strength_lbl)

    def toggle_password_visibility(self, checked):
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.new_password_le.setEchoMode(mode)
        self.confirm_password_le.setEchoMode(mode)
        self._password_toggle.setIcon(qta.icon("fa5s.eye-slash" if checked else "fa5s.eye", color="#6B6B76"))
        self._password_toggle.setToolTip("Hide password" if checked else "Show password")

    def _show_error(self, label, message):
        label.setText(message)
        label.setProperty("error", True)
        label.setVisible(True)
        label.style().unpolish(label)
        label.style().polish(label)
