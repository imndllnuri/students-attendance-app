from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMessageBox
from models.accounts import AccountManager, Account

class CreateAccountWindow(QDialog):
    def __init__(self, account_manager):
        super().__init__()
        uic.loadUi("ui/create_account_window.ui", self)
        self.account_manager = account_manager
        
        self.sign_up_btn.clicked.connect(self.create_account)
        
        # Add security question options to the combo box
        security_questions = ["What is your mother's maiden name?", 
                              "What was your first pet's name?"]
        self.security_question_ComboBox.addItems(security_questions)
        
        self.show()

    def create_account(self):
        email = self.email_le.text()
        password = self.password_le.text()
        password_again = self.password_again_le.text()
        name = self.name_le.text()
        surname = self.surname_le.text()
        security_question = self.security_question_ComboBox.currentText()
        answer = self.answer_le.text()
        
        if password != password_again:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match!")
            return
        
        if self.account_manager.get_account_by_email(email):
            QMessageBox.warning(self, "Account Exists", "An account with this email already exists!")
            return
        
        new_account = Account(email, password, name, surname, security_question, answer)
        self.account_manager.add_account(new_account)
        
        QMessageBox.information(self, "Account Created", "Your account has been created successfully!")
        self.close()
