"""Covers #36: session-timeout preference persistence."""

import shared.session_timeout as st


def test_defaults_to_15_minutes_when_no_preference_file(monkeypatch, tmp_path):
    monkeypatch.setattr(st, "SESSION_TIMEOUT_PREFERENCE_PATH", tmp_path / "missing")
    assert st.load_session_timeout_minutes() == 15


def test_save_then_load_round_trips(monkeypatch, tmp_path):
    pref_path = tmp_path / ".session_timeout_preference"
    monkeypatch.setattr(st, "SESSION_TIMEOUT_PREFERENCE_PATH", pref_path)

    st.save_session_timeout_minutes(30)

    assert st.load_session_timeout_minutes() == 30


def test_never_option_round_trips_as_zero(monkeypatch, tmp_path):
    pref_path = tmp_path / ".session_timeout_preference"
    monkeypatch.setattr(st, "SESSION_TIMEOUT_PREFERENCE_PATH", pref_path)

    st.save_session_timeout_minutes(0)

    assert st.load_session_timeout_minutes() == 0


def test_invalid_preference_content_falls_back_to_default(tmp_path, monkeypatch):
    pref_path = tmp_path / ".session_timeout_preference"
    pref_path.write_text("not-a-number")
    monkeypatch.setattr(st, "SESSION_TIMEOUT_PREFERENCE_PATH", pref_path)

    assert st.load_session_timeout_minutes() == 15


def test_out_of_range_value_falls_back_to_default(tmp_path, monkeypatch):
    pref_path = tmp_path / ".session_timeout_preference"
    pref_path.write_text("999")
    monkeypatch.setattr(st, "SESSION_TIMEOUT_PREFERENCE_PATH", pref_path)

    assert st.load_session_timeout_minutes() == 15
