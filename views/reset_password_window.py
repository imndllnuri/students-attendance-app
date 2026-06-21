import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QGraphicsDropShadowEffect, QLineEdit, QMessageBox

MIN_PASSWORD_LENGTH = 8


class ResetPasswordWindow(QDialog):
    def __init__(self, account_manager):
        super().__init__()
        uic.loadUi("ui/reset_password_window.ui", self)
        self.account_manager = account_manager
        self._email = None

        self.next_btn.clicked.connect(self.fetch_question)
        self.cancel_btn.clicked.connect(self.reject)
        self.back_btn.clicked.connect(lambda: self.steps_stack.setCurrentIndex(0))
        self.reset_btn.clicked.connect(self.submit_reset)
        self.show_password_btn.toggled.connect(self.toggle_password_visibility)

        self.show_password_btn.setText("")
        self.show_password_btn.setIcon(qta.icon("fa5s.eye", color="#64748B"))
        self.show_password_btn.setAccessibleName("Toggle password visibility")
        self.show_password_btn.setToolTip("Show password")

        shadow = QGraphicsDropShadowEffect(self.card_frame)
        shadow.setBlurRadius(24)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(15, 23, 42, 40))
        self.card_frame.setGraphicsEffect(shadow)

    def fetch_question(self):
        email = self.email_le.text().strip()
        if not email:
            self._show_error(self.error_lbl_step1, "Please enter your email.")
            return

        question = self.account_manager.get_security_question(email)
        if not question:
            self._show_error(self.error_lbl_step1, "No account found with this email.")
            return

        self._email = email
        self.error_lbl_step1.setVisible(False)
        self.security_question_lbl.setText(question)
        self.steps_stack.setCurrentIndex(1)

    def submit_reset(self):
        answer = self.answer_le.text().strip()
        new_password = self.new_password_le.text()
        confirm_password = self.confirm_password_le.text()

        if not answer:
            self._show_error(self.error_lbl_step2, "Please answer the security question.")
            return
        if len(new_password) < MIN_PASSWORD_LENGTH:
            self._show_error(
                self.error_lbl_step2,
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters.",
            )
            return
        if new_password != confirm_password:
            self._show_error(self.error_lbl_step2, "Passwords do not match.")
            return

        success, error_message = self.account_manager.reset_password(
            self._email, answer, new_password
        )
        if not success:
            self._show_error(self.error_lbl_step2, error_message)
            return

        QMessageBox.information(
            self, "Password Reset", "Your password has been reset successfully!"
        )
        self.accept()

    def toggle_password_visibility(self, checked):
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.new_password_le.setEchoMode(mode)
        self.confirm_password_le.setEchoMode(mode)
        self.show_password_btn.setIcon(qta.icon("fa5s.eye-slash" if checked else "fa5s.eye", color="#64748B"))
        self.show_password_btn.setToolTip("Hide password" if checked else "Show password")

    def _show_error(self, label, message):
        label.setText(message)
        label.setProperty("error", True)
        label.setVisible(True)
        label.style().unpolish(label)
        label.style().polish(label)
