from datetime import datetime

import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtCore import QEvent, Qt, QSize, QTimer
from PyQt5.QtGui import QColor, QFont, QKeySequence, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QShortcut,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from resources.images import qrc
from services.api_client import ApiError
from shared.palette import PALETTE, class_tag_color
from shared.validation import (
    MIN_PASSWORD_LENGTH,
    SECURITY_QUESTIONS,
    is_valid_email,
    is_valid_password,
    password_strength,
)
from views.add_new_class_window import AddNewClassWindow
from models.accounts import AccountManager
from models.classes import Class, ClassManager

MY_CLASSES_PAGE, SETTINGS_PAGE, SEARCH_PAGE, PROFILE_PAGE, STATISTICS_PAGE = range(5)

SESSION_TIMEOUT_MINUTES = 15
_ACTIVITY_EVENTS = (QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.KeyPress, QEvent.Wheel)

_WEEKDAY_ORDER = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6,
}


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
        self.class_sort_combo.currentIndexChanged.connect(self.load_classes)
        self.show_archived_cb.toggled.connect(self.load_classes)

        self.edit_profile_btn.clicked.connect(self.enable_profile_edit)
        self.save_profile_btn.clicked.connect(self.save_profile)
        self.profile_email_le.textChanged.connect(self.validate_profile_email)

        self.settings_security_question_combo.addItems(SECURITY_QUESTIONS)
        self.change_password_btn.clicked.connect(self.change_password)
        self.update_security_question_btn.clicked.connect(self.update_security_question)
        self.delete_account_btn.clicked.connect(self.confirm_delete_account)
        self.settings_show_password_btn.toggled.connect(self._toggle_settings_password_echo)
        self.new_password_le.textChanged.connect(self.validate_new_password)
        self.new_password_le.textChanged.connect(self._update_settings_password_strength)
        self.confirm_new_password_le.textChanged.connect(self.validate_new_password_match)

        self._nav_buttons = (self.my_classes_btn, self.settings_btn, self.statistics_btn)
        self._setup_icons()
        self._apply_card_shadows()
        self._set_active_nav(self.my_classes_btn)
        self._setup_shortcuts()
        self._setup_session_timeout()

        self.load_classes()
        self.show()

    # --- Session timeout ---

    def _setup_session_timeout(self):
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setSingleShot(True)
        self._inactivity_timer.timeout.connect(self._handle_session_timeout)
        QApplication.instance().installEventFilter(self)
        self._reset_inactivity_timer()

    def eventFilter(self, obj, event):
        if event.type() in _ACTIVITY_EVENTS:
            self._reset_inactivity_timer()
        return super().eventFilter(obj, event)

    def _reset_inactivity_timer(self):
        self._inactivity_timer.start(SESSION_TIMEOUT_MINUTES * 60 * 1000)

    def _handle_session_timeout(self):
        QApplication.instance().removeEventFilter(self)
        QMessageBox.information(
            self,
            "Session Expired",
            f"You've been logged out after {SESSION_TIMEOUT_MINUTES} minutes of inactivity.",
        )
        self.logout()

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

        self.my_classes_btn.setToolTip("My Classes (Ctrl+1)")
        self.settings_btn.setToolTip("Settings (Ctrl+2)")
        self.statistics_btn.setToolTip("Statistics (Ctrl+3)")
        self.search_btn.setToolTip("Search (Ctrl+F)")
        self.create_new_class_btn.setToolTip("Create New Class (Ctrl+N)")
        self.create_new_class_btn.setIcon(qta.icon("fa5s.plus", color="white"))
        self.settings_show_password_btn.setIcon(qta.icon("fa5s.eye", color="#64748B"))
        self.settings_show_password_btn.setText("")
        self.settings_show_password_btn.setAccessibleName("Toggle password visibility")
        self.settings_show_password_btn.setToolTip("Show password")

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+N"), self, self.open_add_new_class_window)
        QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)
        QShortcut(QKeySequence("Ctrl+1"), self, self.show_my_classes)
        QShortcut(QKeySequence("Ctrl+2"), self, self.show_settings)
        QShortcut(QKeySequence("Ctrl+3"), self, self.show_statistics)

    def _focus_search(self):
        self.show_search()
        self.search_bar_le.setFocus()
        self.search_bar_le.selectAll()

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
        showing_archived = self.show_archived_cb.isChecked()
        try:
            classes = self.class_manager.load_classes_for_instructor(
                self.user_id, include_archived=showing_archived
            )
        except ApiError as e:
            QMessageBox.critical(self, "Server Error", str(e))
            return []
        if showing_archived:
            return [cls for cls in classes if cls.archived]
        return classes

    def _class_sort_key(self, cls):
        mode = self.class_sort_combo.currentText()
        if mode == "Class Name":
            return (cls.class_name.lower(), cls.class_code.lower())
        if mode == "Day":
            days = [_WEEKDAY_ORDER.get(day, 99) for day, slots in cls.schedule.items() if slots]
            return (min(days) if days else 99, cls.class_code.lower())
        return (cls.class_code.lower(),)

    def load_classes(self):
        """Load class buttons into class_btns_layout"""
        while self.class_btns_layout.count():
            item = self.class_btns_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        showing_archived = self.show_archived_cb.isChecked()
        self.create_new_class_btn.setVisible(not showing_archived)

        classes = sorted(self.fetch_classes(), key=self._class_sort_key)
        self.empty_state_lbl.setText(
            "No archived classes." if showing_archived
            else "You haven't created any classes yet. Use \"Create New Class\" below to get started."
        )
        self.empty_state_lbl.setVisible(not classes)
        row_builder = self._make_archived_class_row_widget if showing_archived else self._make_class_row_widget
        for row, cls in enumerate(classes):
            self.class_btns_layout.addWidget(row_builder(cls), row, 0)

        self.today_classes_title_lbl.setVisible(not showing_archived)
        if showing_archived:
            self._populate_today_classes([])
            self.no_classes_today_lbl.setVisible(False)
        else:
            self._populate_today_classes(classes)

    def _classes_scheduled_today(self, classes):
        today = datetime.now().strftime("%A")
        return [
            cls for cls in classes
            if any(slot.selected for slot in cls.schedule.get(today, []))
        ]

    def _populate_today_classes(self, classes):
        while self.today_classes_layout.count():
            item = self.today_classes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        todays_classes = self._classes_scheduled_today(classes)
        self.no_classes_today_lbl.setVisible(not todays_classes)
        for cls in todays_classes:
            self.today_classes_layout.addWidget(self._make_today_class_row_widget(cls))

    def _make_today_class_row_widget(self, cls):
        row = QWidget()
        row.setObjectName("today_class_row_widget")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(4, 4, 4, 4)

        label = QLabel(f"{cls.class_name} ({cls.class_code})")
        layout.addWidget(label, 1)

        take_attendance_btn = QPushButton("Take Attendance")
        take_attendance_btn.setCursor(Qt.PointingHandCursor)
        take_attendance_btn.clicked.connect(lambda _, c=cls: self.open_take_attendance_for(c))
        layout.addWidget(take_attendance_btn)

        return row

    def _make_class_row_widget(self, cls):
        class_widget = QWidget()
        class_widget.setObjectName("class_row_widget")
        row_layout = QHBoxLayout(class_widget)
        row_layout.setContentsMargins(4, 4, 4, 4)

        color_chip = QFrame()
        color_chip.setFixedWidth(4)
        color_chip.setMinimumHeight(40)
        color_chip.setStyleSheet(
            f"background-color: {class_tag_color(cls.class_code)}; border-radius: 2px;"
        )
        row_layout.addWidget(color_chip)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)

        class_btn = QPushButton(f"{cls.class_name} ({cls.class_code})")
        class_btn.setObjectName("class_row_name_btn")
        class_btn.setCursor(Qt.PointingHandCursor)
        class_btn.clicked.connect(lambda _, c=cls: self.open_class_window(c))

        caption_lbl = QLabel(f"Section {cls.section}")
        caption_lbl.setObjectName("class_row_caption_lbl")

        text_layout.addWidget(class_btn)
        text_layout.addWidget(caption_lbl)

        duplicate_btn = QPushButton("Duplicate")
        duplicate_btn.setCursor(Qt.PointingHandCursor)
        duplicate_btn.setToolTip("Create a new class with the same schedule and policy")
        duplicate_btn.clicked.connect(lambda _, c=cls: self.open_duplicate_class_window(c))

        archive_btn = QPushButton("X")
        archive_btn.setObjectName("class_delete_btn")
        archive_btn.setFixedSize(25, 25)
        archive_btn.setCursor(Qt.PointingHandCursor)
        archive_btn.setToolTip("Archive class")
        archive_btn.clicked.connect(lambda _, c=cls: self.archive_class(c))

        row_layout.addLayout(text_layout, 1)
        row_layout.addWidget(duplicate_btn)
        row_layout.addWidget(archive_btn)
        return class_widget

    def open_duplicate_class_window(self, cls):
        self.duplicate_class_window = AddNewClassWindow(user_id=self.user_id, duplicate_from=cls)
        self.duplicate_class_window.class_created.connect(self.load_classes)
        self.duplicate_class_window.show()

    def _make_archived_class_row_widget(self, cls):
        class_widget = QWidget()
        class_widget.setObjectName("class_row_widget")
        row_layout = QHBoxLayout(class_widget)
        row_layout.setContentsMargins(4, 4, 4, 4)

        label = QLabel(f"{cls.class_name} ({cls.class_code})")
        row_layout.addWidget(label, 1)

        unarchive_btn = QPushButton("Unarchive")
        unarchive_btn.setCursor(Qt.PointingHandCursor)
        unarchive_btn.clicked.connect(lambda _, c=cls: self.unarchive_class(c))
        row_layout.addWidget(unarchive_btn)

        delete_btn = QPushButton("Delete Permanently")
        delete_btn.setObjectName("class_delete_btn")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(lambda _, c=cls: self.permanently_delete_class(c))
        row_layout.addWidget(delete_btn)

        return class_widget

    def archive_class(self, cls):
        reply = QMessageBox.question(
            self,
            "Archive Class",
            f"Archive '{cls.class_code}'? It will be hidden from My Classes but its data "
            "is kept - you can restore it later from Show Archived.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        if self.class_manager.archive_class(cls.class_id):
            self.load_classes()
        else:
            QMessageBox.critical(self, "Error", f"Could not archive {cls.class_code}.")

    def unarchive_class(self, cls):
        if self.class_manager.unarchive_class(cls.class_id):
            self.load_classes()
        else:
            QMessageBox.critical(self, "Error", f"Could not unarchive {cls.class_code}.")

    def permanently_delete_class(self, cls):
        reply = QMessageBox.question(
            self,
            "Confirm Permanent Deletion",
            f"Permanently delete '{cls.class_code}'? This cannot be undone.",
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
            return self.stackedWidget.widget(existing_index)

        from views.class_window import ClassWindow

        class_page = ClassWindow(class_obj, self, self.class_manager)
        index = self.stackedWidget.addWidget(class_page)
        class_page.setProperty("class_code", class_obj.class_code)
        self.stackedWidget.setCurrentIndex(index)
        return class_page

    def open_take_attendance_for(self, cls):
        class_page = self.open_class_window(cls)
        class_page.attendance_page_show()

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
        self._inactivity_timer.stop()
        QApplication.instance().removeEventFilter(self)
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
        self._populate_recent_logins()

    def _populate_recent_logins(self):
        timestamps = self.account_manager.get_login_history(self.user_id, limit=5)
        if not timestamps:
            self.recent_logins_lbl.setText("No login history yet.")
            return
        lines = []
        for raw in timestamps:
            try:
                dt = datetime.fromisoformat(raw).astimezone()
                lines.append(dt.strftime("%b %d, %Y %H:%M"))
            except ValueError:
                lines.append(raw)
        self.recent_logins_lbl.setText("\n".join(lines))

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
        self._update_settings_password_strength()

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

    def _update_settings_password_strength(self):
        strength = password_strength(self.new_password_le.text())
        self.settings_password_strength_lbl.setText(strength.capitalize() if strength else "")
        self.settings_password_strength_lbl.setProperty("strength", strength)
        self.settings_password_strength_lbl.style().unpolish(self.settings_password_strength_lbl)
        self.settings_password_strength_lbl.style().polish(self.settings_password_strength_lbl)

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
        matches = [c for c in classes if self._class_matches_query(c, query)] if query else classes

        if not matches:
            self.search_status_lbl.setText("No matching classes found.")
        else:
            self.search_status_lbl.setText(f"{len(matches)} class(es) found:")
            for row, cls in enumerate(sorted(matches, key=self._class_sort_key)):
                self.search_results_layout.addWidget(self._make_class_row_widget(cls), row, 0)

    def _class_matches_query(self, cls, query):
        if query in cls.class_name.lower() or query in cls.class_code.lower():
            return True
        try:
            roster = self.class_manager.get_roster(cls.class_id)
        except ApiError:
            return False
        return any(query in student["name_surname"].lower() for student in roster)

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
            self.statistics_empty_lbl.setText("Select a class to view its statistics.")
            self.statistics_empty_lbl.setVisible(True)
            return

        try:
            stats = self.class_manager.get_statistics(cls.class_id)
        except ApiError as e:
            QMessageBox.critical(self, "Server Error", str(e))
            return

        figure = Figure(figsize=(8, 4))
        figure.patch.set_facecolor(PALETTE["bg_card"])
        axes_pie = figure.add_subplot(121)
        axes_trend = figure.add_subplot(122)
        labels = ["Present", "Late", "Absent"]
        values = [stats["present"], stats["late"], stats["absent"]]
        if sum(values) == 0:
            self.statistics_empty_lbl.setText("No attendance recorded yet for this class.")
            self.statistics_empty_lbl.setVisible(True)
            axes_pie.axis("off")
            axes_trend.axis("off")
        else:
            self.statistics_empty_lbl.setVisible(False)
            axes_pie.pie(
                values,
                labels=labels,
                autopct="%1.1f%%",
                colors=[PALETTE["success"], PALETTE["warning"], PALETTE["error"]],
                textprops={"color": PALETTE["text_primary"]},
            )
            axes_pie.set_title(f"Attendance for {cls.class_code}", color=PALETTE["text_primary"])
            self._render_attendance_trend(axes_trend, cls)

        self.statistics_canvas = FigureCanvasQTAgg(figure)
        self.statistics_chart_layout.addWidget(self.statistics_canvas)

    def _render_attendance_trend(self, axes, cls):
        """Plots the per-session attendance rate (% Present+Late) over
        time, reusing the same pivoted student table the roster page
        already fetches rather than adding a parallel server aggregate."""
        try:
            table = self.class_manager.get_student_table(cls.class_id)
        except ApiError:
            axes.axis("off")
            return

        fixed_columns = {"Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours"}
        session_columns = [c for c in table["columns"] if c not in fixed_columns]
        num_students = len(table["rows"])

        if not session_columns or num_students == 0:
            axes.axis("off")
            return

        rates = []
        for col in session_columns:
            col_index = table["columns"].index(col)
            recorded = sum(1 for row in table["rows"] if str(row[col_index]).startswith("1 "))
            rates.append(recorded / num_students * 100)

        axes.plot(range(1, len(rates) + 1), rates, marker="o", color=PALETTE["accent"])
        axes.set_ylim(0, 100)
        axes.set_xlabel("Session", color=PALETTE["text_primary"])
        axes.set_ylabel("Attendance Rate (%)", color=PALETTE["text_primary"])
        axes.set_title("Attendance Trend", color=PALETTE["text_primary"])
        axes.tick_params(colors=PALETTE["text_primary"])
