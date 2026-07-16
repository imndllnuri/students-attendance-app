"""Covers the shadow preset system in shared/shadow.py, including the
AttendU spec's §4.4 rule that dark mode skips the shadow entirely."""

from PyQt5.QtWidgets import QFrame, QGraphicsDropShadowEffect

import shared.shadow as shadow_module
from shared.shadow import apply_card_shadow


def _force_theme(monkeypatch, tmp_path, theme):
    pref_path = tmp_path / ".theme_preference"
    pref_path.write_text(theme)
    monkeypatch.setattr("shared.theme.THEME_PREFERENCE_PATH", pref_path)


def test_default_strength_is_md(qtbot, monkeypatch, tmp_path):
    _force_theme(monkeypatch, tmp_path, "light")
    widget = QFrame()
    qtbot.addWidget(widget)

    apply_card_shadow(widget)

    effect = widget.graphicsEffect()
    assert isinstance(effect, QGraphicsDropShadowEffect)
    assert effect.blurRadius() == 28


def test_lg_strength_is_stronger_than_sm(qtbot, monkeypatch, tmp_path):
    _force_theme(monkeypatch, tmp_path, "light")
    sm_widget = QFrame()
    lg_widget = QFrame()
    qtbot.addWidget(sm_widget)
    qtbot.addWidget(lg_widget)

    apply_card_shadow(sm_widget, strength="sm")
    apply_card_shadow(lg_widget, strength="lg")

    assert lg_widget.graphicsEffect().blurRadius() > sm_widget.graphicsEffect().blurRadius()
    assert lg_widget.graphicsEffect().yOffset() > sm_widget.graphicsEffect().yOffset()


def test_unknown_strength_raises(monkeypatch, tmp_path):
    _force_theme(monkeypatch, tmp_path, "light")
    widget = QFrame()
    try:
        apply_card_shadow(widget, strength="xl")
    except KeyError:
        pass
    else:
        raise AssertionError("expected a KeyError for an unknown strength preset")


def test_dark_mode_skips_the_shadow_entirely(qtbot, monkeypatch, tmp_path):
    _force_theme(monkeypatch, tmp_path, "dark")
    widget = QFrame()
    qtbot.addWidget(widget)

    apply_card_shadow(widget, strength="lg")

    assert widget.graphicsEffect() is None
