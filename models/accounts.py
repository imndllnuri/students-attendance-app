import json
import uuid

class Account:
    def __init__(self, email, password, name, surname, security_question, answer, user_id=None):
        self.user_id = user_id if user_id else str(uuid.uuid4())
        self.email = email
        self.password = password  # No hashing for now
        self.name = name
        self.surname = surname
        self.security_question = security_question
        self.answer = answer  # Security answer stored as plain text

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "email": self.email,
            "password": self.password,
            "name": self.name,
            "surname": self.surname,
            "security_question": self.security_question,
            "answer": self.answer,
        }

    @staticmethod
    def from_dict(data):
        return Account(
            data["email"],
            data["password"],
            data["name"],
            data["surname"],
            data["security_question"],
            data["answer"],
            user_id=data["user_id"]
        )

class AccountManager:
    def __init__(self, file_path="accounts.json"):
        self.file_path = file_path
        self.accounts = self.load_accounts()

    def load_accounts(self):
        try:
            with open(self.file_path, "r") as file:
                data = json.load(file)
                return [Account.from_dict(acc) for acc in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_accounts(self):
        try:
            with open(self.file_path, "w") as file:
                json.dump([acc.to_dict() for acc in self.accounts], file, indent=4)
        except IOError:
            print("Error: Unable to save accounts to file.")

    def add_account(self, account):
        if self.get_account_by_email(account.email):
            print("Error: Email already exists.")
            return False
        self.accounts.append(account)
        self.save_accounts()
        return True

    def get_account_by_email(self, email):
        return next((acc for acc in self.accounts if acc.email == email), None)

    def authenticate(self, email, password):
        account = self.get_account_by_email(email)
        if account and account.password == password:
            return account
        return None
