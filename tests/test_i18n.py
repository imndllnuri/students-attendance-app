"""Covers #28: language selector (English/Turkish) infrastructure."""

import shared.i18n as i18n


def test_defaults_to_english_when_no_preference_file(monkeypatch, tmp_path):
    monkeypatch.setattr(i18n, "LANGUAGE_PREFERENCE_PATH", tmp_path / "missing")
    assert i18n.load_language_preference() == "en"


def test_save_then_load_round_trips_turkish_preference(monkeypatch, tmp_path):
    pref_path = tmp_path / ".language_preference"
    monkeypatch.setattr(i18n, "LANGUAGE_PREFERENCE_PATH", pref_path)

    i18n.save_language_preference("tr")

    assert i18n.load_language_preference() == "tr"


def test_unknown_preference_file_content_falls_back_to_english(tmp_path, monkeypatch):
    pref_path = tmp_path / ".language_preference"
    pref_path.write_text("not-a-real-language")
    monkeypatch.setattr(i18n, "LANGUAGE_PREFERENCE_PATH", pref_path)

    assert i18n.load_language_preference() == "en"


def test_t_translates_a_known_key():
    assert i18n.t("my_classes", language="en") == "My Classes"
    assert i18n.t("my_classes", language="tr") == "Sınıflarım"


def test_t_falls_back_to_the_key_itself_when_unknown():
    assert i18n.t("not_a_real_key", language="tr") == "not_a_real_key"


def test_t_falls_back_to_english_when_language_has_no_entry():
    # Every key here has both en/tr, so fake an entry with only "en" to
    # exercise the per-key fallback path.
    original = i18n.STRINGS["my_classes"]
    i18n.STRINGS["my_classes"] = {"en": "My Classes"}
    try:
        assert i18n.t("my_classes", language="tr") == "My Classes"
    finally:
        i18n.STRINGS["my_classes"] = original


def test_t_uses_saved_preference_when_language_not_given(monkeypatch, tmp_path):
    pref_path = tmp_path / ".language_preference"
    pref_path.write_text("tr")
    monkeypatch.setattr(i18n, "LANGUAGE_PREFERENCE_PATH", pref_path)

    assert i18n.t("settings") == "Ayarlar"
