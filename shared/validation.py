"""Validation rules shared by every view that collects account credentials.

Previously EMAIL_RE/MIN_PASSWORD_LENGTH/SECURITY_QUESTIONS were redefined
independently in main_window.py, create_account_window.py and
reset_password_window.py, and had drifted out of sync (reset only checked
password length, skipping the letter+digit rule enforced elsewhere).
"""

import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
SECURITY_QUESTIONS = [
    "What is your mother's maiden name?",
    "What was your first pet's name?",
]


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def is_valid_password(password: str) -> bool:
    return (
        len(password) >= MIN_PASSWORD_LENGTH
        and any(c.isalpha() for c in password)
        and any(c.isdigit() for c in password)
    )
