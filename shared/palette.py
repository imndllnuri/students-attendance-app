"""Design tokens - the single source of truth for color values used across
the app. Qt stylesheets have no variables, so resources/theme.qss embeds
these same hex values directly (with a comment header listing the tokens
for humans); any Python code that sets colors dynamically (e.g. per-cell
pass/fail/attendance-status coloring in table widgets, which QSS can't
express since it's driven by cell content, not a static widget state)
must import from here rather than hardcoding a QColor/hex value, so both
places stay in sync by construction.

If theme.qss and this file drift apart, this file wins - update the QSS
to match.
"""

PALETTE = {
    # Background layers
    "bg_app": "#F8FAFC",
    "bg_card": "#FFFFFF",
    "bg_elevated": "#FFFFFF",
    "bg_sidebar": "#1E293B",
    "bg_hover": "#F1F5F9",

    # Text
    "text_primary": "#0F172A",
    "text_secondary": "#64748B",
    "text_disabled": "#CBD5E1",
    "text_on_dark": "#E2E8F0",
    "text_on_dark_muted": "#94A3B8",

    # Accent / brand
    "accent": "#4F46E5",
    "accent_hover": "#4338CA",
    "accent_pressed": "#3730A3",
    "accent_subtle": "#EEF2FF",

    # Semantic status colors (Present/Pass, Late, Absent/Fail)
    "success": "#16A34A",
    "success_tint": "#DCFCE7",
    "success_border": "#86EFAC",
    "success_text": "#166534",

    "warning": "#D97706",
    "warning_tint": "#FEF3C7",
    "warning_border": "#FCD34D",
    "warning_text": "#92400E",

    "error": "#DC2626",
    "error_tint": "#FEE2E2",
    "error_border": "#FCA5A5",
    "error_text": "#991B1B",

    # Borders
    "border": "#E2E8F0",
    "border_strong": "#CBD5E1",
}


def qcolor(token: str):
    """Return a QColor for a palette token. Imports PyQt5 lazily so this
    module stays importable from non-GUI code (e.g. scripts, tests) without
    requiring a display."""
    from PyQt5.QtGui import QColor

    return QColor(PALETTE[token])
