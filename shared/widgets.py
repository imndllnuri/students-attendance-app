"""Small, reusable composite-widget builders: a stat card with a progress
bar, and a colored tag pill. These are plain factory functions rather than
QWidget subclasses since neither one changes state or handles events after
construction; callers just drop the returned widget into a layout.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from shared.palette import PALETTE, RADIUS, TAG_COLORS


def clear_layout(layout) -> None:
    """Empties a layout, detaching each child widget immediately via
    setParent(None) rather than relying on deleteLater() alone - a bare
    deleteLater() defers destruction, so a widget can still be painted at
    its old position if the layout is repopulated (e.g. with a different
    column count) before the event loop gets around to deleting it."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.setParent(None)
            widget.deleteLater()


def make_stat_card(label: str, value: str, percent: int, fill_color: str = None) -> QFrame:
    """A small rounded card: a label, a big value, and a thin rounded
    progress bar - e.g. "Attendance Rate" / "82%" / a mostly-filled bar."""
    palette = PALETTE
    fill_color = fill_color or palette["accent"]

    card = QFrame()
    card.setStyleSheet(
        f"QFrame {{ background-color: {palette['bg_card']}; "
        f"border: 1px solid {palette['border']}; "
        f"border-radius: {RADIUS['control_sm']}px; }}"
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(4)

    label_lbl = QLabel(label)
    label_lbl.setStyleSheet(f"border: none; color: {palette['text_secondary']}; font-size: 9pt;")
    layout.addWidget(label_lbl)

    value_lbl = QLabel(value)
    value_lbl.setStyleSheet(
        f"border: none; color: {palette['text_primary']}; font-size: 14pt; font-weight: 700;"
    )
    layout.addWidget(value_lbl)

    bar = QProgressBar()
    bar.setRange(0, 100)
    bar.setValue(max(0, min(100, percent)))
    bar.setTextVisible(False)
    bar.setFixedHeight(6)
    bar.setStyleSheet(
        f"QProgressBar {{ background-color: {palette['bg_hover']}; "
        f"border: none; border-radius: 3px; }}"
        f"QProgressBar::chunk {{ background-color: {fill_color}; border-radius: 3px; }}"
    )
    layout.addWidget(bar)

    return card


def set_auth_headline(label: QLabel, first_line: str, second_line: str) -> None:
    """The two-tone headline on every auth screen's fixed-dark left panel
    (e.g. "Track every session." / "Never miss a beat.") - white first
    line, accent-colored second line."""
    label.setTextFormat(Qt.RichText)
    label.setText(
        f'<span style="color:#FFFFFF;">{first_line}</span><br>'
        f'<span style="color:{PALETTE["accent"]};">{second_line}</span>'
    )


def make_tag_pill(text: str, color_key: str = "indigo") -> QWidget:
    """A small rounded pill: a colored dot + a label, tinted to match -
    e.g. a class's color tag or an "Archived" status flag."""
    entry = TAG_COLORS.get(color_key, TAG_COLORS["slate"])

    pill = QWidget()
    pill.setStyleSheet(
        f"background-color: {entry['tint']}; border-radius: {RADIUS['pill']}px;"
    )
    layout = QHBoxLayout(pill)
    layout.setContentsMargins(8, 3, 10, 3)
    layout.setSpacing(6)

    dot = QFrame()
    dot.setFixedSize(6, 6)
    dot.setStyleSheet(f"background-color: {entry['dot']}; border-radius: 3px; border: none;")
    layout.addWidget(dot, 0, Qt.AlignVCenter)

    label = QLabel(text)
    label.setStyleSheet(f"border: none; color: {entry['dot']}; font-size: 8.5pt; font-weight: 600;")
    layout.addWidget(label)

    return pill
