from pathlib import Path

import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLineEdit, QMessageBox, QWidget

from models.accounts import Account, AccountManager
from shared.backend_config import load_backend_config, save_backend_config
from shared.dialogs import ServerConnectionDialog
from shared.i18n import t
from shared.qt_style import set_dynamic_property
from shared.validation import (
    MIN_PASSWORD_LENGTH,
    SECURITY_QUESTIONS,
    is_valid_email,
    is_valid_password,
    password_strength,
)
from shared.widgets import set_auth_headline

REMEMBERED_EMAIL_PATH = Path(".remembered_email")

SIGN_IN_PAGE, SIGN_UP_PAGE, RESET_PAGE = range(3)


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/login_window.ui", self)

        self.account_manager = AccountManager()
        self._reset_email = None

        set_auth_headline(self.auth_headline_lbl, "Track every session.", "Never miss a beat.")
        self.auth_icon_lbl.setPixmap(
            QPixmap("resources/images/app_icon.png").scaled(
                28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )

        self._setup_sign_in_page()
        self._setup_sign_up_page()
        self._setup_reset_page()
        self._setup_server_settings()

        # QStackedWidget sizes itself to the TALLEST page by default (not the
        # current one) so the window doesn't jump around when switching -
        # here that means the compact Sign In page inherits the much taller
        # Sign Up page's height, leaving a huge empty gap. Since every page
        # here is a fixed, static form (not something a user resizes text
        # into), pin each stack's height to whichever page is actually showing.
        self.auth_stack.currentChanged.connect(lambda _: self._sync_stack_height(self.auth_stack))
        self.steps_stack.currentChanged.connect(lambda _: self._sync_stack_height(self.steps_stack))

        self._apply_translations()
        self.load_remembered_email()
        self.auth_stack.setCurrentIndex(SIGN_IN_PAGE)
        self._sync_stack_height(self.auth_stack)
        self._sync_stack_height(self.steps_stack)
        self.show()

    def _sync_stack_height(self, stack):
        current = stack.currentWidget()
        if current is None:
            return
        height = current.sizeHint().height()
        stack.setMinimumHeight(height)
        stack.setMaximumHeight(height)

    # --- Navigation between Sign In / Sign Up / Reset Password ---

    def show_sign_in_page(self):
        self.auth_stack.setCurrentIndex(SIGN_IN_PAGE)

    def show_sign_up_page(self):
        self.auth_stack.setCurrentIndex(SIGN_UP_PAGE)

    def show_reset_page(self):
        self.steps_stack.setCurrentIndex(0)
        self.reset_email_le.clear()
        self.error_lbl_step1.setVisible(False)
        self.auth_stack.setCurrentIndex(RESET_PAGE)

    def _apply_translations(self):
        self.signin_title_lbl.setText(t("welcome_back"))
        self.signin_subtitle_lbl.setText(t("sign_in_subtitle"))
        self.signin_email_field_lbl.setText(t("email_address"))
        self.signin_password_field_lbl.setText(t("password"))
        self.forgot_password_btn.setText(t("forgot_password"))
        self.remember_me_cb.setText(t("remember_me"))
        self.login_btn.setText(t("log_in"))
        self.create_account_prompt_lbl.setText(t("dont_have_account"))
        self.create_account_btn.setText(t("create_one"))

    # --- Sign In ---

    def _setup_sign_in_page(self):
        set_dynamic_property(self.login_btn, "variant", "primary")
        set_dynamic_property(self.create_account_btn, "variant", "ghost")
        set_dynamic_property(self.forgot_password_btn, "variant", "ghost")

        self.login_btn.clicked.connect(self.login)
        self.create_account_btn.clicked.connect(self.show_sign_up_page)
        self.forgot_password_btn.clicked.connect(self.show_reset_page)

        self.signin_email_le.addAction(qta.icon("fa5s.envelope", color="#8A93A7"), QLineEdit.LeadingPosition)
        self.signin_password_le.addAction(qta.icon("fa5s.lock", color="#8A93A7"), QLineEdit.LeadingPosition)
        self._toggle_password_action = self.signin_password_le.addAction(
            qta.icon("fa5s.eye", color="#8A93A7"), QLineEdit.TrailingPosition
        )
        self._toggle_password_action.setCheckable(True)
        self._toggle_password_action.setToolTip("Show password")
        self._toggle_password_action.toggled.connect(self._toggle_password_visibility)

        self.signin_email_le.textChanged.connect(self._clear_login_error)
        self.signin_password_le.textChanged.connect(self._clear_login_error)

    def _toggle_password_visibility(self, checked):
        self.signin_password_le.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self._toggle_password_action.setIcon(
            qta.icon("fa5s.eye-slash" if checked else "fa5s.eye", color="#8A93A7")
        )
        self._toggle_password_action.setToolTip("Hide password" if checked else "Show password")

    def load_remembered_email(self):
        if REMEMBERED_EMAIL_PATH.exists():
            self.signin_email_le.setText(REMEMBERED_EMAIL_PATH.read_text().strip())
            self.remember_me_cb.setChecked(True)

    def login(self):
        email = self.signin_email_le.text()
        password = self.signin_password_le.text()

        account = self.account_manager.authenticate(email, password)

        if account:
            if self.remember_me_cb.isChecked():
                REMEMBERED_EMAIL_PATH.write_text(email)
            elif REMEMBERED_EMAIL_PATH.exists():
                REMEMBERED_EMAIL_PATH.unlink()

            self.open_main_window(account)
        else:
            self._show_login_error("Incorrect email or password.")

    def _show_login_error(self, message):
        self.login_error_lbl.setText(message)
        self.login_error_lbl.setProperty("error", True)
        self.login_error_lbl.setVisible(True)
        self.login_error_lbl.style().unpolish(self.login_error_lbl)
        self.login_error_lbl.style().polish(self.login_error_lbl)

    def _clear_login_error(self):
        self.login_error_lbl.setVisible(False)

    def open_main_window(self, account):
        from views.main_window import MainWindow

        self.main_window = MainWindow(account)
        self.main_window.show()
        self.main_window._maybe_show_whats_new()
        self.close()

    # --- Server Connection ---

    def _setup_server_settings(self):
        self.server_settings_btn.setIcon(qta.icon("fa5s.cog", color="#8A93A7"))
        self.server_settings_btn.setToolTip("Server Connection")
        self.server_settings_btn.clicked.connect(self.show_server_connection_dialog)

    def show_server_connection_dialog(self):
        config = load_backend_config()
        dialog = ServerConnectionDialog(self, config["base_url"], config.get("api_key", ""))
        if dialog.exec_() == ServerConnectionDialog.Accepted:
            config["base_url"] = dialog.base_url()
            config["api_key"] = dialog.api_key()
            save_backend_config(config)
            self.account_manager = AccountManager()

    # --- Sign Up ---

    def _setup_sign_up_page(self):
        set_dynamic_property(self.sign_up_btn, "variant", "primary")
        set_dynamic_property(self.sign_in_btn, "variant", "ghost")
        self.sign_up_btn.clicked.connect(self.create_account)
        self.sign_in_btn.clicked.connect(self.show_sign_in_page)

        self.signup_email_le.addAction(qta.icon("fa5s.envelope", color="#8A93A7"), QLineEdit.LeadingPosition)
        self._signup_password_toggle = self._add_password_toggle(self.signup_password_le)
        self._signup_password_again_toggle = self._add_password_toggle(self.password_again_le)

        self.signup_email_le.textChanged.connect(self.validate_email)
        self.signup_password_le.textChanged.connect(self.validate_password)
        self.signup_password_le.textChanged.connect(self._update_password_strength)
        self.password_again_le.textChanged.connect(self.validate_password_match)

        self.security_question_combo.addItems(SECURITY_QUESTIONS)
        self.security_question_2_combo.addItems(SECURITY_QUESTIONS)
        if len(SECURITY_QUESTIONS) > 1:
            self.security_question_2_combo.setCurrentIndex(1)

    def _add_password_toggle(self, line_edit):
        action = line_edit.addAction(qta.icon("fa5s.eye", color="#8A93A7"), QLineEdit.TrailingPosition)
        action.setCheckable(True)
        action.setToolTip("Show password")
        action.toggled.connect(lambda checked: self._toggle_echo(line_edit, action, checked))
        return action

    def _toggle_echo(self, line_edit, action, checked):
        line_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        action.setIcon(qta.icon("fa5s.eye-slash" if checked else "fa5s.eye", color="#8A93A7"))
        action.setToolTip("Hide password" if checked else "Show password")

    def validate_email(self):
        email = self.signup_email_le.text().strip()
        if email and not is_valid_email(email):
            self._set_error(self.signup_email_le, self.email_error_lbl, "Enter a valid email address.")
            return False
        self._clear_error(self.signup_email_le, self.email_error_lbl)
        return True

    def validate_password(self):
        password = self.signup_password_le.text()
        if password and not is_valid_password(password):
            self._set_error(
                self.signup_password_le,
                self.password_error_lbl,
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters "
                "and include both letters and numbers.",
            )
            self.validate_password_match()
            return False
        self._clear_error(self.signup_password_le, self.password_error_lbl)
        self.validate_password_match()
        return True

    def _update_password_strength(self):
        strength = password_strength(self.signup_password_le.text())
        self.password_strength_lbl.setText(strength.capitalize() if strength else "")
        self.password_strength_lbl.setProperty("strength", strength)
        self.password_strength_lbl.style().unpolish(self.password_strength_lbl)
        self.password_strength_lbl.style().polish(self.password_strength_lbl)

    def validate_password_match(self):
        if self.password_again_le.text() and self.password_again_le.text() != self.signup_password_le.text():
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
        email = self.signup_email_le.text().strip()
        password = self.signup_password_le.text()
        password_again = self.password_again_le.text()
        name = self.name_le.text().strip()
        surname = self.surname_le.text().strip()
        security_question_1 = self.security_question_combo.currentText()
        answer_1 = self.signup_answer_le.text()
        security_question_2 = self.security_question_2_combo.currentText()
        answer_2 = self.signup_answer_2_le.text()

        email_ok = self.validate_email()
        password_ok = self.validate_password()
        match_ok = self.validate_password_match()

        if not (email_ok and password_ok and match_ok):
            return
        if not email or not password or not name or not surname or not answer_1 or not answer_2:
            QMessageBox.warning(self, "Missing Information", "Please fill in all fields.")
            return
        if security_question_1 == security_question_2:
            self._set_error(
                self.signup_answer_2_le, self.security_questions_error_lbl,
                "Please choose two different security questions.",
            )
            return
        self._clear_error(self.signup_answer_2_le, self.security_questions_error_lbl)

        new_account = Account(
            email, password, name, surname,
            security_question_1, answer_1, security_question_2, answer_2,
        )
        if not self.account_manager.add_account(new_account):
            QMessageBox.warning(self, "Account Exists", "An account with this email already exists!")
            return

        QMessageBox.information(self, "Account Created", "Your account has been created successfully!")
        self.show_sign_in_page()

    # --- Reset Password ---

    def _setup_reset_page(self):
        set_dynamic_property(self.next_btn, "variant", "primary")
        set_dynamic_property(self.cancel_btn, "variant", "secondary")
        set_dynamic_property(self.back_btn, "variant", "secondary")
        set_dynamic_property(self.reset_btn, "variant", "primary")
        set_dynamic_property(self.back_to_signin_btn, "variant", "ghost")

        self.next_btn.clicked.connect(self.fetch_question)
        self.cancel_btn.clicked.connect(self.show_sign_in_page)
        self.back_btn.clicked.connect(lambda: self.steps_stack.setCurrentIndex(0))
        self.back_to_signin_btn.clicked.connect(self.show_sign_in_page)
        self.reset_btn.clicked.connect(self.submit_reset)
        self.new_password_le.textChanged.connect(self._update_reset_password_strength)

        self._reset_password_toggle = self.new_password_le.addAction(
            qta.icon("fa5s.eye", color="#8A93A7"), QLineEdit.TrailingPosition
        )
        self._reset_password_toggle.setCheckable(True)
        self._reset_password_toggle.setToolTip("Show password")
        self._reset_password_toggle.toggled.connect(self.toggle_reset_password_visibility)

    def fetch_question(self):
        email = self.reset_email_le.text().strip()
        if not email:
            self._show_reset_error(self.error_lbl_step1, "Please enter your email.")
            return

        questions = self.account_manager.get_security_questions(email)
        if not questions:
            self._show_reset_error(self.error_lbl_step1, "No account found with this email.")
            return

        self._reset_email = email
        self.error_lbl_step1.setVisible(False)
        self.security_question_lbl.setText(questions[0])
        self.security_question_2_lbl.setText(questions[1])
        self.steps_stack.setCurrentIndex(1)

    def submit_reset(self):
        answer_1 = self.reset_answer_le.text().strip()
        answer_2 = self.reset_answer_2_le.text().strip()
        new_password = self.new_password_le.text()
        confirm_password = self.confirm_password_le.text()

        if not answer_1 or not answer_2:
            self._show_reset_error(self.error_lbl_step2, "Please answer both security questions.")
            return
        if not is_valid_password(new_password):
            self._show_reset_error(
                self.error_lbl_step2,
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters "
                "and include both letters and numbers.",
            )
            return
        if new_password != confirm_password:
            self._show_reset_error(self.error_lbl_step2, "Passwords do not match.")
            return

        success, error_message = self.account_manager.reset_password(
            self._reset_email, answer_1, answer_2, new_password
        )
        if not success:
            self._show_reset_error(self.error_lbl_step2, error_message)
            return

        QMessageBox.information(
            self, "Password Reset", "Your password has been reset successfully!"
        )
        self.show_sign_in_page()

    def _update_reset_password_strength(self):
        strength = password_strength(self.new_password_le.text())
        self.new_password_strength_lbl.setText(strength.capitalize() if strength else "")
        self.new_password_strength_lbl.setProperty("strength", strength)
        self.new_password_strength_lbl.style().unpolish(self.new_password_strength_lbl)
        self.new_password_strength_lbl.style().polish(self.new_password_strength_lbl)

    def toggle_reset_password_visibility(self, checked):
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.new_password_le.setEchoMode(mode)
        self.confirm_password_le.setEchoMode(mode)
        self._reset_password_toggle.setIcon(
            qta.icon("fa5s.eye-slash" if checked else "fa5s.eye", color="#8A93A7")
        )
        self._reset_password_toggle.setToolTip("Hide password" if checked else "Show password")

    def _show_reset_error(self, label, message):
        label.setText(message)
        label.setProperty("error", True)
        label.setVisible(True)
        label.style().unpolish(label)
        label.style().polish(label)
