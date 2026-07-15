"""Lightweight dict-based i18n - not Qt's QTranslator/.ts/.qm workflow.
Covers navigation, page titles, and common actions; not every string in
the app is translated yet (see FEATURE_BACKLOG.md's scope note).

Language choice is persisted the same way as the theme preference (a
plain text file next to the app) and applied when each window builds its
UI - there is no live re-translation of already-open windows.
"""

from pathlib import Path

LANGUAGE_PREFERENCE_PATH = Path(".language_preference")

LANGUAGES = {"en": "English", "tr": "Türkçe"}

STRINGS = {
    "welcome_back": {"en": "Welcome back", "tr": "Tekrar hoş geldiniz"},
    "forgot_password": {"en": "Forgot password?", "tr": "Şifremi unuttum?"},
    "log_in": {"en": "Log in", "tr": "Giriş yap"},
    "create_account": {"en": "Create Account", "tr": "Hesap Oluştur"},

    "my_classes": {"en": "My Classes", "tr": "Sınıflarım"},
    "settings": {"en": "Settings", "tr": "Ayarlar"},
    "statistics": {"en": "Statistics", "tr": "İstatistikler"},
    "log_out": {"en": "Log Out", "tr": "Çıkış Yap"},
    "create_new_class": {"en": "Create New Class", "tr": "Yeni Sınıf Oluştur"},
    "attendance_statistics": {"en": "Attendance Statistics", "tr": "Devam İstatistikleri"},
    "profile": {"en": "Profile", "tr": "Profil"},
}


def load_language_preference() -> str:
    if LANGUAGE_PREFERENCE_PATH.exists():
        value = LANGUAGE_PREFERENCE_PATH.read_text().strip()
        if value in LANGUAGES:
            return value
    return "en"


def save_language_preference(language: str) -> None:
    LANGUAGE_PREFERENCE_PATH.write_text(language)


def t(key: str, language: str = None) -> str:
    """Translates a string key into the given (or currently saved) language,
    falling back to English if the key or language is missing."""
    language = language or load_language_preference()
    entry = STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(language, entry["en"])
