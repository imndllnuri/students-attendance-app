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
        "welcome_back": "Welcome back.",
        "sign_in_subtitle": "Sign in to your account",
        "email_address": "Email Address",
        "password": "Password",
        "forgot_password": "Forgot password?",
        "remember_me": "Remember me for 30 days",
        "log_in": "Sign In",
        "dont_have_account": "Don't have an account?",
        "create_one": "Create one",
    }[key])
    window = build_window(qtbot, monkeypatch)

    assert window.signin_title_lbl.text() == "Welcome back."
    assert window.login_btn.text() == "Sign In"
    assert window.create_account_prompt_lbl.text() == "Don't have an account?"
    assert window.create_account_btn.text() == "Create one"


def test_uses_turkish_strings_when_that_is_the_saved_language(qtbot, monkeypatch):
    turkish = {
        "welcome_back": "Tekrar hoş geldiniz.",
        "sign_in_subtitle": "Hesabınıza giriş yapın",
        "email_address": "E-posta Adresi",
        "password": "Şifre",
        "forgot_password": "Şifremi unuttum?",
        "remember_me": "30 gün boyunca beni hatırla",
        "log_in": "Giriş Yap",
        "dont_have_account": "Hesabınız yok mu?",
        "create_one": "Hesap oluşturun",
    }
    monkeypatch.setattr(lw, "t", lambda key: turkish[key])
    window = build_window(qtbot, monkeypatch)

    assert window.signin_title_lbl.text() == "Tekrar hoş geldiniz."
    assert window.forgot_password_btn.text() == "Şifremi unuttum?"
    assert window.login_btn.text() == "Giriş Yap"
    assert window.create_account_btn.text() == "Hesap oluşturun"
