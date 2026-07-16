"""Covers the reusable widget builders in shared/widgets.py: stat cards
with a progress bar, and tag pills."""

from PyQt5.QtWidgets import QLabel, QProgressBar

from shared.widgets import make_stat_card, make_tag_pill


def test_stat_card_shows_label_and_value(qtbot):
    card = make_stat_card("Attendance Rate", "82%", 82)
    qtbot.addWidget(card)

    labels = card.findChildren(QLabel)
    assert any(lbl.text() == "Attendance Rate" for lbl in labels)
    assert any(lbl.text() == "82%" for lbl in labels)


def test_stat_card_progress_bar_value_is_clamped(qtbot):
    over = make_stat_card("Over", "150", 150)
    under = make_stat_card("Under", "-10", -10)
    qtbot.addWidget(over)
    qtbot.addWidget(under)

    assert over.findChild(QProgressBar).value() == 100
    assert under.findChild(QProgressBar).value() == 0


def test_stat_card_uses_custom_fill_color(qtbot):
    card = make_stat_card("Late", "5", 20, fill_color="#DC2626")
    qtbot.addWidget(card)

    bar = card.findChild(QProgressBar)
    assert "#DC2626" in bar.styleSheet()


def test_tag_pill_shows_label_text(qtbot):
    pill = make_tag_pill("COMP101", color_key="sky")
    qtbot.addWidget(pill)

    label = pill.findChild(QLabel)
    assert label.text() == "COMP101"


def test_tag_pill_falls_back_to_slate_for_unknown_color_key(qtbot):
    from shared.palette import TAG_COLORS

    pill = make_tag_pill("Archived", color_key="not-a-real-color")
    qtbot.addWidget(pill)

    label = pill.findChild(QLabel)
    assert TAG_COLORS["slate"]["dot"] in label.styleSheet()
