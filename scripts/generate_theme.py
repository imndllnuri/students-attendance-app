"""Renders resources/styles/theme.qss.tmpl into the real theme.qss file
consumed by the app, filling every `{{token}}` placeholder by NAME from
shared/palette.py's PALETTE, plus the RADIUS/SPACING scales.

Run this after editing theme.qss.tmpl or the tokens in shared/palette.py.
Never hand-edit theme.qss directly - it's overwritten.
"""

import re
from pathlib import Path

from shared.palette import PALETTE, RADIUS, SPACING

TEMPLATE = Path(__file__).parent.parent / "resources" / "styles" / "theme.qss.tmpl"
LIGHT_QSS = Path(__file__).parent.parent / "resources" / "styles" / "theme.qss"

_TOKEN_RE = re.compile(r"\{\{(\w+)\}\}")


def _tokens_for(palette: dict) -> dict:
    """Merges the color palette with the radius/spacing scales."""
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
    print(f"Wrote {LIGHT_QSS}")


if __name__ == "__main__":
    main()
