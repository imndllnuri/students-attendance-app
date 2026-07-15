"""Regenerates resources/styles/theme_dark.qss from theme.qss by substituting
each PALETTE[key] hex value for its DARK_PALETTE[key] counterpart, plus a
small map of one-off hex literals in theme.qss that aren't PALETTE tokens.
Run this after editing theme.qss or the palettes in shared/palette.py.
"""

import re
from pathlib import Path

from shared.palette import DARK_PALETTE, PALETTE

# One-off hex literals in theme.qss that aren't PALETTE tokens (e.g. a
# hover-state tint used in exactly one place) -> their dark-mode replacement.
EXTRA_HEX_MAP = {
    "#BFDBFE": "#1E3A8A",  # light blue (disabled bg / hover border)
    "#FECACA": "#7F1D1D",  # light red hover background
    "#334155": "#CBD5E1",  # dark slate text -> light slate text on dark bg
}

LIGHT_QSS = Path(__file__).parent.parent / "resources" / "styles" / "theme.qss"
DARK_QSS = Path(__file__).parent.parent / "resources" / "styles" / "theme_dark.qss"


def generate_dark_qss(light_content: str) -> str:
    # Single-pass replacement: some dark values coincidentally equal other
    # keys' light source hex (e.g. dark bg_hover == the light literal we
    # remap separately), so sequential .replace() calls would corrupt each
    # other's output. A regex sub over the whole mapping replaces every
    # match against the *original* text exactly once instead.
    mapping = {light.upper(): DARK_PALETTE[key] for key, light in PALETTE.items()}
    mapping.update({k.upper(): v for k, v in EXTRA_HEX_MAP.items()})

    pattern = re.compile("|".join(re.escape(h) for h in mapping), re.IGNORECASE)
    content = pattern.sub(lambda m: mapping[m.group(0).upper()], light_content)

    # text_on_dark and border share the same light hex (#E2E8F0), so the
    # blanket substitution above can't tell them apart - text_on_dark isn't
    # actually used in any QSS rule (only mentioned in the header comment),
    # so patch just that comment line back to its real DARK_PALETTE value.
    content = re.sub(
        r"(text_on_dark\s+)#[0-9A-Fa-f]{6}",
        lambda m: m.group(1) + DARK_PALETTE["text_on_dark"],
        content,
    )

    content = content.replace(
        '/* Shared theme for the whole app - "Modern SaaS, Light" direction.\n'
        "   theme_dark.qss is generated from this file by\n"
        "   scripts/generate_dark_theme.py - re-run it after editing colors here.\n",
        '/* GENERATED FILE - do not edit directly. Run\n'
        "   scripts/generate_dark_theme.py after changing theme.qss or\n"
        "   shared/palette.py's DARK_PALETTE instead.\n"
        '   Dark-mode counterpart to theme.qss ("Modern SaaS, Light" direction).\n',
    )

    return content


def main():
    DARK_QSS.write_text(generate_dark_qss(LIGHT_QSS.read_text()))
    print(f"Wrote {DARK_QSS}")


if __name__ == "__main__":
    main()
