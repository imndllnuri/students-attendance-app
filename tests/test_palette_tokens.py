"""Covers the design tokens in shared/palette.py (spacing/radius scales,
tag colors)."""

from shared.palette import RADIUS, SPACING, TAG_COLORS


def test_spacing_scale_is_ascending():
    values = [SPACING["xs"], SPACING["sm"], SPACING["md"], SPACING["lg"], SPACING["xl"], SPACING["xxl"]]
    assert values == sorted(values)
    assert len(set(values)) == len(values)


def test_radius_scale_has_expected_keys():
    assert set(RADIUS) == {"card", "control_sm", "pill", "avatar"}
    assert RADIUS["pill"] == RADIUS["avatar"] == 999


def test_tag_colors_have_dot_and_tint():
    for name, entry in TAG_COLORS.items():
        assert set(entry) == {"dot", "tint"}
