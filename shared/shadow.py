"""Shared card drop-shadow. Three presets cover every card in the app:
  sm - card-grid items (many on screen at once, needs a light touch)
  md - Info panel / Class Detail / Settings / Profile cards
  lg - centered auth cards (Login/Create Account/Reset Password)

Per the AttendU spec's elevation rule (§4.4): light mode gets a soft drop
shadow, dark mode skips the shadow entirely and relies on the card's border
plus its slightly-lighter-than-background surface color instead - stacking
a shadow on top of an already-dark surface reads muddy rather than "lifted."
"""

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

from shared.theme import load_theme_preference

_PRESETS = {
    "sm": {"blur": 20, "offset": (0, 4), "alpha": 22},
    "md": {"blur": 28, "offset": (0, 6), "alpha": 26},
    "lg": {"blur": 40, "offset": (0, 10), "alpha": 30},
}


def apply_card_shadow(widget, strength="md"):
    if load_theme_preference() == "dark":
        widget.setGraphicsEffect(None)
        return

    preset = _PRESETS[strength]
    x_offset, y_offset = preset["offset"]

    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(preset["blur"])
    shadow.setXOffset(x_offset)
    shadow.setYOffset(y_offset)
    shadow.setColor(QColor(30, 30, 40, preset["alpha"]))
    widget.setGraphicsEffect(shadow)
