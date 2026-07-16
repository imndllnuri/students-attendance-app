"""Covers scripts/generate_theme.py's token-substitution pipeline that
renders resources/styles/theme.qss.tmpl into the real theme.qss."""

from pathlib import Path


def test_generated_qss_is_up_to_date_with_the_template():
    """Regression guard: theme.qss must match what scripts/generate_theme.py
    produces from the current theme.qss.tmpl and palette - catches both
    drift (forgot to re-run it) and template changes that reference a token
    shared/palette.py doesn't define."""
    from scripts.generate_theme import LIGHT_QSS, TEMPLATE, render
    from shared.palette import PALETTE

    template_text = TEMPLATE.read_text()

    assert LIGHT_QSS.read_text() == render(template_text, PALETTE)


def test_template_has_no_unresolved_placeholders():
    repo_root = Path(__file__).parent.parent
    qss = (repo_root / "resources" / "styles" / "theme.qss").read_text()

    assert "{{" not in qss


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

    assert result == "border-radius: 999px; margin: 12px;"
