"""Covers #28: language selector (English/Turkish) on the Settings page."""

import types

import views.main_window as mw


class FakeClassManager:
    def load_classes_for_instructor(self, user_id, include_archived=False):
        return []


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def build_window(qtbot, monkeypatch):
    monkeypatch.setattr(mw, "ClassManager", FakeClassManager)
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    return window


def test_nav_and_titles_translate_to_saved_language(qtbot, monkeypatch):
    turkish = {
        "my_classes": "Sınıflarım",
        "settings": "Ayarlar",
        "statistics": "İstatistikler",
        "log_out": "Çıkış Yap",
        "create_new_class": "Yeni Sınıf Oluştur",
        "profile": "Profil",
        "attendance_statistics": "Devam İstatistikleri",
    }
    monkeypatch.setattr(mw, "t", lambda key: turkish[key])
    window = build_window(qtbot, monkeypatch)

    assert window.my_classes_btn.text() == "Sınıflarım"
    assert window.settings_btn.text() == "Ayarlar"
    assert window.statistics_btn.text() == "İstatistikler"
    assert window.log_out_btn.text() == "Çıkış Yap"
    assert window.my_classes_title_lbl.text() == "Sınıflarım"


def test_language_combo_reflects_saved_preference(qtbot, monkeypatch):
    monkeypatch.setattr(mw, "load_language_preference", lambda: "tr")
    window = build_window(qtbot, monkeypatch)

    assert window.language_combo.currentData() == "tr"
    assert window.language_combo.currentText() == "Türkçe"


def test_changing_language_saves_preference_and_notifies(qtbot, monkeypatch):
    window = build_window(qtbot, monkeypatch)

    saved = []
    monkeypatch.setattr(mw, "save_language_preference", lambda lang: saved.append(lang))
    monkeypatch.setattr(mw.QMessageBox, "information", lambda *a, **k: None)

    tr_index = window.language_combo.findData("tr")
    window.language_combo.setCurrentIndex(tr_index)

    assert saved == ["tr"]
