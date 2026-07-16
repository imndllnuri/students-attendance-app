"""Reusable QDialog-based replacements for the few call sites that had
outgrown QMessageBox/QInputDialog - injecting a QComboBox into a
QMessageBox's own layout, or attaching a non-standard ActionRole button to
one. Both patterns work, but the widgets they add live inside the message
box's internal layout rather than a real one, so they're awkward to keep
consistent with the rest of the app's dialog styling. These are real
QDialog subclasses instead, styled by the shared `QDialog` rules in
theme.qss like any other dialog.
"""

from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
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
