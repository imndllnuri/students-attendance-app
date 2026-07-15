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
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "accent_pressed": "#1E40AF",
    "accent_subtle": "#EFF6FF",

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

# Dark-mode counterpart to PALETTE, same keys - resources/styles/theme_dark.qss
# is generated from theme.qss by substituting each PALETTE[key] hex for
# DARK_PALETTE[key] (see scripts/generate_dark_theme.py). Dynamic per-cell
# coloring (qcolor(), class_tag_color()) intentionally still uses the light
# PALETTE in both themes - only the static QSS chrome is dark-mode aware for
# now; see ROADMAP.md.
DARK_PALETTE = {
    "bg_app": "#0F172A",
    "bg_card": "#1E293B",
    "bg_elevated": "#1E293B",
    "bg_sidebar": "#0B1120",
    "bg_hover": "#334155",

    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_disabled": "#475569",
    "text_on_dark": "#E2E8F0",
    "text_on_dark_muted": "#94A3B8",

    "accent": "#3B82F6",
    "accent_hover": "#60A5FA",
    "accent_pressed": "#2563EB",
    "accent_subtle": "#1E3A8A",

    "success": "#22C55E",
    "success_tint": "#14532D",
    "success_border": "#16A34A",
    "success_text": "#BBF7D0",

    "warning": "#F59E0B",
    "warning_tint": "#78350F",
    "warning_border": "#D97706",
    "warning_text": "#FDE68A",

    "error": "#EF4444",
    "error_tint": "#7F1D1D",
    "error_border": "#DC2626",
    "error_text": "#FECACA",

    "border": "#334155",
    "border_strong": "#475569",
}

# Class-card color tags: a small, hand-picked set of distinct hues (not an
# arbitrary hash-to-RGB, which tends to produce muddy colors).
CLASS_TAG_COLORS = [
    "#4F46E5", "#0EA5E9", "#16A34A", "#D97706",
    "#DC2626", "#DB2777", "#7C3AED", "#0D9488",
]


def qcolor(token: str):
    """Return a QColor for a palette token. Imports PyQt5 lazily so this
    module stays importable from non-GUI code (e.g. scripts, tests) without
    requiring a display."""
    from PyQt5.QtGui import QColor

    return QColor(PALETTE[token])


def class_tag_color(class_code: str) -> str:
    """Deterministic color per class code, stable across app restarts
    (Python's built-in hash() is randomized per-process, so it can't be
    used here - crc32 is stable)."""
    import zlib

    index = zlib.crc32(class_code.encode("utf-8")) % len(CLASS_TAG_COLORS)
    return CLASS_TAG_COLORS[index]
