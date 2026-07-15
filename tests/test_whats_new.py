"""Covers #40: What's New changelog dialog shown once per version bump."""

import shared.whats_new as wn


def test_first_run_shows_whats_new(monkeypatch, tmp_path):
    monkeypatch.setattr(wn, "LAST_SEEN_VERSION_PATH", tmp_path / "missing")
    assert wn.load_last_seen_version() == ""
    assert wn.should_show_whats_new() is True


def test_saving_current_version_stops_it_showing_again(monkeypatch, tmp_path):
    path = tmp_path / ".last_seen_version"
    monkeypatch.setattr(wn, "LAST_SEEN_VERSION_PATH", path)

    wn.save_last_seen_version(wn.APP_VERSION)

    assert wn.load_last_seen_version() == wn.APP_VERSION
    assert wn.should_show_whats_new() is False


def test_older_seen_version_still_shows_it(monkeypatch, tmp_path):
    path = tmp_path / ".last_seen_version"
    monkeypatch.setattr(wn, "LAST_SEEN_VERSION_PATH", path)

    wn.save_last_seen_version("0.0.1")

    assert wn.should_show_whats_new() is True
