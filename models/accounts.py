from services.api_client import ApiClient, ApiError


class Account:
    def __init__(self, email, password, name, surname, security_question, answer, user_id=None):
        self.user_id = user_id
        self.email = email
        self.password = password
        self.name = name
        self.surname = surname
        self.security_question = security_question
        self.answer = answer

    def to_dict(self):
        return {
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
            data.get("password", ""),
            data["name"],
            data["surname"],
            data.get("security_question", ""),
            data.get("answer", ""),
            user_id=data["user_id"],
        )


class AccountManager:
    """Thin wrapper around the attendance server's account endpoints."""

    def __init__(self, api_client=None):
        self.api_client = api_client or ApiClient()

    def add_account(self, account):
        try:
            self.api_client.create_account(account.to_dict())
            return True
        except ApiError:
            return False

    def authenticate(self, email, password):
        try:
            data = self.api_client.authenticate(email, password)
        except ApiError:
            return None
        return Account.from_dict(data) if data else None

    def get_security_question(self, email):
        try:
            data = self.api_client.get_security_question(email)
        except ApiError:
            return None
        return data["security_question"] if data else None

    def reset_password(self, email, answer, new_password):
        try:
            self.api_client.reset_password(email, answer, new_password)
        except ApiError as e:
            return False, str(e)
        return True, ""

    def update_account(self, user_id, email=None, name=None, surname=None):
        try:
            data = self.api_client.update_account(user_id, email=email, name=name, surname=surname)
        except ApiError as e:
            return None, str(e)
        return data, ""

    def change_password(self, user_id, current_password, new_password):
        try:
            self.api_client.change_password(user_id, current_password, new_password)
        except ApiError as e:
            return False, str(e)
        return True, ""

    def update_security_question(self, user_id, current_password, security_question, answer):
        try:
            self.api_client.update_security_question(
                user_id, current_password, security_question, answer
            )
        except ApiError as e:
            return False, str(e)
        return True, ""

    def delete_account(self, user_id):
        try:
            self.api_client.delete_account(user_id)
        except ApiError as e:
            return False, str(e)
        return True, ""
