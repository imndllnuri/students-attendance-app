import pytest

from shared.validation import is_valid_email, is_valid_password, password_strength


@pytest.mark.parametrize(
    "email,expected",
    [
        ("instructor@example.edu", True),
        ("not-an-email", False),
        ("missing@domain", False),
        ("has spaces@example.com", False),
    ],
)
def test_is_valid_email(email, expected):
    assert is_valid_email(email) is expected


@pytest.mark.parametrize(
    "password,expected",
    [
        ("Password123", True),
        ("short1", False),  # too short
        ("alllettersnodigits", False),  # no digit
        ("12345678", False),  # no letter
    ],
)
def test_is_valid_password(password, expected):
    assert is_valid_password(password) is expected


@pytest.mark.parametrize(
    "password,expected",
    [
        ("", ""),
        ("short1", "weak"),
        ("password123", "weak"),  # long enough but no upper/lower mix
        ("Password123", "medium"),
        ("Password1234", "strong"),  # 12+ chars and upper/lower mix and digit
        ("Password123!", "strong"),
    ],
)
def test_password_strength(password, expected):
    assert password_strength(password) == expected
