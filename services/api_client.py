import requests


class ApiError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url.rstrip("/")

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(method, url, timeout=5, **kwargs)
        except requests.exceptions.ConnectionError as e:
            raise ApiError(
                "Could not reach the attendance server. Is it running "
                "(python -m server.app)?"
            ) from e
        if response.status_code >= 400:
            try:
                message = response.json().get("error", response.text)
            except ValueError:
                message = response.text
            raise ApiError(message, response.status_code)
        if response.content:
            return response.json()
        return None

    # Accounts
    def authenticate(self, email, password):
        return self._request("POST", "/authenticate", json={"email": email, "password": password})

    def create_account(self, account_data):
        return self._request("POST", "/accounts", json=account_data)

    def get_security_question(self, email):
        return self._request("POST", "/security-question", json={"email": email})

    def reset_password(self, email, answer, new_password):
        return self._request(
            "POST",
            "/reset-password",
            json={"email": email, "answer": answer, "new_password": new_password},
        )

    def update_account(self, user_id, email=None, name=None, surname=None):
        payload = {
            k: v for k, v in {"email": email, "name": name, "surname": surname}.items()
            if v is not None
        }
        return self._request("PATCH", f"/accounts/{user_id}", json=payload)

    def change_password(self, user_id, current_password, new_password):
        return self._request(
            "POST",
            f"/accounts/{user_id}/change-password",
            json={"current_password": current_password, "new_password": new_password},
        )

    def update_security_question(self, user_id, current_password, security_question, answer):
        return self._request(
            "POST",
            f"/accounts/{user_id}/security-question",
            json={
                "current_password": current_password,
                "security_question": security_question,
                "answer": answer,
            },
        )

    def delete_account(self, user_id):
        return self._request("DELETE", f"/accounts/{user_id}")

    def get_login_history(self, user_id, limit=10):
        return self._request(
            "GET", f"/accounts/{user_id}/login-history", params={"limit": limit}
        )

    # Classes
    def list_classes(self, instructor_id, include_archived=False):
        return self._request(
            "GET",
            "/classes",
            params={"instructor_id": instructor_id, "include_archived": include_archived},
        )

    def create_class(self, class_data):
        return self._request("POST", "/classes", json=class_data)

    def update_class(self, class_id, fields):
        return self._request("PATCH", f"/classes/{class_id}", json=fields)

    def delete_class(self, class_id):
        return self._request("DELETE", f"/classes/{class_id}")

    # Roster / students
    def get_roster(self, class_id):
        return self._request("GET", "/roster", params={"class_id": class_id})

    def add_student(self, class_id, student_number, name_surname):
        return self._request(
            "POST",
            "/roster",
            json={
                "class_id": class_id,
                "student_number": student_number,
                "name_surname": name_surname,
            },
        )

    def remove_student(self, student_id):
        return self._request("DELETE", f"/roster/{student_id}")

    def merge_students(self, keep_student_id, remove_student_id):
        return self._request(
            "POST",
            "/roster/merge",
            json={"keep_student_id": keep_student_id, "remove_student_id": remove_student_id},
        )

    def register_card(self, student_id, card_id):
        return self._request("POST", f"/roster/{student_id}/card", json={"card_id": card_id})

    def get_student_table(self, class_id):
        return self._request("GET", "/students", params={"class_id": class_id})

    # Attendance
    def submit_attendance(self, class_id, records):
        return self._request("POST", "/attend", json={"class_id": class_id, "records": records})

    def correct_attendance(self, class_id, student_id, date, time_slot, status):
        return self._request(
            "POST",
            "/attend/correct",
            json={
                "class_id": class_id,
                "student_id": student_id,
                "date": date,
                "time_slot": time_slot,
                "status": status,
            },
        )

    def get_attendance_sheet(self, class_id, date):
        return self._request("GET", "/attendance_sheet", params={"class_id": class_id, "date": date})

    def get_statistics(self, class_id):
        return self._request("GET", "/statistics", params={"class_id": class_id})
