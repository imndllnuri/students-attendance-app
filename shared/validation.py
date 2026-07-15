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
    "What city were you born in?",
]


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def is_valid_password(password: str) -> bool:
    return (
        len(password) >= MIN_PASSWORD_LENGTH
        and any(c.isalpha() for c in password)
        and any(c.isdigit() for c in password)
    )


def password_strength(password: str) -> str:
    """Returns "", "weak", "medium", or "strong" - used to drive a live
    strength indicator on password-creation fields. Independent of
    is_valid_password()'s pass/fail rule: a password can be valid (meets
    the minimum bar) while still rating as only "weak"."""
    if not password:
        return ""

    score = 0
    if len(password) >= MIN_PASSWORD_LENGTH:
        score += 1
    if len(password) >= 12:
        score += 1
    if any(c.islower() for c in password) and any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(not c.isalnum() for c in password):
        score += 1

    if score <= 2:
        return "weak"
    if score <= 3:
        return "medium"
    return "strong"
