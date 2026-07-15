"""Small helper for the dynamic-Qt-property-driven QSS pattern used
throughout this app's stylesheets (`[variant="primary"]`, `[error="true"]`,
`[active="true"]`, `[state="idle"]`, etc.).

A property set via `widget.setProperty(...)` alone only takes effect if the
widget is later force-repolished - forgetting the unpolish/polish call is an
easy, silent mistake (the widget just renders unstyled/default and nothing
raises an error), so this wraps the whole three-call sequence in one place.
"""


def set_dynamic_property(widget, name: str, value) -> None:
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
