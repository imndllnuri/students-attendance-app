"""Covers shared/dialogs.py: ChoiceDialog (real-QDialog replacement for
QInputDialog.getItem), DetailDialog (replacement for a QMessageBox with
an ActionRole button hijacked into it), and ServerConnectionDialog (lets
the user point the app at a TapIn server and test the connection)."""

from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from services.api_client import ApiError
from shared.dialogs import ChoiceDialog, DetailDialog, ServerConnectionDialog


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


def test_server_connection_dialog_prefills_current_values(qtbot):
    dialog = ServerConnectionDialog(None, "http://192.168.1.42:5000", "secret-token")
    qtbot.addWidget(dialog)

    assert dialog.base_url() == "http://192.168.1.42:5000"
    assert dialog.api_key() == "secret-token"


def test_server_connection_dialog_test_connection_success(qtbot, monkeypatch):
    from services.api_client import ApiClient

    monkeypatch.setattr(ApiClient, "check_health", lambda self: {"status": "ok"})

    dialog = ServerConnectionDialog(None)
    qtbot.addWidget(dialog)
    dialog.base_url_le.setText("http://192.168.1.42:5000")
    dialog.api_key_le.setText("secret-token")

    dialog.test_connection()

    assert dialog.status_lbl.text() == "Connected."


def test_server_connection_dialog_test_connection_failure(qtbot, monkeypatch):
    from services.api_client import ApiClient

    def raise_api_error(self):
        raise ApiError("Unauthorized", status_code=401)

    monkeypatch.setattr(ApiClient, "check_health", raise_api_error)

    dialog = ServerConnectionDialog(None)
    qtbot.addWidget(dialog)
    dialog.base_url_le.setText("http://192.168.1.42:5000")
    dialog.api_key_le.setText("wrong-token")

    dialog.test_connection()

    assert "Unauthorized" in dialog.status_lbl.text()


def test_server_connection_dialog_ok_returns_entered_values(qtbot, monkeypatch):
    monkeypatch.setattr(QDialog, "exec_", lambda self: QDialog.Accepted)

    dialog = ServerConnectionDialog(None)
    qtbot.addWidget(dialog)
    dialog.base_url_le.setText(" http://192.168.1.42:5000 ")
    dialog.api_key_le.setText("secret-token")

    assert dialog.exec_() == QDialog.Accepted
    assert dialog.base_url() == "http://192.168.1.42:5000"
    assert dialog.api_key() == "secret-token"
