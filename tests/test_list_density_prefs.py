"""Covers #11: class list density preference persistence."""

import shared.list_density as ld


def test_defaults_to_comfortable_when_no_preference_file(monkeypatch, tmp_path):
    monkeypatch.setattr(ld, "DENSITY_PREFERENCE_PATH", tmp_path / "missing")
    assert ld.load_list_density() == "comfortable"


def test_save_then_load_round_trips_compact(monkeypatch, tmp_path):
    pref_path = tmp_path / ".list_density_preference"
    monkeypatch.setattr(ld, "DENSITY_PREFERENCE_PATH", pref_path)

    ld.save_list_density("compact")

    assert ld.load_list_density() == "compact"


def test_invalid_content_falls_back_to_comfortable(tmp_path, monkeypatch):
    pref_path = tmp_path / ".list_density_preference"
    pref_path.write_text("garbage")
    monkeypatch.setattr(ld, "DENSITY_PREFERENCE_PATH", pref_path)

    assert ld.load_list_density() == "comfortable"
