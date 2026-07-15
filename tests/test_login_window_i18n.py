"""Covers #28: login window strings translate per the saved language preference."""

import views.login_window as lw


class FakeAccountManager:
    pass


def build_window(qtbot, monkeypatch):
    monkeypatch.setattr(lw, "AccountManager", FakeAccountManager)
    window = lw.LoginWindow()
    qtbot.addWidget(window)
    return window


def test_defaults_to_english_strings(qtbot, monkeypatch):
    monkeypatch.setattr(lw, "t", lambda key: {
        "welcome_back": "Welcome back",
        "sign_in_subtitle": "Sign in to manage your classes and attendance",
        "forgot_password": "Forgot password?",
        "log_in": "Log in",
        "create_account": "Create Account",
    }[key])
    window = build_window(qtbot, monkeypatch)

    assert window.title_lbl.text() == "Welcome back"
    assert window.login_btn.text() == "Log in"
    assert window.create_account_btn.text() == "Create Account"


def test_uses_turkish_strings_when_that_is_the_saved_language(qtbot, monkeypatch):
    turkish = {
        "welcome_back": "Tekrar hoş geldiniz",
        "sign_in_subtitle": "Sınıflarınızı ve yoklamalarınızı yönetmek için giriş yapın",
        "forgot_password": "Şifremi unuttum?",
        "log_in": "Giriş yap",
        "create_account": "Hesap Oluştur",
    }
    monkeypatch.setattr(lw, "t", lambda key: turkish[key])
    window = build_window(qtbot, monkeypatch)

    assert window.title_lbl.text() == "Tekrar hoş geldiniz"
    assert window.forgot_password_btn.text() == "Şifremi unuttum?"
    assert window.login_btn.text() == "Giriş yap"
    assert window.create_account_btn.text() == "Hesap Oluştur"
