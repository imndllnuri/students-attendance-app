"""Covers #35: font size / accessibility scaling preference persistence."""

import shared.font_scale as fs


def test_defaults_to_normal_when_no_preference_file(monkeypatch, tmp_path):
    monkeypatch.setattr(fs, "FONT_SCALE_PREFERENCE_PATH", tmp_path / "missing")
    assert fs.load_font_scale() == "normal"


def test_save_then_load_round_trips(monkeypatch, tmp_path):
    path = tmp_path / ".font_scale_preference"
    monkeypatch.setattr(fs, "FONT_SCALE_PREFERENCE_PATH", path)

    fs.save_font_scale("large")

    assert fs.load_font_scale() == "large"


def test_invalid_content_falls_back_to_normal(tmp_path, monkeypatch):
    path = tmp_path / ".font_scale_preference"
    path.write_text("gigantic")
    monkeypatch.setattr(fs, "FONT_SCALE_PREFERENCE_PATH", path)

    assert fs.load_font_scale() == "normal"


def test_point_size_scales_relative_to_base():
    assert fs.point_size_for_scale("normal") == fs.BASE_POINT_SIZE
    assert fs.point_size_for_scale("small") < fs.BASE_POINT_SIZE
    assert fs.point_size_for_scale("large") > fs.BASE_POINT_SIZE
    assert fs.point_size_for_scale("extra_large") > fs.point_size_for_scale("large")


def test_point_size_for_unknown_scale_defaults_to_base():
    assert fs.point_size_for_scale("unknown") == fs.BASE_POINT_SIZE
