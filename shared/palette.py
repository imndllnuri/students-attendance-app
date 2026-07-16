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

Token set below matches the "AttendU" reference redesign (see
reference-theme/student-attendance-app-redesign-prompt.md and
reference-theme/ASSUMPTIONS.md) - a dark-first purple/blue-gradient look,
replacing the earlier "Kintsugi" white/black-chrome direction. The internal
key name `error` is kept (not renamed to the spec's "danger") purely for
call-site continuity - every existing `qcolor("error_tint")`-style call
across the app keeps working; it's the same semantic color the spec calls
"danger."
"""

PALETTE = {
    # Background layers - AttendU direction: a cool light-gray page behind
    # white cards, NOT theme-reactive chrome (see bg_sidebar below).
    "bg_app": "#EEF0F5",
    "bg_card": "#FFFFFF",
    "bg_elevated": "#FFFFFF",
    "bg_hover": "#F4F5F9",

    # Sidebar + the auth screens' left brand panel are ALWAYS dark,
    # regardless of the light/dark toggle - confirmed directly from the
    # reference screenshots (the light-mode Dashboard/Settings shots still
    # show a dark sidebar). These are fixed values, not swapped by theme.
    "bg_sidebar": "#12141C",
    "bg_sidebar_hover": "#1B202C",
    "bg_sidebar_active": "#1F2333",
    "text_sidebar": "#C7CCDA",
    "text_sidebar_muted": "#767D91",

    # Text
    "text_primary": "#1B1E2B",
    "text_secondary": "#8A93A7",
    "text_disabled": "#C2C7D4",

    # Accent / brand - primary CTAs use a purple-to-blue gradient
    # (accent -> accent_end), everything else (links, focus rings, active
    # nav, selected calendar day) uses the flat accent color.
    "accent": "#7C6EF7",
    "accent_end": "#6D8CFA",
    "accent_hover": "#6C5CE1",
    "accent_pressed": "#5B4FD1",
    "accent_subtle": "#EEECFE",

    # Semantic status colors (Present/Pass, Late, Absent/Fail) - load-bearing
    # for attendance status coding throughout roster tables and charts.
    "success": "#16A34A",
    "success_tint": "#DCFCE7",
    "success_border": "#86EFAC",
    "success_text": "#166534",

    "warning": "#B45309",
    "warning_tint": "#FEF3C7",
    "warning_border": "#FCD34D",
    "warning_text": "#92400E",

    "error": "#DC2626",
    "error_tint": "#FEE2E2",
    "error_border": "#FCA5A5",
    "error_text": "#991B1B",

    # Neutral pill (inactive/tag chips)
    "neutral_pill_bg": "#F1F2F6",
    "neutral_pill_text": "#6B7280",

    # Borders
    "border": "#E4E7ED",
    "border_strong": "#D4D8E2",
}

# Dark-mode counterpart to PALETTE, same keys - resources/styles/theme_dark.qss
# is generated from resources/styles/theme.qss.tmpl (see scripts/generate_theme.py).
# Dynamic per-cell coloring (qcolor(), class_tag_color()) intentionally still
# uses the light PALETTE in both themes - only the static QSS chrome and
# matplotlib charts (via active_palette()) are dark-mode aware.
DARK_PALETTE = {
    "bg_app": "#0B0E14",
    "bg_card": "#161A24",
    "bg_elevated": "#1B202C",
    "bg_hover": "#1E2330",

    # Sidebar stays the same fixed dark values in both themes - see PALETTE.
    "bg_sidebar": "#12141C",
    "bg_sidebar_hover": "#1B202C",
    "bg_sidebar_active": "#1F2333",
    "text_sidebar": "#C7CCDA",
    "text_sidebar_muted": "#767D91",

    "text_primary": "#F1F2F6",
    "text_secondary": "#8790A6",
    "text_disabled": "#4B5162",

    "accent": "#8B7CF9",
    "accent_end": "#6EA8FE",
    "accent_hover": "#9D90FA",
    "accent_pressed": "#7C6EF7",
    "accent_subtle": "#262040",

    "success": "#4ADE80",
    "success_tint": "#123722",
    "success_border": "#16A34A",
    "success_text": "#BBF7D0",

    "warning": "#FBBF24",
    "warning_tint": "#3A2E0F",
    "warning_border": "#B45309",
    "warning_text": "#FDE68A",

    "error": "#F87171",
    "error_tint": "#3A1414",
    "error_border": "#DC2626",
    "error_text": "#FECACA",

    "neutral_pill_bg": "#232838",
    "neutral_pill_text": "#9AA1B4",

    "border": "#262B38",
    "border_strong": "#333A4A",
}

# Class-card color tags: a small, hand-picked set of distinct hues (not an
# arbitrary hash-to-RGB, which tends to produce muddy colors). Matches the
# 9-swatch "Class Color" picker shown in the Add/Edit Class wizard's
# Color & Confirm step.
CLASS_TAG_COLORS = [
    "#7C6EF7", "#3B82F6", "#22C55E", "#F59E0B",
    "#F87171", "#A78BFA", "#FB923C", "#38BDF8", "#34D399",
]

# Spacing scale (px): base unit 4px on the spec's 4/8/12/16/20/24/32 ramp.
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 20,
    "xxl": 24,
    "xxxl": 32,
}

# Radius scale (px). "pill" is meant to be passed to QSS as
# `border-radius: 999px` on a widget with a fixed/min height, so it always
# renders as a true pill rather than a rounded rectangle.
RADIUS = {
    "card": 16,
    "control_sm": 10,
    "pill": 999,
    "avatar": 999,
}

# Tag-chip colors: each entry is a (dot, tint) pair - "dot" is the small
# colored-circle color, "tint" is the pill's light background fill.
# Additive alongside CLASS_TAG_COLORS (which class_tag_color() depends on
# and keeps working unchanged) rather than a replacement, since tag chips
# are a distinct, richer concept (dot + tinted pill) from a single flat
# tag-strip color.
TAG_COLORS = {
    "indigo": {"dot": "#7C6EF7", "tint": "#EEECFE"},
    "sky": {"dot": "#38BDF8", "tint": "#E8F7FE"},
    "green": {"dot": "#22C55E", "tint": "#E9FBEF"},
    "amber": {"dot": "#F59E0B", "tint": "#FEF3DE"},
    "rose": {"dot": "#FB7185", "tint": "#FFEEF0"},
    "violet": {"dot": "#A78BFA", "tint": "#F3EFFE"},
    "teal": {"dot": "#14B8A6", "tint": "#E6FAF8"},
    "slate": {"dot": "#94A3B8", "tint": "#F1F3F6"},
}

DARK_TAG_COLORS = {
    "indigo": {"dot": "#8B7CF9", "tint": "#262040"},
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


def attendance_tier(percent: float, minimum: float) -> str:
    """The spec's tier-coloring rule, used everywhere a percentage or a bar
    needs a success/warning/error classification: danger below the class's
    configured minimum, warning within 10 points above it, success 10+
    points above it."""
    if percent < minimum:
        return "error"
    if percent < minimum + 10:
        return "warning"
    return "success"


def class_tag_color(class_code: str) -> str:
    """Deterministic color per class code, stable across app restarts
    (Python's built-in hash() is randomized per-process, so it can't be
    used here - crc32 is stable)."""
    import zlib

    index = zlib.crc32(class_code.encode("utf-8")) % len(CLASS_TAG_COLORS)
    return CLASS_TAG_COLORS[index]


def class_tag_color_key(class_code: str) -> str:
    """Deterministic TAG_COLORS/DARK_TAG_COLORS key per class code, for
    contexts that need a named tag-pill color (see shared.widgets.make_tag_pill)
    rather than class_tag_color()'s raw hex (used for the class-card
    illustration tint)."""
    import zlib

    keys = list(TAG_COLORS.keys())
    return keys[zlib.crc32(class_code.encode("utf-8")) % len(keys)]
