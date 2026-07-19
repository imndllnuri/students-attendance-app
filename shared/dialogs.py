"""Reusable QDialog-based replacements for the few call sites that had
outgrown QMessageBox/QInputDialog - injecting a QComboBox into a
QMessageBox's own layout, or attaching a non-standard ActionRole button to
one. Both patterns work, but the widgets they add live inside the message
box's internal layout rather than a real one, so they're awkward to keep
consistent with the rest of the app's dialog styling. These are real
QDialog subclasses instead, styled by the shared `QDialog` rules in
theme.qss like any other dialog.
"""

import qtawesome as qta
import requests
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class ChoiceDialog(QDialog):
    """A single prompt + dropdown + OK/Cancel. Drop-in replacement for
    QInputDialog.getItem() wherever the picked item feeds into logic that
    needs a real Cancel path (register_card previously had none at all)."""

    def __init__(self, parent, title, message, choices, current_index=0):
        super().__init__(parent)
        self.setWindowTitle(title)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(message))

        self.combo = QComboBox()
        self.combo.addItems(choices)
        self.combo.setCurrentIndex(current_index)
        layout.addWidget(self.combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_text(self):
        return self.combo.currentText()

    @staticmethod
    def get_item(parent, title, message, choices, current_index=0):
        """Same (text, ok) return shape as QInputDialog.getItem(parent,
        title, message, choices, current_index, False) so callers only
        need to swap the import and call."""
        dialog = ChoiceDialog(parent, title, message, choices, current_index)
        ok = dialog.exec_() == QDialog.Accepted
        return dialog.selected_text(), ok


class DetailDialog(QDialog):
    """A read-only text body with a Close button and an optional extra
    action button (e.g. "Export CSV"). Replaces
    QMessageBox.addButton(label, QMessageBox.ActionRole), which works but
    treats an alert box as a general-purpose dialog."""

    def __init__(self, parent, title, text, action_label=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.action_triggered = False

        layout = QVBoxLayout(self)
        self._body = QLabel(text)
        self._body.setWordWrap(True)
        layout.addWidget(self._body)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        if action_label:
            action_btn = buttons.addButton(action_label, QDialogButtonBox.ActionRole)
            action_btn.clicked.connect(self._trigger_action)
        layout.addWidget(buttons)

    def text(self):
        return self._body.text()

    def _trigger_action(self):
        self.action_triggered = True
        self.accept()


class ServerConnectionDialog(QDialog):
    """Lets the user point the app at a TapIn server (base URL + API key)
    and verify the connection before saving - see DEPLOYMENT.md / the
    Server Connection card in Settings and the gear icon on the login
    screen, which are the two callers of this dialog."""

    def __init__(self, parent, current_base_url="", current_api_key=""):
        super().__init__(parent)
        self.setWindowTitle("Server Connection")

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.base_url_le = QLineEdit(current_base_url)
        self.base_url_le.setPlaceholderText("http://192.168.1.42:5000")
        form.addRow("Server URL", self.base_url_le)

        self.api_key_le = QLineEdit(current_api_key)
        self.api_key_le.setEchoMode(QLineEdit.Password)
        api_key_toggle = self.api_key_le.addAction(
            qta.icon("fa5s.eye", color="#6B6B76"), QLineEdit.TrailingPosition
        )
        api_key_toggle.setCheckable(True)
        api_key_toggle.setToolTip("Show API key")
        api_key_toggle.toggled.connect(
            lambda checked: self.api_key_le.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        form.addRow("API Key", self.api_key_le)
        layout.addLayout(form)

        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        layout.addWidget(self.status_lbl)

        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.clicked.connect(self.test_connection)
        layout.addWidget(self.test_connection_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def test_connection(self):
        # Deliberately bypasses shared.backend_config.create_client(): the
        # whole point is probing the *unsaved* field values, which
        # create_client() has no way to see since it always reads the
        # persisted config file.
        from services.api_client import ApiClient, ApiError

        client = ApiClient(base_url=self.base_url_le.text().strip(), api_key=self.api_key_le.text())
        try:
            client.check_health()
        except (ApiError, requests.exceptions.RequestException) as e:
            self.status_lbl.setText(f"Couldn't connect: {e}")
            return
        self.status_lbl.setText("Connected.")

    def base_url(self):
        return self.base_url_le.text().strip()

    def api_key(self):
        return self.api_key_le.text()
