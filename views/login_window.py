from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from models.accounts import AccountManager
from views.create_account_window import CreateAccountWindow
from views.main_window import MainWindow
from resources.images import qrc

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        print("Initializing LoginWindow...")

        try:
            uic.loadUi("ui/login_window.ui", self)
            print("UI loaded successfully from ui/login_window.ui")
        except Exception as e:
            print(f"Failed to load UI: {e}")

        self.account_manager = AccountManager()

        self.login_btn.clicked.connect(self.login)
        self.create_account_btn.clicked.connect(self.open_create_account_window)
        self.close_window_btn.clicked.connect(self.close)

        print("LoginWindow setup complete. Showing window...")
        self.show()

    def login(self):
        email = self.email_le.text()
        password = self.password_le.text()
        print(f"Login attempt for email: {email}")

        account = self.account_manager.get_account_by_email(email)

        if account and account.password == password:
            print(f"Login successful for email: {email}")

            if self.remember_me_cb.isChecked():
                print("Remember me checked. Implement storage logic here.")

            self.open_main_window(account)
        else:
            print(f"Login failed for email: {email} (Incorrect credentials)")
            QMessageBox.warning(self, "Login Failed", "Incorrect email or password")

    def open_create_account_window(self):
        print("Opening CreateAccountWindow...")

        try:
            self.create_account_window = CreateAccountWindow(self.account_manager)
            self.create_account_window.show()
            print("CreateAccountWindow opened successfully.")
        except Exception as e:
            print(f"Error opening CreateAccountWindow: {e}")

    def open_main_window(self, account):
        print(f"Opening MainWindow for user: {account.email}")

        try:
            self.main_window = MainWindow(account)
            self.main_window.show()
            print("MainWindow opened successfully.")
            self.close()  # Close login window after successful login
        except Exception as e:
            print(f"Error opening MainWindow: {e}")
