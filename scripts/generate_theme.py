"""Renders resources/styles/theme.qss.tmpl into the real light/dark QSS
files consumed by the app (resources/styles/theme.qss and theme_dark.qss),
filling every `{{token}}` placeholder by NAME from shared/palette.py's
PALETTE (light output) or DARK_PALETTE (dark output), plus the
theme-independent RADIUS/SPACING scales.

This replaces the older scripts/generate_dark_theme.py, which generated
theme_dark.qss from theme.qss by matching literal hex VALUES - two tokens
that happen to share a light-mode hex but need different dark-mode values
(or vice versa) could silently collide under that approach. Substituting by
token name instead of by hex value eliminates that whole bug class.

Run this after editing theme.qss.tmpl or the tokens in shared/palette.py.
Never hand-edit theme.qss/theme_dark.qss directly - they're overwritten.
"""

import re
from pathlib import Path

from shared.palette import DARK_PALETTE, PALETTE, RADIUS, SPACING

TEMPLATE = Path(__file__).parent.parent / "resources" / "styles" / "theme.qss.tmpl"
LIGHT_QSS = Path(__file__).parent.parent / "resources" / "styles" / "theme.qss"
DARK_QSS = Path(__file__).parent.parent / "resources" / "styles" / "theme_dark.qss"

_TOKEN_RE = re.compile(r"\{\{(\w+)\}\}")


def _tokens_for(palette: dict) -> dict:
    """Merges a color palette (PALETTE or DARK_PALETTE) with the
    theme-independent radius/spacing scales, which render identically in
    both light and dark output."""
    tokens = dict(palette)
    tokens.update({f"radius_{key}": value for key, value in RADIUS.items()})
    tokens.update({f"spacing_{key}": value for key, value in SPACING.items()})
    return tokens


def render(template_text: str, palette: dict) -> str:
    tokens = _tokens_for(palette)

    def replace(match):
        name = match.group(1)
        if name not in tokens:
            raise KeyError(f"theme.qss.tmpl references unknown token {{{{{name}}}}}")
        return str(tokens[name])

    return _TOKEN_RE.sub(replace, template_text)


def main():
    template_text = TEMPLATE.read_text()
    LIGHT_QSS.write_text(render(template_text, PALETTE))
    DARK_QSS.write_text(render(template_text, DARK_PALETTE))
    print(f"Wrote {LIGHT_QSS}")
    print(f"Wrote {DARK_QSS}")


if __name__ == "__main__":
    main()
