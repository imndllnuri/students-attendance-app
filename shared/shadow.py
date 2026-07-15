"""Shared card drop-shadow, matching the "Enterprise Dense" direction:
a flatter, more subtle depth cue than a typical SaaS card shadow."""

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect


def apply_card_shadow(widget):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(12)
    shadow.setXOffset(0)
    shadow.setYOffset(2)
    shadow.setColor(QColor(15, 23, 42, 20))
    widget.setGraphicsEffect(shadow)
