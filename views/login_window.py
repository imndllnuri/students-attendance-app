from pathlib import Path

import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QLineEdit, QWidget

from models.accounts import AccountManager
from shared.i18n import t
from shared.qt_style import set_dynamic_property
from shared.theme import load_theme_preference, save_theme_preference, stylesheet_path
from shared.widgets import set_auth_headline
from views.create_account_window import CreateAccountWindow
from views.main_window import MainWindow
from views.reset_password_window import ResetPasswordWindow
from resources.images import qrc

REMEMBERED_EMAIL_PATH = Path(".remembered_email")


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/login_window.ui", self)

        self.account_manager = AccountManager()

        set_dynamic_property(self.login_btn, "variant", "primary")
        set_dynamic_property(self.create_account_btn, "variant", "ghost")
        set_dynamic_property(self.forgot_password_btn, "variant", "ghost")

        self.login_btn.clicked.connect(self.login)
        self.create_account_btn.clicked.connect(self.open_create_account_window)
        self.forgot_password_btn.clicked.connect(self.open_reset_password_window)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)

        self.email_le.addAction(qta.icon("fa5s.envelope", color="#8A93A7"), QLineEdit.LeadingPosition)
        self.password_le.addAction(qta.icon("fa5s.lock", color="#8A93A7"), QLineEdit.LeadingPosition)
        self._toggle_password_action = self.password_le.addAction(
            qta.icon("fa5s.eye", color="#8A93A7"), QLineEdit.TrailingPosition
        )
        self._toggle_password_action.setCheckable(True)
        self._toggle_password_action.setToolTip("Show password")
        self._toggle_password_action.toggled.connect(self._toggle_password_visibility)

        self.email_le.textChanged.connect(self._clear_login_error)
        self.password_le.textChanged.connect(self._clear_login_error)

        set_auth_headline(self.auth_headline_lbl, "Track every session.", "Never miss a beat.")

        self._apply_translations()
        self._update_theme_icon()
        self.load_remembered_email()
        self.show()

    def _apply_translations(self):
        self.title_lbl.setText(t("welcome_back"))
        self.subtitle_lbl.setText(t("sign_in_subtitle"))
        self.email_field_lbl.setText(t("email_address"))
        self.password_field_lbl.setText(t("password"))
        self.forgot_password_btn.setText(t("forgot_password"))
        self.remember_me_cb.setText(t("remember_me"))
        self.login_btn.setText(t("log_in"))
        self.create_account_prompt_lbl.setText(t("dont_have_account"))
        self.create_account_btn.setText(t("create_one"))

    def toggle_theme(self):
        """Same mechanism as MainWindow.toggle_dark_mode - this button is
        the only theme control visible before login, matching the
        reference's top-right sun/moon toggle on every auth screen."""
        new_theme = "light" if load_theme_preference() == "dark" else "dark"
        save_theme_preference(new_theme)
        with open(stylesheet_path(new_theme)) as f:
            QApplication.instance().setStyleSheet(f.read())
        self._update_theme_icon()

    def _update_theme_icon(self):
        is_dark = load_theme_preference() == "dark"
        icon_name = "fa5s.sun" if is_dark else "fa5s.moon"
        self.theme_toggle_btn.setIcon(qta.icon(icon_name, color="#8A93A7"))

    def _toggle_password_visibility(self, checked):
        self.password_le.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self._toggle_password_action.setIcon(
            qta.icon("fa5s.eye-slash" if checked else "fa5s.eye", color="#8A93A7")
        )
        self._toggle_password_action.setToolTip("Hide password" if checked else "Show password")

    def load_remembered_email(self):
        if REMEMBERED_EMAIL_PATH.exists():
            self.email_le.setText(REMEMBERED_EMAIL_PATH.read_text().strip())
            self.remember_me_cb.setChecked(True)

    def login(self):
        email = self.email_le.text()
        password = self.password_le.text()

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

    def open_create_account_window(self):
        self.create_account_window = CreateAccountWindow(self.account_manager)
        self.create_account_window.show()

    def open_reset_password_window(self):
        self.reset_password_window = ResetPasswordWindow(self.account_manager)
        self.reset_password_window.exec_()

    def open_main_window(self, account):
        self.main_window = MainWindow(account)
        self.main_window.show()
        self.main_window._maybe_show_whats_new()
        self.close()
