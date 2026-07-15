"""Covers #27: dark mode preference persistence and the generated dark QSS."""

import re
from pathlib import Path

import shared.theme as theme


def test_defaults_to_light_when_no_preference_file(monkeypatch, tmp_path):
    monkeypatch.setattr(theme, "THEME_PREFERENCE_PATH", tmp_path / "missing")
    assert theme.load_theme_preference() == "light"
    assert theme.stylesheet_path("light") == theme.LIGHT_QSS_PATH


def test_save_then_load_round_trips_dark_preference(monkeypatch, tmp_path):
    pref_path = tmp_path / ".theme_preference"
    monkeypatch.setattr(theme, "THEME_PREFERENCE_PATH", pref_path)

    theme.save_theme_preference("dark")

    assert theme.load_theme_preference() == "dark"
    assert theme.stylesheet_path("dark") == theme.DARK_QSS_PATH


def test_invalid_preference_file_content_falls_back_to_light(monkeypatch, tmp_path):
    pref_path = tmp_path / ".theme_preference"
    pref_path.write_text("not-a-real-theme")
    monkeypatch.setattr(theme, "THEME_PREFERENCE_PATH", pref_path)

    assert theme.load_theme_preference() == "light"


def test_generated_dark_qss_is_up_to_date_with_the_generator():
    """Regression guard: theme_dark.qss must match what
    scripts/generate_dark_theme.py produces from the current theme.qss and
    palettes, catching both drift (forgot to re-run it) and substitution
    bugs (e.g. two keys sharing a light hex clobbering each other)."""
    from scripts.generate_dark_theme import DARK_QSS, LIGHT_QSS, generate_dark_qss

    checked_in = DARK_QSS.read_text()
    regenerated = generate_dark_qss(LIGHT_QSS.read_text())

    assert checked_in == regenerated


def test_specific_known_substitutions_are_correct():
    """Spot-checks a few concrete rules rather than re-deriving the whole
    substitution map generically (see test above for the full-file check)."""
    repo_root = Path(__file__).parent.parent
    dark_qss = (repo_root / "resources" / "styles" / "theme_dark.qss").read_text()

    assert "background-color: #334155;\n    color: #CBD5E1;" in dark_qss  # header row
    assert "QPushButton#delete_account_btn:hover {\n    background-color: #7F1D1D;" in dark_qss
    assert "#3730A3" in dark_qss  # disabled-button background (was light indigo #C7D2FE)
