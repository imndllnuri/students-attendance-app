"""Design tokens - the single source of truth for color/spacing/radius
values used across the app. Qt stylesheets have no variables, so
resources/styles/theme.qss.tmpl references these tokens by name
(`{{token_name}}`) and scripts/generate_theme.py renders it into the real
theme.qss/theme_dark.qss files consumed at runtime - never hand-edit those
generated files directly, edit the template instead and re-run the script.

Any Python code that sets colors dynamically (e.g. per-cell pass/fail/
attendance-status coloring in table widgets, which QSS can't express since
it's driven by cell content, not a static widget state) must import from
here rather than hardcoding a QColor/hex value, so both places stay in sync
by construction.
"""

PALETTE = {
    # Background layers - Kintsugi direction (see .claude/plans/wild-jingling-unicorn.md):
    # mostly-white/black chrome with a sparing blue accent, replacing the
    # earlier "Enterprise Dense" navy-sidebar look.
    "bg_app": "#EEF0FA",
    "bg_app_gradient_start": "#E7E9FA",
    "bg_app_gradient_end": "#EFEFF7",
    "bg_card": "#FFFFFF",
    "bg_elevated": "#FFFFFF",
    "bg_sidebar": "#FFFFFF",
    "bg_hover": "#F4F4F8",
    "bg_nav_active_pill": "#F1F1F5",

    # Text
    "text_primary": "#111114",
    "text_secondary": "#6B6B76",
    "text_disabled": "#C7C7D1",

    # Accent / brand
    "accent": "#2F5CF0",
    "accent_hover": "#254BC7",
    "accent_pressed": "#1D3D9E",
    "accent_subtle": "#EAF0FE",

    # Semantic status colors (Present/Pass, Late, Absent/Fail) - kept in the
    # same hue families as before; these are load-bearing for attendance
    # status coding throughout roster tables and charts.
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
    "border": "#E7E7EE",
    "border_strong": "#D6D6E0",
}

# Dark-mode counterpart to PALETTE, same keys - resources/styles/theme_dark.qss
# is generated from resources/styles/theme.qss.tmpl (see scripts/generate_theme.py).
# Dynamic per-cell coloring (qcolor(), class_tag_color()) intentionally still
# uses the light PALETTE in both themes - only the static QSS chrome and
# matplotlib charts (via active_palette()) are dark-mode aware.
DARK_PALETTE = {
    "bg_app": "#14141B",
    "bg_app_gradient_start": "#14141B",
    "bg_app_gradient_end": "#1B1B24",
    "bg_card": "#1E1E27",
    "bg_elevated": "#1E1E27",
    "bg_sidebar": "#17171F",
    "bg_hover": "#24242E",
    "bg_nav_active_pill": "#24242E",

    "text_primary": "#F1F1F5",
    "text_secondary": "#A0A0AC",
    "text_disabled": "#54545F",

    "accent": "#5B7FF5",
    "accent_hover": "#7C99F7",
    "accent_pressed": "#2F5CF0",
    "accent_subtle": "#22315E",

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

    "border": "#2E2E38",
    "border_strong": "#3D3D49",
}

# Class-card color tags: a small, hand-picked set of distinct hues (not an
# arbitrary hash-to-RGB, which tends to produce muddy colors).
CLASS_TAG_COLORS = [
    "#4F46E5", "#0EA5E9", "#16A34A", "#D97706",
    "#DC2626", "#DB2777", "#7C3AED", "#0D9488",
]

# Spacing scale (px) for the Kintsugi-direction redesign (see the plan at
# .claude/plans/wild-jingling-unicorn.md) - wider than the Enterprise Dense
# scale to match Kintsugi's generous whitespace. Consumed by
# resources/styles/theme.qss.tmpl (via scripts/generate_theme.py) and by
# Python code that builds widgets programmatically.
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
    "xxl": 48,
}

# Radius scale (px) for the same redesign. "pill" is meant to be passed to
# QSS as `border-radius: 999px` on a widget with a fixed/min height, so it
# always renders as a true pill rather than a rounded rectangle.
RADIUS = {
    "card": 20,
    "control_sm": 10,
    "pill": 999,
    "avatar": 999,
}

# Tag-chip colors for the new redesign: each entry is a (dot, tint) pair -
# "dot" is the small colored-circle color, "tint" is the pill's light
# background fill. Additive alongside CLASS_TAG_COLORS (which class_tag_color()
# depends on and keeps working unchanged) rather than a replacement, since tag
# chips are a distinct, richer concept (dot + tinted pill) from a single flat
# tag-strip color.
TAG_COLORS = {
    "indigo": {"dot": "#6366F1", "tint": "#EEF0FE"},
    "sky": {"dot": "#38BDF8", "tint": "#E8F7FE"},
    "green": {"dot": "#22C55E", "tint": "#E9FBEF"},
    "amber": {"dot": "#F59E0B", "tint": "#FEF3DE"},
    "rose": {"dot": "#FB7185", "tint": "#FFEEF0"},
    "violet": {"dot": "#A78BFA", "tint": "#F3EFFE"},
    "teal": {"dot": "#14B8A6", "tint": "#E6FAF8"},
    "slate": {"dot": "#94A3B8", "tint": "#F1F3F6"},
}

DARK_TAG_COLORS = {
    "indigo": {"dot": "#818CF8", "tint": "#2A2A5C"},
    "sky": {"dot": "#5FCBFB", "tint": "#173A4A"},
    "green": {"dot": "#4ADE80", "tint": "#173A26"},
    "amber": {"dot": "#FBBF24", "tint": "#3D2E0E"},
    "rose": {"dot": "#FDA4AF", "tint": "#3D1E22"},
    "violet": {"dot": "#C4B5FD", "tint": "#2E2650"},
    "teal": {"dot": "#5EEAD4", "tint": "#123531"},
    "slate": {"dot": "#CBD5E1", "tint": "#2A2E36"},
}


def active_palette() -> dict:
    """Returns the currently-active PALETTE or DARK_PALETTE, based on the
    saved theme preference - lets code that colors things dynamically
    (matplotlib charts, custom-painted widgets) follow dark mode instead of
    always reading the light PALETTE."""
    from shared.theme import load_theme_preference

    return DARK_PALETTE if load_theme_preference() == "dark" else PALETTE


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
