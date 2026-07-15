"""Shared card drop-shadow, matching the Kintsugi redesign direction: a
softer, more "lifted" depth cue than the old Enterprise Dense flat shadow.

Three presets cover every card in the app:
  sm - card-grid items (many on screen at once, needs a light touch)
  md - Info panel / Class Detail / Settings / Profile cards
  lg - centered auth cards (Login/Create Account/Reset Password), which sit
       directly on the gradient canvas and need the most "floating" feel
"""

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

_PRESETS = {
    "sm": {"blur": 20, "offset": (0, 4), "alpha": 22},
    "md": {"blur": 28, "offset": (0, 6), "alpha": 26},
    "lg": {"blur": 40, "offset": (0, 10), "alpha": 30},
}


def apply_card_shadow(widget, strength="md"):
    preset = _PRESETS[strength]
    x_offset, y_offset = preset["offset"]

    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(preset["blur"])
    shadow.setXOffset(x_offset)
    shadow.setYOffset(y_offset)
    shadow.setColor(QColor(30, 30, 40, preset["alpha"]))
    widget.setGraphicsEffect(shadow)
