"""Covers the Kintsugi-redesign shadow preset system in shared/shadow.py."""

from PyQt5.QtWidgets import QFrame, QGraphicsDropShadowEffect

from shared.shadow import apply_card_shadow


def test_default_strength_is_md(qtbot):
    widget = QFrame()
    qtbot.addWidget(widget)

    apply_card_shadow(widget)

    effect = widget.graphicsEffect()
    assert isinstance(effect, QGraphicsDropShadowEffect)
    assert effect.blurRadius() == 28


def test_lg_strength_is_stronger_than_sm(qtbot):
    sm_widget = QFrame()
    lg_widget = QFrame()
    qtbot.addWidget(sm_widget)
    qtbot.addWidget(lg_widget)

    apply_card_shadow(sm_widget, strength="sm")
    apply_card_shadow(lg_widget, strength="lg")

    assert lg_widget.graphicsEffect().blurRadius() > sm_widget.graphicsEffect().blurRadius()
    assert lg_widget.graphicsEffect().yOffset() > sm_widget.graphicsEffect().yOffset()


def test_unknown_strength_raises():
    widget = QFrame()
    try:
        apply_card_shadow(widget, strength="xl")
    except KeyError:
        pass
    else:
        raise AssertionError("expected a KeyError for an unknown strength preset")
