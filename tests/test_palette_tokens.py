"""Covers the new Kintsugi-redesign design tokens added to shared/palette.py
(spacing/radius scales, tag colors, active_palette())."""

import shared.palette as palette
from shared.palette import (
    DARK_PALETTE,
    DARK_TAG_COLORS,
    PALETTE,
    RADIUS,
    SPACING,
    TAG_COLORS,
    active_palette,
)


def test_spacing_scale_is_ascending():
    values = [SPACING["xs"], SPACING["sm"], SPACING["md"], SPACING["lg"], SPACING["xl"], SPACING["xxl"]]
    assert values == sorted(values)
    assert len(set(values)) == len(values)


def test_radius_scale_has_expected_keys():
    assert set(RADIUS) == {"card", "control_sm", "pill", "avatar"}
    assert RADIUS["pill"] == RADIUS["avatar"] == 999


def test_tag_colors_light_and_dark_have_matching_keys():
    assert set(TAG_COLORS) == set(DARK_TAG_COLORS)
    for name, entry in TAG_COLORS.items():
        assert set(entry) == {"dot", "tint"}
        assert set(DARK_TAG_COLORS[name]) == {"dot", "tint"}


def test_active_palette_defaults_to_light(monkeypatch, tmp_path):
    monkeypatch.setattr("shared.theme.THEME_PREFERENCE_PATH", tmp_path / "missing")
    assert active_palette() is PALETTE


def test_active_palette_returns_dark_when_preference_is_dark(monkeypatch, tmp_path):
    pref_path = tmp_path / ".theme_preference"
    pref_path.write_text("dark")
    monkeypatch.setattr("shared.theme.THEME_PREFERENCE_PATH", pref_path)
    assert active_palette() is DARK_PALETTE
