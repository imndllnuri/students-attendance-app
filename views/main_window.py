import csv
import json
from datetime import datetime

import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtCore import QEvent, Qt, QSize, QTimer
from PyQt5.QtGui import QColor, QFont, QKeySequence, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMainWindow,
    QMenu,
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
from shared.class_order import load_class_order, save_class_order
from shared.i18n import LANGUAGES, load_language_preference, save_language_preference, t
from shared.list_density import load_list_density, save_list_density
from shared.palette import PALETTE, class_tag_color
from shared.session_timeout import (
    TIMEOUT_OPTIONS,
    load_session_timeout_minutes,
    save_session_timeout_minutes,
)
from shared.theme import load_theme_preference, save_theme_preference, stylesheet_path
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
        self.notifications = []
        self.recently_viewed_class_ids = []

        self.user_info_lbl.setText(f"{user.name} {user.surname}")

        self.profile_btn.clicked.connect(self.show_profile)
        self.my_classes_btn.clicked.connect(self.show_my_classes)
        self.settings_btn.clicked.connect(self.show_settings)
        self.statistics_btn.clicked.connect(self.show_statistics)
        self.log_out_btn.clicked.connect(self.confirm_logout)
        self.create_new_class_btn.clicked.connect(self.open_add_new_class_window)
        self.search_btn.clicked.connect(self.show_search)
        self.search_bar_le.returnPressed.connect(self.show_search)
        self.notifications_btn.clicked.connect(self.show_notifications_menu)
        self.statistics_class_combo.currentIndexChanged.connect(self.render_statistics)
        self.export_chart_btn.clicked.connect(self.export_statistics_chart)
        self.class_sort_combo.currentIndexChanged.connect(self.load_classes)
        self.show_archived_cb.toggled.connect(self.load_classes)
        self.compact_view_cb.blockSignals(True)
        self.compact_view_cb.setChecked(load_list_density() == "compact")
        self.compact_view_cb.blockSignals(False)
        self.compact_view_cb.toggled.connect(self.toggle_list_density)
        self.export_class_list_btn.clicked.connect(self.export_class_list)
        self.custom_order_listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.custom_order_listWidget.model().rowsMoved.connect(self._save_custom_order)

        self.edit_profile_btn.clicked.connect(self.enable_profile_edit)
        self.save_profile_btn.clicked.connect(self.save_profile)
        self.export_account_data_btn.clicked.connect(self.export_account_data)
        self.profile_email_le.textChanged.connect(self.validate_profile_email)

        self.dark_mode_cb.blockSignals(True)
        self.dark_mode_cb.setChecked(load_theme_preference() == "dark")
        self.dark_mode_cb.blockSignals(False)
        self.dark_mode_cb.toggled.connect(self.toggle_dark_mode)

        self._apply_translations()
        self._setup_language_combo()

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
        self._setup_session_timeout_combo()

        self.load_classes()
        self.show()

    # --- Session timeout ---

    def _setup_session_timeout(self):
        self.session_timeout_minutes = load_session_timeout_minutes()
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
        if self.session_timeout_minutes <= 0:
            self._inactivity_timer.stop()
            return
        self._inactivity_timer.start(self.session_timeout_minutes * 60 * 1000)

    def _handle_session_timeout(self):
        QApplication.instance().removeEventFilter(self)
        QMessageBox.information(
            self,
            "Session Expired",
            f"You've been logged out after {self.session_timeout_minutes} minutes of inactivity.",
        )
        self.logout()

    def change_session_timeout(self):
        minutes = self.session_timeout_combo.currentData()
        self.session_timeout_minutes = minutes
        save_session_timeout_minutes(minutes)
        self._reset_inactivity_timer()

    def _setup_session_timeout_combo(self):
        labels = {5: "5 minutes", 15: "15 minutes", 30: "30 minutes", 0: "Never"}
        self.session_timeout_combo.blockSignals(True)
        self.session_timeout_combo.clear()
        for minutes in TIMEOUT_OPTIONS:
            self.session_timeout_combo.addItem(labels[minutes], minutes)
        self.session_timeout_combo.setCurrentIndex(TIMEOUT_OPTIONS.index(self.session_timeout_minutes))
        self.session_timeout_combo.blockSignals(False)
        self.session_timeout_combo.currentIndexChanged.connect(self.change_session_timeout)

    def _setup_icons(self):
        self.my_classes_btn.setIcon(qta.icon("fa5s.th-large", color="#94A3B8"))
        self.settings_btn.setIcon(qta.icon("fa5s.cog", color="#94A3B8"))
        self.statistics_btn.setIcon(qta.icon("fa5s.chart-bar", color="#94A3B8"))
        self.log_out_btn.setIcon(qta.icon("fa5s.sign-out-alt", color="#94A3B8"))
        for btn in (self.my_classes_btn, self.settings_btn, self.statistics_btn, self.log_out_btn):
            btn.setIconSize(QSize(16, 16))

        self.profile_btn.setIcon(qta.icon("fa5s.user-circle", color="#4F46E5"))
        self.search_btn.setIcon(qta.icon("fa5s.search", color="#4F46E5"))
        self.notifications_btn.setIcon(qta.icon("fa5s.bell", color="#4F46E5"))
        self.profile_btn.setIconSize(QSize(18, 18))
        self.search_btn.setIconSize(QSize(16, 16))
        self.notifications_btn.setIconSize(QSize(16, 16))

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
        QShortcut(QKeySequence("Ctrl+K"), self, self.jump_to_class)

    def _focus_search(self):
        self.show_search()
        self.search_bar_le.setFocus()
        self.search_bar_le.selectAll()

    def jump_to_class(self):
        """Ctrl+K command palette: type or pick a class by name/code and
        jump straight to its detail page."""
        classes = self.fetch_classes()
        if not classes:
            QMessageBox.information(self, "No Classes", "You have no classes to jump to.")
            return

        labels = [f"{c.class_name} ({c.class_code})" for c in classes]
        selected_label, ok = QInputDialog.getItem(
            self, "Jump to Class", "Type or select a class:", labels, 0, True
        )
        if not ok or selected_label not in labels:
            return

        cls = classes[labels.index(selected_label)]
        self.show_my_classes()
        self.open_class_window(cls)

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
        pin_key = 0 if cls.pinned else 1
        mode = self.class_sort_combo.currentText()
        if mode == "Class Name":
            return (pin_key, cls.class_name.lower(), cls.class_code.lower())
        if mode == "Day":
            days = [_WEEKDAY_ORDER.get(day, 99) for day, slots in cls.schedule.items() if slots]
            return (pin_key, min(days) if days else 99, cls.class_code.lower())
        return (pin_key, cls.class_code.lower())

    def _format_schedule_for_export(self, schedule):
        parts = []
        for day, slots in schedule.items():
            times = [f"{s.start_time.toString('HH:mm')}-{s.end_time.toString('HH:mm')}" for s in slots if s.selected]
            if times:
                parts.append(f"{day}: {', '.join(times)}")
        return "; ".join(parts)

    def export_class_list(self):
        classes = self.fetch_classes()
        if not classes:
            QMessageBox.information(self, "Nothing to Export", "No classes to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Class List", "classes.csv", "CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Class Code", "Class Name", "Section", "Attendance Policy (%)",
                    "Late Threshold (min)", "Weeks", "Total Hours", "Weekly Hours", "Schedule",
                ])
                for cls in classes:
                    writer.writerow([
                        cls.class_code, cls.class_name, cls.section, cls.attendance_policy,
                        cls.late_threshold, cls.total_weeks, cls.total_hours, cls.weekly_hours,
                        self._format_schedule_for_export(cls.schedule),
                    ])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to write file:\n{e}")
            return

        QMessageBox.information(self, "Success", f"Class list exported to:\n{file_path}")

    def load_classes(self):
        """Load class buttons into class_btns_layout"""
        while self.class_btns_layout.count():
            item = self.class_btns_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        showing_archived = self.show_archived_cb.isChecked()
        self.create_new_class_btn.setVisible(not showing_archived)
        custom_order_mode = self.class_sort_combo.currentText() == "Custom Order" and not showing_archived

        classes = sorted(self.fetch_classes(), key=self._class_sort_key)
        self.empty_state_lbl.setText(
            "No archived classes." if showing_archived
            else "You haven't created any classes yet. Use \"Create New Class\" below to get started."
        )
        self.empty_state_lbl.setVisible(not classes)

        self.class_grid_widget.setVisible(not custom_order_mode)
        self.custom_order_listWidget.setVisible(custom_order_mode)
        if custom_order_mode:
            self._populate_custom_order_list(classes)
        else:
            row_builder = self._make_archived_class_row_widget if showing_archived else self._make_class_row_widget
            for row, cls in enumerate(classes):
                self.class_btns_layout.addWidget(row_builder(cls), row, 0)

        self.today_classes_title_lbl.setVisible(not showing_archived)
        self.recently_viewed_title_lbl.setVisible(not showing_archived)
        if showing_archived:
            self._populate_today_classes([])
            self.no_classes_today_lbl.setVisible(False)
            self._populate_recently_viewed([])
            self.no_recently_viewed_lbl.setVisible(False)
        else:
            self._populate_today_classes(classes)
            self._populate_recently_viewed(classes)

    def _populate_custom_order_list(self, classes):
        self.custom_order_listWidget.clear()
        saved_order = load_class_order()
        order_index = {class_id: i for i, class_id in enumerate(saved_order)}
        ordered = sorted(
            classes,
            key=lambda c: (0 if c.pinned else 1, order_index.get(c.class_id, len(saved_order))),
        )
        for cls in ordered:
            item = QListWidgetItem(f"{'★ ' if cls.pinned else ''}{cls.class_name} ({cls.class_code})")
            item.setData(Qt.UserRole, cls.class_id)
            self.custom_order_listWidget.addItem(item)

    def _save_custom_order(self, *args):
        class_ids = [
            self.custom_order_listWidget.item(i).data(Qt.UserRole)
            for i in range(self.custom_order_listWidget.count())
        ]
        save_class_order(class_ids)

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

    def _track_recently_viewed(self, cls):
        self.recently_viewed_class_ids = [
            class_id for class_id in self.recently_viewed_class_ids if class_id != cls.class_id
        ]
        self.recently_viewed_class_ids.insert(0, cls.class_id)
        self.recently_viewed_class_ids = self.recently_viewed_class_ids[:5]

    def _populate_recently_viewed(self, classes):
        while self.recently_viewed_layout.count():
            item = self.recently_viewed_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        by_id = {c.class_id: c for c in classes}
        recent_classes = [
            by_id[class_id] for class_id in self.recently_viewed_class_ids if class_id in by_id
        ]
        self.no_recently_viewed_lbl.setVisible(not recent_classes)
        for cls in recent_classes:
            self.recently_viewed_layout.addWidget(self._make_recently_viewed_row_widget(cls))

    def _make_recently_viewed_row_widget(self, cls):
        row = QWidget()
        row.setObjectName("recently_viewed_row_widget")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(4, 4, 4, 4)

        label = QLabel(f"{cls.class_name} ({cls.class_code})")
        layout.addWidget(label, 1)

        open_btn = QPushButton("Open")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.clicked.connect(lambda _, c=cls: self.open_class_window(c))
        layout.addWidget(open_btn)

        return row

    def _make_class_row_widget(self, cls):
        compact = self.compact_view_cb.isChecked()
        class_widget = QWidget()
        class_widget.setObjectName("class_row_widget")
        row_layout = QHBoxLayout(class_widget)
        row_layout.setContentsMargins(*((4, 2, 4, 2) if compact else (4, 4, 4, 4)))

        color_chip = QFrame()
        color_chip.setFixedWidth(4)
        color_chip.setMinimumHeight(40)
        color_chip.setStyleSheet(
            f"background-color: {cls.color or class_tag_color(cls.class_code)}; border-radius: 2px;"
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
        caption_lbl.setVisible(not compact)

        text_layout.addWidget(class_btn)
        text_layout.addWidget(caption_lbl)

        pin_btn = QPushButton("★" if cls.pinned else "☆")
        pin_btn.setFixedSize(28, 28)
        pin_btn.setCursor(Qt.PointingHandCursor)
        pin_btn.setToolTip("Unpin class" if cls.pinned else "Pin class to the top")
        pin_btn.clicked.connect(lambda _, c=cls: self.toggle_pin_class(c))

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
        row_layout.addWidget(pin_btn)
        row_layout.addWidget(duplicate_btn)
        row_layout.addWidget(archive_btn)
        return class_widget

    def toggle_pin_class(self, cls):
        try:
            self.class_manager.update_class(cls.class_id, {"pinned": not cls.pinned})
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Could not update {cls.class_code}:\n{e}")
            return
        self.load_classes()

    def open_duplicate_class_window(self, cls):
        self.duplicate_class_window = AddNewClassWindow(user_id=self.user_id, duplicate_from=cls)
        self.duplicate_class_window.class_created.connect(self.load_classes)
        self.duplicate_class_window.roster_load_failed.connect(
            lambda msg: self.add_notification(f"Roster upload failed: {msg}")
        )
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
        self._track_recently_viewed(class_obj)
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
        self.add_new_class_window.roster_load_failed.connect(
            lambda msg: self.add_notification(f"Roster upload failed: {msg}")
        )
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

    def export_account_data(self):
        classes = self.fetch_classes()
        data = {
            "user_id": self.user_id,
            "email": self.user.email,
            "name": self.user.name,
            "surname": self.user.surname,
            "classes": [
                {
                    "class_code": cls.class_code,
                    "class_name": cls.class_name,
                    "section": cls.section,
                    "attendance_policy": cls.attendance_policy,
                    "late_threshold": cls.late_threshold,
                    "total_weeks": cls.total_weeks,
                    "total_hours": cls.total_hours,
                    "weekly_hours": cls.weekly_hours,
                }
                for cls in classes
            ],
            "recent_logins": self.account_manager.get_login_history(self.user_id, limit=5),
        }

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Download My Data", "my_account_data.json", "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to write file:\n{e}")
            return

        QMessageBox.information(self, "Success", f"Account data exported to:\n{file_path}")

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

    # --- Notifications ---

    def add_notification(self, message):
        """Appends an in-app activity notification (e.g. a roster upload
        failure, an at-risk student summary). No email/SMTP is configured
        for this project, so this is an in-app feed rather than a real
        email digest."""
        if self.notifications and self.notifications[-1][1] == message:
            return  # avoid spamming the same message on repeated refreshes
        timestamp = datetime.now().strftime("%H:%M")
        self.notifications.append((timestamp, message))
        self._update_notifications_badge()

    def clear_notifications(self):
        self.notifications = []
        self._update_notifications_badge()

    def _update_notifications_badge(self):
        count = len(self.notifications)
        self.notifications_badge_lbl.setText(str(count) if count else "")
        self.notifications_badge_lbl.setVisible(count > 0)

    def show_notifications_menu(self):
        menu = QMenu(self)
        if not self.notifications:
            menu.addAction("No notifications").setEnabled(False)
        else:
            for timestamp, message in reversed(self.notifications):
                menu.addAction(f"[{timestamp}] {message}").setEnabled(False)
            menu.addSeparator()
            menu.addAction("Clear All").triggered.connect(self.clear_notifications)
        menu.exec_(self.notifications_btn.mapToGlobal(self.notifications_btn.rect().bottomLeft()))

    def toggle_dark_mode(self, checked):
        theme = "dark" if checked else "light"
        save_theme_preference(theme)
        with open(stylesheet_path(theme)) as f:
            QApplication.instance().setStyleSheet(f.read())

    def toggle_list_density(self, checked):
        save_list_density("compact" if checked else "comfortable")
        self.load_classes()

    def _apply_translations(self):
        self.my_classes_btn.setText(t("my_classes"))
        self.settings_btn.setText(t("settings"))
        self.statistics_btn.setText(t("statistics"))
        self.log_out_btn.setText(t("log_out"))
        self.create_new_class_btn.setText(t("create_new_class"))
        self.profile_btn.setText(t("profile"))
        self.my_classes_title_lbl.setText(t("my_classes"))
        self.title_lbl_settings.setText(t("settings"))
        self.statistics_title_lbl.setText(t("attendance_statistics"))

    def _setup_language_combo(self):
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        for code, label in LANGUAGES.items():
            self.language_combo.addItem(label, code)
        current = load_language_preference()
        self.language_combo.setCurrentIndex(list(LANGUAGES).index(current))
        self.language_combo.blockSignals(False)
        self.language_combo.currentIndexChanged.connect(self.change_language)

    def change_language(self):
        save_language_preference(self.language_combo.currentData())
        QMessageBox.information(
            self, "Language Changed", "Restart the app for the new language to take full effect."
        )

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

        typed_email, ok = QInputDialog.getText(
            self, "Confirm Deletion",
            f"Type your email ({self.user.email}) to confirm permanent deletion:",
        )
        if not ok:
            return
        if typed_email.strip().lower() != self.user.email.strip().lower():
            QMessageBox.warning(self, "Email Didn't Match", "Account deletion cancelled.")
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

    def export_statistics_chart(self):
        if self.statistics_canvas is None:
            QMessageBox.information(
                self, "Nothing to Export", "Select a class with attendance data first."
            )
            return

        cls = self.statistics_class_combo.currentData()
        default_name = f"{cls.class_code}_statistics.png" if cls else "statistics.png"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Chart", default_name, "PNG Image (*.png);;PDF Document (*.pdf)"
        )
        if not file_path:
            return

        figure = self.statistics_canvas.figure
        try:
            figure.savefig(file_path, facecolor=figure.get_facecolor())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export chart:\n{e}")
            return

        QMessageBox.information(self, "Success", f"Chart exported to:\n{file_path}")
