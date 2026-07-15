"""Covers #27: dark mode preference persistence and the generated dark QSS."""

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


def test_generated_qss_files_are_up_to_date_with_the_template():
    """Regression guard: theme.qss and theme_dark.qss must match what
    scripts/generate_theme.py produces from the current theme.qss.tmpl and
    palettes - catches both drift (forgot to re-run it) and template
    changes that reference a token shared/palette.py doesn't define."""
    from scripts.generate_theme import DARK_QSS, LIGHT_QSS, TEMPLATE, render
    from shared.palette import DARK_PALETTE, PALETTE

    template_text = TEMPLATE.read_text()

    assert LIGHT_QSS.read_text() == render(template_text, PALETTE)
    assert DARK_QSS.read_text() == render(template_text, DARK_PALETTE)


def test_template_has_no_unresolved_placeholders_in_either_output():
    repo_root = Path(__file__).parent.parent
    light_qss = (repo_root / "resources" / "styles" / "theme.qss").read_text()
    dark_qss = (repo_root / "resources" / "styles" / "theme_dark.qss").read_text()

    assert "{{" not in light_qss
    assert "{{" not in dark_qss


def test_specific_known_substitutions_are_correct():
    """Spot-checks a few concrete rules rather than re-deriving the whole
    substitution map generically (see test above for the full-file check)."""
    repo_root = Path(__file__).parent.parent
    light_qss = (repo_root / "resources" / "styles" / "theme.qss").read_text()
    dark_qss = (repo_root / "resources" / "styles" / "theme_dark.qss").read_text()

    # "Always white text on a colored control" contexts must stay pure
    # white in BOTH themes, not drift to a dark bg_card-ish value - this
    # was a real, previously-unnoticed dark-mode bug the template-based
    # (substitute-by-name, not by-hex-value) generator fixes.
    assert "QLabel#notifications_badge_lbl {\n    background-color: #DC2626;\n    color: #FFFFFF;" in light_qss
    assert "QLabel#notifications_badge_lbl {\n    background-color: #EF4444;\n    color: #FFFFFF;" in dark_qss

    assert 'QPushButton[variant="primary"] {\n    background-color: #2F5CF0;\n    color: #FFFFFF;' in light_qss
    assert 'QPushButton[variant="primary"] {\n    background-color: #5B7FF5;\n    color: #FFFFFF;' in dark_qss

    # Sidebar flips from white (light) to dark (dark mode) - the biggest
    # single token change in the Kintsugi redesign vs. the old dark-navy-
    # always sidebar.
    assert "QWidget#sidebar_widget {\n    background-color: #FFFFFF;" in light_qss
    assert "QWidget#sidebar_widget {\n    background-color: #17171F;" in dark_qss

    # Pill radius (999px) renders identically regardless of theme, since
    # radius/spacing tokens aren't color tokens.
    assert "border-radius: 999px;" in light_qss
    assert "border-radius: 999px;" in dark_qss


def test_render_raises_on_an_unknown_placeholder():
    from scripts.generate_theme import render
    from shared.palette import PALETTE

    try:
        render("QWidget { color: {{not_a_real_token}}; }", PALETTE)
    except KeyError:
        pass
    else:
        raise AssertionError("expected a KeyError for an unknown template token")


def test_render_fills_radius_and_spacing_tokens():
    from scripts.generate_theme import render
    from shared.palette import PALETTE

    result = render("border-radius: {{radius_pill}}px; margin: {{spacing_md}}px;", PALETTE)

    assert result == "border-radius: 999px; margin: 16px;"
