from pathlib import Path

import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QLineEdit, QMainWindow

from models.accounts import AccountManager
from views.create_account_window import CreateAccountWindow
from views.main_window import MainWindow
from views.reset_password_window import ResetPasswordWindow
from resources.images import qrc

REMEMBERED_EMAIL_PATH = Path(".remembered_email")


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/login_window.ui", self)

        self.account_manager = AccountManager()

        self.login_btn.clicked.connect(self.login)
        self.create_account_btn.clicked.connect(self.open_create_account_window)
        self.close_window_btn.clicked.connect(self.close)
        self.forgot_password_btn.clicked.connect(self.open_reset_password_window)

        self.close_window_btn.setText("")
        self.close_window_btn.setIcon(qta.icon("fa5s.times", color="#64748B"))
        self.close_window_btn.setIconSize(QSize(14, 14))

        shadow = QGraphicsDropShadowEffect(self.card_frame)
        shadow.setBlurRadius(24)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(15, 23, 42, 40))
        self.card_frame.setGraphicsEffect(shadow)

        self.email_le.textChanged.connect(self._clear_login_error)
        self.password_le.textChanged.connect(self._clear_login_error)
        self.show_password_cb.toggled.connect(self._toggle_password_visibility)

        self.load_remembered_email()
        self.show()

    def _toggle_password_visibility(self, checked):
        self.password_le.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

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
        self.close()
