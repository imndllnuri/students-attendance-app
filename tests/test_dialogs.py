"""Covers shared/dialogs.py: ChoiceDialog (real-QDialog replacement for
QInputDialog.getItem) and DetailDialog (replacement for a QMessageBox with
an ActionRole button hijacked into it)."""

from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from shared.dialogs import ChoiceDialog, DetailDialog


def test_choice_dialog_get_item_returns_selection_on_accept(qtbot, monkeypatch):
    monkeypatch.setattr(QDialog, "exec_", lambda self: QDialog.Accepted)

    selected, ok = ChoiceDialog.get_item(None, "Pick", "Choose one:", ["A", "B", "C"], current_index=1)

    assert ok is True
    assert selected == "B"


def test_choice_dialog_get_item_reports_not_ok_on_cancel(qtbot, monkeypatch):
    monkeypatch.setattr(QDialog, "exec_", lambda self: QDialog.Rejected)

    selected, ok = ChoiceDialog.get_item(None, "Pick", "Choose one:", ["A", "B"])

    assert ok is False


def test_detail_dialog_exposes_title_and_body_text():
    dialog = DetailDialog(None, "Detail", "Some body text")

    assert dialog.windowTitle() == "Detail"
    assert dialog.text() == "Some body text"
    assert dialog.action_triggered is False


def test_detail_dialog_action_button_sets_triggered_and_accepts(qtbot):
    dialog = DetailDialog(None, "Detail", "Body", action_label="Export CSV")
    qtbot.addWidget(dialog)

    buttons = dialog.findChild(QDialogButtonBox)
    action_btn = next(b for b in buttons.buttons() if b.text() == "Export CSV")
    action_btn.click()

    assert dialog.action_triggered is True
    assert dialog.result() == QDialog.Accepted
