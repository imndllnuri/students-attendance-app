import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QWidget,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from resources.images import qrc
from services.api_client import ApiError
from shared.validation import (
    MIN_PASSWORD_LENGTH,
    SECURITY_QUESTIONS,
    is_valid_email,
    is_valid_password,
)
from views.add_new_class_window import AddNewClassWindow
from models.accounts import AccountManager
from models.classes import Class, ClassManager

MY_CLASSES_PAGE, SETTINGS_PAGE, SEARCH_PAGE, PROFILE_PAGE, STATISTICS_PAGE = range(5)


class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        uic.loadUi("ui/main_window.ui", self)
        self.gridLayout.setColumnStretch(0, 0)
        self.gridLayout.setColumnStretch(1, 1)

        self.user = user
        self.user_id = user.user_id
        self.class_manager = ClassManager()
        self.account_manager = AccountManager()
        self.statistics_canvas = None

        self.user_info_lbl.setText(f"{user.name} {user.surname}")

        self.profile_btn.clicked.connect(self.show_profile)
        self.my_classes_btn.clicked.connect(self.show_my_classes)
        self.settings_btn.clicked.connect(self.show_settings)
        self.statistics_btn.clicked.connect(self.show_statistics)
        self.log_out_btn.clicked.connect(self.confirm_logout)
        self.create_new_class_btn.clicked.connect(self.open_add_new_class_window)
        self.search_btn.clicked.connect(self.show_search)
        self.search_bar_le.returnPressed.connect(self.show_search)
        self.statistics_class_combo.currentIndexChanged.connect(self.render_statistics)

        self.edit_profile_btn.clicked.connect(self.enable_profile_edit)
        self.save_profile_btn.clicked.connect(self.save_profile)
        self.profile_email_le.textChanged.connect(self.validate_profile_email)

        self.settings_security_question_combo.addItems(SECURITY_QUESTIONS)
        self.change_password_btn.clicked.connect(self.change_password)
        self.update_security_question_btn.clicked.connect(self.update_security_question)
        self.delete_account_btn.clicked.connect(self.confirm_delete_account)
        self.settings_show_password_btn.toggled.connect(self._toggle_settings_password_echo)
        self.new_password_le.textChanged.connect(self.validate_new_password)
        self.confirm_new_password_le.textChanged.connect(self.validate_new_password_match)

        self._nav_buttons = (self.my_classes_btn, self.settings_btn, self.statistics_btn)
        self._setup_icons()
        self._apply_card_shadows()
        self._set_active_nav(self.my_classes_btn)

        self.load_classes()
        self.show()

    def _setup_icons(self):
        self.my_classes_btn.setIcon(qta.icon("fa5s.th-large", color="#94A3B8"))
        self.settings_btn.setIcon(qta.icon("fa5s.cog", color="#94A3B8"))
        self.statistics_btn.setIcon(qta.icon("fa5s.chart-bar", color="#94A3B8"))
        self.log_out_btn.setIcon(qta.icon("fa5s.sign-out-alt", color="#94A3B8"))
        for btn in (self.my_classes_btn, self.settings_btn, self.statistics_btn, self.log_out_btn):
            btn.setIconSize(QSize(16, 16))

        self.profile_btn.setIcon(qta.icon("fa5s.user-circle", color="#4F46E5"))
        self.search_btn.setIcon(qta.icon("fa5s.search", color="#4F46E5"))
        self.profile_btn.setIconSize(QSize(18, 18))
        self.search_btn.setIconSize(QSize(16, 16))

        self.create_new_class_btn.setIcon(qta.icon("fa5s.plus", color="white"))
        self.settings_show_password_btn.setIcon(qta.icon("fa5s.eye", color="#64748B"))
        self.settings_show_password_btn.setText("")
        self.settings_show_password_btn.setAccessibleName("Toggle password visibility")
        self.settings_show_password_btn.setToolTip("Show password")

    def _apply_card_shadows(self):
        for frame in (self.profile_card_frame, self.settings_card_frame):
            shadow = QGraphicsDropShadowEffect(frame)
            shadow.setBlurRadius(24)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(QColor(15, 23, 42, 40))
            frame.setGraphicsEffect(shadow)

    def _set_active_nav(self, active_btn):
        for btn in self._nav_buttons:
            btn.setProperty("active", btn is active_btn)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def show_profile(self):
        self.populate_profile_fields()
        self.stackedWidget.setCurrentIndex(PROFILE_PAGE)

    def show_my_classes(self):
        self._set_active_nav(self.my_classes_btn)
        self.stackedWidget.setCurrentIndex(MY_CLASSES_PAGE)
        self.load_classes()

    def show_settings(self):
        self._set_active_nav(self.settings_btn)
        self._clear_settings_form()
        self.stackedWidget.setCurrentIndex(SETTINGS_PAGE)

    def fetch_classes(self):
        try:
            return self.class_manager.load_classes_for_instructor(self.user_id)
        except ApiError as e:
            QMessageBox.critical(self, "Server Error", str(e))
            return []

    def load_classes(self):
        """Load class buttons into class_btns_layout"""
        while self.class_btns_layout.count():
            item = self.class_btns_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        classes = sorted(self.fetch_classes(), key=lambda c: c.class_code)
        for row, cls in enumerate(classes):
            self.class_btns_layout.addWidget(self._make_class_row_widget(cls), row, 0)

    def _make_class_row_widget(self, cls):
        class_widget = QWidget()
        class_layout = QHBoxLayout(class_widget)
        class_layout.setContentsMargins(0, 0, 0, 0)

        class_btn = QPushButton(f"{cls.class_name} ({cls.class_code})")
        class_btn.clicked.connect(lambda _, c=cls: self.open_class_window(c))

        delete_btn = QPushButton("X")
        delete_btn.setObjectName("class_delete_btn")
        delete_btn.setFixedSize(25, 25)
        delete_btn.clicked.connect(lambda _, c=cls: self.delete_class(c))

        class_layout.addWidget(class_btn)
        class_layout.addWidget(delete_btn)
        return class_widget

    def delete_class(self, cls):
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the class '{cls.class_code}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        if self.class_manager.delete_class(cls.class_id):
            self.load_classes()
            QMessageBox.information(self, "Success", f"Class '{cls.class_code}' has been deleted.")
        else:
            QMessageBox.critical(self, "Error", f"Could not delete {cls.class_code}.")

    def open_class_window(self, class_obj):
        existing_index = self.find_class_tab(class_obj.class_code)

        if existing_index is not None:
            self.stackedWidget.setCurrentIndex(existing_index)
        else:
            from views.class_window import ClassWindow

            class_page = ClassWindow(class_obj, self, self.class_manager)
            index = self.stackedWidget.addWidget(class_page)
            class_page.setProperty("class_code", class_obj.class_code)
            self.stackedWidget.setCurrentIndex(index)

    def find_class_tab(self, class_code):
        for i in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(i)
            if widget.property("class_code") == class_code:
                return i
        return None

    def open_add_new_class_window(self):
        self.add_new_class_window = AddNewClassWindow(user_id=self.user_id)
        self.add_new_class_window.class_created.connect(self.load_classes)
        self.add_new_class_window.show()

    def confirm_logout(self):
        reply = QMessageBox.question(self, 'Log Out', 'Are you sure you want to log out?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.logout()

    def logout(self):
        from views.login_window import LoginWindow
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    # --- Profile ---

    def _toggle_echo(self, line_edit, button, checked):
        line_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        button.setText("Hide" if checked else "Show")

    def _toggle_settings_password_echo(self, checked):
        echo_mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.new_password_le.setEchoMode(echo_mode)
        self.confirm_new_password_le.setEchoMode(echo_mode)
        self.current_password_le.setEchoMode(echo_mode)
        glyph = "fa5s.eye-slash" if checked else "fa5s.eye"
        self.settings_show_password_btn.setIcon(qta.icon(glyph, color="#64748B"))
        self.settings_show_password_btn.setToolTip("Hide password" if checked else "Show password")

    def _set_error(self, line_edit, label, message):
        label.setText(message)
        label.setProperty("error", True)
        label.setVisible(True)
        label.style().unpolish(label)
        label.style().polish(label)
        line_edit.setProperty("error", True)
        line_edit.style().unpolish(line_edit)
        line_edit.style().polish(line_edit)

    def _clear_error(self, line_edit, label):
        label.setVisible(False)
        line_edit.setProperty("error", False)
        line_edit.style().unpolish(line_edit)
        line_edit.style().polish(line_edit)

    def _make_initials_avatar(self, name, surname, size=96):
        initials = f"{name[:1]}{surname[:1]}".upper()
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(45, 82, 101))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(size // 3)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, initials)
        painter.end()
        return pixmap

    def populate_profile_fields(self):
        self.profile_name_le.setText(self.user.name)
        self.profile_surname_le.setText(self.user.surname)
        self.profile_email_le.setText(self.user.email)
        self.profile_avatar_lbl.setPixmap(
            self._make_initials_avatar(self.user.name, self.user.surname)
        )
        self._set_profile_editing(False)

    def _set_profile_editing(self, editing):
        for line_edit in (self.profile_name_le, self.profile_surname_le, self.profile_email_le):
            line_edit.setReadOnly(not editing)
        self.edit_profile_btn.setVisible(not editing)
        self.save_profile_btn.setVisible(editing)
        self._clear_error(self.profile_email_le, self.profile_email_error_lbl)

    def enable_profile_edit(self):
        self._set_profile_editing(True)

    def validate_profile_email(self):
        email = self.profile_email_le.text().strip()
        if email and not is_valid_email(email):
            self._set_error(self.profile_email_le, self.profile_email_error_lbl,
                             "Enter a valid email address.")
            return False
        self._clear_error(self.profile_email_le, self.profile_email_error_lbl)
        return True

    def save_profile(self):
        name = self.profile_name_le.text().strip()
        surname = self.profile_surname_le.text().strip()
        email = self.profile_email_le.text().strip()

        if not self.validate_profile_email():
            return
        if not name or not surname or not email:
            QMessageBox.warning(self, "Missing Information", "Please fill in all fields.")
            return

        data, error = self.account_manager.update_account(
            self.user_id, email=email, name=name, surname=surname
        )
        if data is None:
            QMessageBox.critical(self, "Update Failed", error)
            return

        self.user.name = data["name"]
        self.user.surname = data["surname"]
        self.user.email = data["email"]
        self.user_info_lbl.setText(f"{self.user.name} {self.user.surname}")
        self._set_profile_editing(False)
        QMessageBox.information(self, "Profile Updated", "Your profile has been updated successfully!")

    # --- Settings ---

    def _clear_settings_form(self):
        for line_edit in (
            self.current_password_le, self.new_password_le, self.confirm_new_password_le,
            self.settings_answer_le, self.settings_current_password_for_question_le,
        ):
            line_edit.clear()
        self._clear_error(self.new_password_le, self.new_password_error_lbl)
        self._clear_error(self.confirm_new_password_le, self.confirm_new_password_error_lbl)
        self._clear_error(self.settings_answer_le, self.security_question_error_lbl)
        self.settings_security_question_combo.setCurrentIndex(0)

    def validate_new_password(self):
        password = self.new_password_le.text()
        if password and not is_valid_password(password):
            self._set_error(
                self.new_password_le,
                self.new_password_error_lbl,
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters "
                "and include both letters and numbers.",
            )
            self.validate_new_password_match()
            return False
        self._clear_error(self.new_password_le, self.new_password_error_lbl)
        self.validate_new_password_match()
        return True

    def validate_new_password_match(self):
        if (self.confirm_new_password_le.text()
                and self.confirm_new_password_le.text() != self.new_password_le.text()):
            self._set_error(self.confirm_new_password_le, self.confirm_new_password_error_lbl,
                             "Passwords do not match.")
            return False
        self._clear_error(self.confirm_new_password_le, self.confirm_new_password_error_lbl)
        return True

    def change_password(self):
        current = self.current_password_le.text()
        new = self.new_password_le.text()

        if not current:
            QMessageBox.warning(self, "Missing Information", "Please enter your current password.")
            return
        if not new:
            QMessageBox.warning(self, "Missing Information", "Please enter a new password.")
            return
        if not (self.validate_new_password() and self.validate_new_password_match()):
            return

        success, error = self.account_manager.change_password(self.user_id, current, new)
        if not success:
            QMessageBox.critical(self, "Change Password Failed", error)
            return

        self._clear_settings_form()
        QMessageBox.information(self, "Password Changed", "Your password has been changed successfully!")

    def update_security_question(self):
        current_password = self.settings_current_password_for_question_le.text()
        question = self.settings_security_question_combo.currentText()
        answer = self.settings_answer_le.text().strip()

        if not current_password:
            QMessageBox.warning(self, "Missing Information",
                                 "Please enter your current password to confirm.")
            return
        if not answer:
            self._set_error(self.settings_answer_le, self.security_question_error_lbl,
                             "Please provide an answer.")
            return
        self._clear_error(self.settings_answer_le, self.security_question_error_lbl)

        success, error = self.account_manager.update_security_question(
            self.user_id, current_password, question, answer
        )
        if not success:
            QMessageBox.critical(self, "Update Failed", error)
            return

        self._clear_settings_form()
        QMessageBox.information(self, "Security Question Updated",
                                 "Your security question has been updated.")

    def confirm_delete_account(self):
        reply = QMessageBox.question(
            self, "Delete Account",
            "Are you sure you want to permanently delete your account? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        success, error = self.account_manager.delete_account(self.user_id)
        if not success:
            QMessageBox.critical(self, "Delete Account Failed", error)
            return

        QMessageBox.information(self, "Account Deleted", "Your account has been deleted.")
        self.logout()

    # --- Search ---

    def show_search(self):
        self.stackedWidget.setCurrentIndex(SEARCH_PAGE)
        while self.search_results_layout.count():
            item = self.search_results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        query = self.search_bar_le.text().strip().lower()
        classes = self.fetch_classes()
        matches = [
            c for c in classes
            if query in c.class_name.lower() or query in c.class_code.lower()
        ] if query else classes

        if not matches:
            self.search_status_lbl.setText("No matching classes found.")
        else:
            self.search_status_lbl.setText(f"{len(matches)} class(es) found:")
            for row, cls in enumerate(sorted(matches, key=lambda c: c.class_code)):
                self.search_results_layout.addWidget(self._make_class_row_widget(cls), row, 0)

    # --- Statistics ---

    def show_statistics(self):
        self._set_active_nav(self.statistics_btn)
        self.stackedWidget.setCurrentIndex(STATISTICS_PAGE)
        self.statistics_class_combo.blockSignals(True)
        self.statistics_class_combo.clear()
        for cls in self.fetch_classes():
            self.statistics_class_combo.addItem(f"{cls.class_name} ({cls.class_code})", cls)
        self.statistics_class_combo.blockSignals(False)
        self.render_statistics()

    def render_statistics(self):
        if self.statistics_canvas is not None:
            self.statistics_chart_layout.removeWidget(self.statistics_canvas)
            self.statistics_canvas.deleteLater()
            self.statistics_canvas = None

        cls = self.statistics_class_combo.currentData()
        if cls is None:
            return

        try:
            stats = self.class_manager.get_statistics(cls.class_id)
        except ApiError as e:
            QMessageBox.critical(self, "Server Error", str(e))
            return

        figure = Figure(figsize=(4, 4))
        axes = figure.add_subplot(111)
        labels = ["Present", "Late", "Absent"]
        values = [stats["present"], stats["late"], stats["absent"]]
        if sum(values) == 0:
            axes.text(0.5, 0.5, "No attendance recorded yet", ha="center", va="center")
            axes.axis("off")
        else:
            axes.pie(values, labels=labels, autopct="%1.1f%%",
                     colors=["#90ee90", "#ffdf80", "#ff9696"])
            axes.set_title(f"Attendance for {cls.class_code}")

        self.statistics_canvas = FigureCanvasQTAgg(figure)
        self.statistics_chart_layout.addWidget(self.statistics_canvas)
