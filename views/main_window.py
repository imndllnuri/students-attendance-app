import csv
import json
import math
from collections import defaultdict
from datetime import datetime

import numpy as np
import pandas as pd
import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtCore import QEasingCurve, QEvent, QPropertyAnimation, Qt, QSize, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QKeySequence, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QShortcut,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from services.api_client import ApiError
from shared.class_order import load_class_order, save_class_order
from shared.font_scale import SCALE_LABELS, load_font_scale, point_size_for_scale, save_font_scale
from shared.i18n import LANGUAGES, load_language_preference, save_language_preference, t
from shared.list_density import load_list_density, save_list_density
from shared.palette import (
    PALETTE,
    RADIUS,
    active_palette,
    attendance_tier,
    class_tag_color,
    class_tag_color_key,
)
from shared.qt_style import set_dynamic_property
from shared.shadow import apply_card_shadow
from shared.session_timeout import (
    TIMEOUT_OPTIONS,
    load_session_timeout_minutes,
    save_session_timeout_minutes,
)
from shared.theme import load_theme_preference, save_theme_preference, stylesheet_path
from shared.widgets import clear_layout, make_tag_pill
from shared.validation import (
    MIN_PASSWORD_LENGTH,
    SECURITY_QUESTIONS,
    is_valid_email,
    is_valid_password,
    password_strength,
)
from shared.whats_new import (
    APP_VERSION,
    CHANGELOG,
    save_last_seen_version,
    should_show_whats_new,
)
from views.add_new_class_window import AddNewClassWindow
from models.accounts import AccountManager
from models.classes import Class, ClassManager

DASHBOARD_PAGE, MY_CLASSES_PAGE, SETTINGS_PAGE, SEARCH_PAGE, PROFILE_PAGE, STATISTICS_PAGE = range(6)

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
        self._last_chart_builder = None
        self.notifications = []
        self.recently_viewed_class_ids = []
        self.selected_class_ids = set()

        self.sidebar_user_name_lbl.setText(f"{user.name} {user.surname}")
        self.sidebar_user_email_lbl.setText(getattr(user, "email", ""))
        self.sidebar_avatar_lbl.setPixmap(self._make_initials_avatar(user.name, user.surname, size=36))
        self.sidebar_top_name_lbl.setText(f"{user.name} {user.surname}")
        self.sidebar_top_avatar_lbl.setPixmap(self._make_initials_avatar(user.name, user.surname, size=36))

        self.profile_btn.clicked.connect(self.show_profile_menu)
        self.dashboard_btn.clicked.connect(self.show_dashboard)
        self.my_classes_btn.clicked.connect(self.show_my_classes)
        self.settings_btn.clicked.connect(self.show_settings)
        self.statistics_btn.clicked.connect(self.show_statistics)
        self.log_out_btn.clicked.connect(self.confirm_logout)
        self.sidebar_profile_widget.setCursor(Qt.PointingHandCursor)
        self.sidebar_profile_widget.mousePressEvent = lambda _event: self.show_profile()
        self.create_new_class_btn.clicked.connect(self.open_add_new_class_window)
        self.add_class_dashboard_btn.clicked.connect(self.open_add_new_class_window)
        self.import_classes_btn.clicked.connect(self.import_classes_from_spreadsheet)
        set_dynamic_property(self.add_class_dashboard_btn, "variant", "primary")
        set_dynamic_property(self.create_new_class_btn, "variant", "primary")
        self._dashboard_filter_group = QButtonGroup(self)
        self._dashboard_filter_group.setExclusive(True)
        for tab_btn in (
            self.dashboard_filter_all_btn, self.dashboard_filter_active_btn, self.dashboard_filter_pinned_btn,
        ):
            set_dynamic_property(tab_btn, "variant", "segmented")
            self._dashboard_filter_group.addButton(tab_btn)
            tab_btn.clicked.connect(self.render_dashboard)
        self.search_bar_le.addAction(qta.icon("fa5s.search", color="#C7C7D1"), QLineEdit.LeadingPosition)
        self.search_bar_le.returnPressed.connect(self.show_search)
        self.notifications_btn.clicked.connect(self.show_notifications_menu)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme_button)
        self.statistics_class_combo.currentIndexChanged.connect(self.render_statistics)
        self.export_chart_btn.clicked.connect(self.export_statistics_chart)
        self.compare_classes_btn.clicked.connect(self.show_class_comparison)
        self.attendance_heatmap_btn.clicked.connect(self.show_attendance_heatmap)
        self.export_pdf_report_btn.clicked.connect(self.export_statistics_pdf)
        for btn in (
            self.compare_classes_btn, self.attendance_heatmap_btn,
            self.export_chart_btn, self.export_pdf_report_btn,
        ):
            set_dynamic_property(btn, "variant", "ghost")
        self.class_sort_combo.currentIndexChanged.connect(self.load_classes)
        self.show_archived_cb.toggled.connect(self.load_classes)
        self.compact_view_cb.blockSignals(True)
        self.compact_view_cb.setChecked(load_list_density() == "compact")
        self.compact_view_cb.blockSignals(False)
        self.compact_view_cb.toggled.connect(self.toggle_list_density)
        set_dynamic_property(self.export_class_list_btn, "variant", "secondary")
        set_dynamic_property(self.bulk_archive_btn, "variant", "secondary")
        self.export_class_list_btn.clicked.connect(self.export_class_list)
        self.bulk_archive_btn.clicked.connect(self.bulk_archive_selected)
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
        self.settings_security_question_2_combo.addItems(SECURITY_QUESTIONS)
        if len(SECURITY_QUESTIONS) > 1:
            self.settings_security_question_2_combo.setCurrentIndex(1)
        self.change_password_btn.clicked.connect(self.change_password)
        self.update_security_question_btn.clicked.connect(self.update_security_questions)
        self.delete_account_btn.clicked.connect(self.confirm_delete_account)
        self._settings_password_toggle = self.new_password_le.addAction(
            qta.icon("fa5s.eye", color="#6B6B76"), QLineEdit.TrailingPosition
        )
        self._settings_password_toggle.setCheckable(True)
        self._settings_password_toggle.setToolTip("Show password")
        self._settings_password_toggle.toggled.connect(self._toggle_settings_password_echo)
        self.new_password_le.textChanged.connect(self.validate_new_password)
        self.new_password_le.textChanged.connect(self._update_settings_password_strength)
        self.confirm_new_password_le.textChanged.connect(self.validate_new_password_match)

        self._nav_buttons = (self.dashboard_btn, self.my_classes_btn, self.statistics_btn, self.settings_btn)
        self._setup_icons()
        self._apply_card_shadows()
        self._setup_shortcuts()
        self._setup_session_timeout()
        self._setup_session_timeout_combo()
        self._setup_font_scale_combo()
        self._setup_server_health_indicator()

        self.load_classes()
        self._flush_offline_queue_on_startup()
        self.show_dashboard()
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

    def _setup_font_scale_combo(self):
        self.font_scale_combo.blockSignals(True)
        self.font_scale_combo.clear()
        for scale, label in SCALE_LABELS.items():
            self.font_scale_combo.addItem(label, scale)
        current_scale = load_font_scale()
        self.font_scale_combo.setCurrentIndex(list(SCALE_LABELS).index(current_scale))
        self.font_scale_combo.blockSignals(False)
        self.font_scale_combo.currentIndexChanged.connect(self.change_font_scale)

    def change_font_scale(self):
        scale = self.font_scale_combo.currentData()
        save_font_scale(scale)
        font = QApplication.instance().font()
        font.setPointSize(point_size_for_scale(scale))
        QApplication.instance().setFont(font)

    def _setup_server_health_indicator(self):
        self._health_check_timer = QTimer(self)
        self._health_check_timer.timeout.connect(self.update_server_health_indicator)
        self._health_check_timer.start(30000)  # recheck every 30s
        self.update_server_health_indicator()

    def update_server_health_indicator(self):
        palette = active_palette()
        if self.class_manager.check_server_health():
            self.server_health_lbl.setText("● Connected")
            self.server_health_lbl.setStyleSheet(f"color: {palette['success']};")
        else:
            self.server_health_lbl.setText("● Offline")
            self.server_health_lbl.setStyleSheet(f"color: {palette['error']};")

    def export_settings(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "app_settings.json", "JSON Files (*.json)"
        )
        if not file_path:
            return

        settings = {
            "theme": load_theme_preference(),
            "language": load_language_preference(),
            "session_timeout_minutes": self.session_timeout_minutes,
            "list_density": load_list_density(),
            "font_scale": load_font_scale(),
        }
        try:
            with open(file_path, "w") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to write file:\n{e}")
            return

        QMessageBox.information(self, "Success", f"Settings exported to:\n{file_path}")

    def import_settings(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            with open(file_path) as f:
                settings = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read file:\n{e}")
            return

        if settings.get("theme") in ("light", "dark"):
            theme = settings["theme"]
            save_theme_preference(theme)
            with open(stylesheet_path(theme)) as f:
                QApplication.instance().setStyleSheet(f.read())
            self.dark_mode_cb.blockSignals(True)
            self.dark_mode_cb.setChecked(theme == "dark")
            self.dark_mode_cb.blockSignals(False)

        if settings.get("language") in LANGUAGES:
            save_language_preference(settings["language"])
            index = list(LANGUAGES).index(settings["language"])
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)

        minutes = settings.get("session_timeout_minutes")
        if minutes in TIMEOUT_OPTIONS:
            save_session_timeout_minutes(minutes)
            self.session_timeout_minutes = minutes
            self._reset_inactivity_timer()
            self.session_timeout_combo.blockSignals(True)
            self.session_timeout_combo.setCurrentIndex(TIMEOUT_OPTIONS.index(minutes))
            self.session_timeout_combo.blockSignals(False)

        if settings.get("list_density") in ("comfortable", "compact"):
            density = settings["list_density"]
            save_list_density(density)
            self.compact_view_cb.blockSignals(True)
            self.compact_view_cb.setChecked(density == "compact")
            self.compact_view_cb.blockSignals(False)
            self.load_classes()

        if settings.get("font_scale") in SCALE_LABELS:
            scale = settings["font_scale"]
            save_font_scale(scale)
            font = QApplication.instance().font()
            font.setPointSize(point_size_for_scale(scale))
            QApplication.instance().setFont(font)
            self.font_scale_combo.blockSignals(True)
            self.font_scale_combo.setCurrentIndex(list(SCALE_LABELS).index(scale))
            self.font_scale_combo.blockSignals(False)

        QMessageBox.information(
            self, "Success",
            "Settings imported. The language change (if any) applies on next launch.",
        )

    def _setup_icons(self):
        self.dashboard_btn.setIcon(qta.icon("fa5s.th-large", color="#767D91"))
        self.my_classes_btn.setIcon(qta.icon("fa5s.book-open", color="#767D91"))
        self.statistics_btn.setIcon(qta.icon("fa5s.chart-bar", color="#767D91"))
        self.settings_btn.setIcon(qta.icon("fa5s.cog", color="#767D91"))
        self.log_out_btn.setIcon(qta.icon("fa5s.sign-out-alt", color="#767D91"))
        for btn in (self.dashboard_btn, self.my_classes_btn, self.statistics_btn, self.settings_btn, self.log_out_btn):
            btn.setIconSize(QSize(16, 16))

        avatar_pixmap = self._make_initials_avatar(self.user.name, self.user.surname, size=34)
        self.profile_btn.setIcon(QIcon(avatar_pixmap))
        self.profile_btn.setIconSize(QSize(34, 34))
        self.notifications_btn.setIcon(qta.icon("fa5s.bell", color="#8A93A7"))
        self.notifications_btn.setIconSize(QSize(16, 16))
        self._update_theme_toggle_icon()

        self.dashboard_btn.setToolTip("Dashboard (Ctrl+1)")
        self.my_classes_btn.setToolTip("My Classes (Ctrl+2)")
        self.statistics_btn.setToolTip("Statistics (Ctrl+3)")
        self.settings_btn.setToolTip("Settings (Ctrl+4)")
        self.create_new_class_btn.setToolTip("Create New Class (Ctrl+N)")
        self.create_new_class_btn.setIcon(qta.icon("fa5s.plus", color="white"))

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+N"), self, self.open_add_new_class_window)
        QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)
        QShortcut(QKeySequence("Ctrl+1"), self, self.show_dashboard)
        QShortcut(QKeySequence("Ctrl+2"), self, self.show_my_classes)
        QShortcut(QKeySequence("Ctrl+3"), self, self.show_statistics)
        QShortcut(QKeySequence("Ctrl+4"), self, self.show_settings)
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
            apply_card_shadow(frame, strength="md")

    def _set_active_nav(self, active_btn):
        for btn in self._nav_buttons:
            btn.setProperty("active", btn is active_btn)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def show_profile(self):
        self.populate_profile_fields()
        self.stackedWidget.setCurrentIndex(PROFILE_PAGE)

    def show_profile_menu(self):
        """Avatar button in the topbar opens a small QMenu (name/email
        header + Edit Profile / Settings / Sign Out), per the AttendU
        reference - the avatar itself no longer navigates directly."""
        menu = QMenu(self)
        header = menu.addAction(f"{self.user.name} {self.user.surname}")
        header.setEnabled(False)
        email_action = menu.addAction(getattr(self.user, "email", ""))
        email_action.setEnabled(False)
        menu.addSeparator()
        menu.addAction("Edit Profile", self.show_profile)
        menu.addAction("Settings", self.show_settings)
        menu.addSeparator()
        menu.addAction("Sign Out", self.confirm_logout)
        menu.exec_(self.profile_btn.mapToGlobal(self.profile_btn.rect().bottomRight()))

    def toggle_theme_button(self):
        """The topbar's sun/moon icon button - same mechanism as the
        Settings page's Dark Mode checkbox (toggle_dark_mode), just
        triggered from a plain button instead of a checked state."""
        self.toggle_dark_mode(load_theme_preference() != "dark")
        self.dark_mode_cb.blockSignals(True)
        self.dark_mode_cb.setChecked(load_theme_preference() == "dark")
        self.dark_mode_cb.blockSignals(False)
        self._update_theme_toggle_icon()

    def _update_theme_toggle_icon(self):
        is_dark = load_theme_preference() == "dark"
        icon_name = "fa5s.sun" if is_dark else "fa5s.moon"
        self.theme_toggle_btn.setIcon(qta.icon(icon_name, color="#8A93A7"))

    def show_dashboard(self):
        self._set_active_nav(self.dashboard_btn)
        self.stackedWidget.setCurrentIndex(DASHBOARD_PAGE)
        self.render_dashboard()

    def _render_dashboard_greeting(self):
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        self.dashboard_greeting_lbl.setText(f"{greeting}, {self.user.name} \U0001F44B")
        self.dashboard_date_lbl.setText(datetime.now().strftime("%A, %B %-d, %Y"))

    def _make_dashboard_stat_card(self, label, value, caption, icon_name=None, icon_color=None):
        palette = active_palette()
        card = QFrame()
        card.setObjectName("dashboard_stat_card")
        apply_card_shadow(card, strength="sm")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        header_row = QHBoxLayout()
        label_lbl = QLabel(label)
        label_lbl.setObjectName("class_row_caption_lbl")
        header_row.addWidget(label_lbl)
        header_row.addStretch(1)
        if icon_name:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(qta.icon(icon_name, color=icon_color or palette["accent"]).pixmap(16, 16))
            header_row.addWidget(icon_lbl)
        layout.addLayout(header_row)

        value_lbl = QLabel(value)
        value_lbl.setObjectName("dashboard_stat_value_lbl")
        layout.addWidget(value_lbl)

        caption_lbl = QLabel(caption)
        caption_lbl.setObjectName("class_row_caption_lbl")
        layout.addWidget(caption_lbl)

        return card

    def _current_dashboard_filter(self):
        if self.dashboard_filter_pinned_btn.isChecked():
            return "pinned"
        if self.dashboard_filter_active_btn.isChecked():
            return "active"
        return "all"

    def render_dashboard(self):
        self._render_dashboard_greeting()
        self.load_classes()  # keeps My Classes' row-list in sync while we're at it

        try:
            all_classes = self.class_manager.load_classes_for_instructor(self.user_id, include_archived=True)
        except ApiError:
            all_classes = []

        active_classes = [c for c in all_classes if not c.archived]
        self._populate_today_classes(active_classes)
        self._populate_recently_viewed(active_classes)

        total = len(all_classes)
        archived = len(all_classes) - len(active_classes)
        pinned = [c for c in all_classes if c.pinned and not c.archived]
        non_pinned_active = [c for c in active_classes if not c.pinned]

        total_present = 0
        total_records = 0
        for cls in active_classes:
            try:
                stats = self.class_manager.get_statistics(cls.class_id)
            except ApiError:
                continue
            attended = stats.get("present", 0) + stats.get("late", 0)
            total_present += attended
            total_records += attended + stats.get("absent", 0)
        overall_rate = int(total_present / total_records * 100) if total_records else 0

        clear_layout(self.dashboard_stats_row)
        for label, value, caption, icon_name in (
            ("Active Classes", str(len(active_classes)), "Currently enrolled", "fa5s.th-large"),
            ("Pinned Classes", str(len(pinned)), "Quick access", "fa5s.thumbtack"),
            ("Total Classes", str(total), "All sessions logged", "fa5s.layer-group"),
            ("Attended", str(total_present), f"{overall_rate}% overall rate", "fa5s.check-circle"),
            ("Archived", str(archived), "Past sessions", "fa5s.archive"),
        ):
            self.dashboard_stats_row.addWidget(self._make_dashboard_stat_card(label, value, caption, icon_name))

        self.dashboard_filter_all_btn.setText(f"All Classes ({total})")
        self.dashboard_filter_active_btn.setText(f"Active ({len(active_classes)})")
        self.dashboard_filter_pinned_btn.setText(f"Pinned ({len(pinned)})")

        dashboard_filter = self._current_dashboard_filter()
        show_pinned = dashboard_filter in ("all", "pinned") and bool(pinned)
        show_active = dashboard_filter in ("all", "active")
        show_inactive = dashboard_filter == "all" and archived > 0

        self.dashboard_empty_state_lbl.setVisible(total == 0)

        self.dashboard_pinned_title_lbl.setVisible(show_pinned)
        self.dashboard_pinned_grid_widget.setVisible(show_pinned)
        clear_layout(self.dashboard_pinned_grid)
        if show_pinned:
            self._add_class_cards_to_grid(self.dashboard_pinned_grid, pinned, self.dashboard_pinned_grid_widget)

        self.dashboard_active_title_lbl.setVisible(show_active and bool(non_pinned_active))
        self.dashboard_active_grid_widget.setVisible(show_active)
        clear_layout(self.dashboard_active_grid)
        if show_active:
            self._add_class_cards_to_grid(
                self.dashboard_active_grid, non_pinned_active, self.dashboard_active_grid_widget
            )

        archived_classes = [c for c in all_classes if c.archived]
        self.dashboard_inactive_title_lbl.setVisible(show_inactive)
        self.dashboard_inactive_grid_widget.setVisible(show_inactive)
        clear_layout(self.dashboard_inactive_grid)
        if show_inactive:
            self._add_class_cards_to_grid(
                self.dashboard_inactive_grid, archived_classes, self.dashboard_inactive_grid_widget
            )

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
        """Load class rows into class_btns_layout (My Classes' row-list)."""
        clear_layout(self.class_btns_layout)

        self.selected_class_ids = set()
        showing_archived = self.show_archived_cb.isChecked()
        self.create_new_class_btn.setVisible(not showing_archived)
        custom_order_mode = self.class_sort_combo.currentText() == "Custom Order" and not showing_archived

        classes = sorted(self.fetch_classes(), key=self._class_sort_key)
        self.empty_state_lbl.setText(
            "No archived classes." if showing_archived
            else "You haven't created any classes yet. Use \"+ Create New Class\" above to get started."
        )
        self.empty_state_lbl.setVisible(not classes)
        self.my_classes_count_lbl.setText(
            f"{len(classes)} archived" if showing_archived else f"{len(classes)} enrolled"
        )

        self.class_grid_widget.setVisible(not custom_order_mode)
        self.custom_order_listWidget.setVisible(custom_order_mode)
        if custom_order_mode:
            self._populate_custom_order_list(classes)
        elif showing_archived:
            for cls in classes:
                self.class_btns_layout.addWidget(self._make_archived_class_row_widget(cls))
        else:
            for cls in classes:
                self.class_btns_layout.addWidget(self._make_class_list_row_widget(cls))

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
        clear_layout(self.today_classes_layout)

        todays_classes = self._classes_scheduled_today(classes)
        self.no_classes_today_lbl.setVisible(not todays_classes)
        for cls in todays_classes:
            self.today_classes_layout.addWidget(self._make_today_class_row_widget(cls))

    def _make_today_class_row_widget(self, cls):
        row = QFrame()
        row.setObjectName("today_class_row_widget")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setObjectName("today_class_icon_lbl")
        icon_lbl.setPixmap(qta.icon("fa5s.calendar-day", color=active_palette()["accent"]).pixmap(16, 16))
        layout.addWidget(icon_lbl)

        label = QLabel(f"{cls.class_name} ({cls.class_code})")
        label.setObjectName("today_class_label_lbl")
        layout.addWidget(label, 1)

        take_attendance_btn = QPushButton("Take Attendance")
        take_attendance_btn.setCursor(Qt.PointingHandCursor)
        set_dynamic_property(take_attendance_btn, "variant", "secondary")
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
        clear_layout(self.recently_viewed_layout)

        by_id = {c.class_id: c for c in classes}
        recent_classes = [
            by_id[class_id] for class_id in self.recently_viewed_class_ids if class_id in by_id
        ]
        self.no_recently_viewed_lbl.setVisible(not recent_classes)
        for cls in recent_classes:
            self.recently_viewed_layout.addWidget(self._make_recently_viewed_row_widget(cls))

    def _make_recently_viewed_row_widget(self, cls):
        row = QFrame()
        row.setObjectName("recently_viewed_row_widget")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setObjectName("recently_viewed_icon_lbl")
        icon_lbl.setPixmap(qta.icon("fa5s.history", color=active_palette()["text_secondary"]).pixmap(16, 16))
        layout.addWidget(icon_lbl)

        label = QLabel(f"{cls.class_name} ({cls.class_code})")
        label.setObjectName("recently_viewed_label_lbl")
        layout.addWidget(label, 1)

        open_btn = QPushButton("Open")
        open_btn.setCursor(Qt.PointingHandCursor)
        set_dynamic_property(open_btn, "variant", "ghost")
        open_btn.clicked.connect(lambda _, c=cls: self.open_class_window(c))
        layout.addWidget(open_btn)

        return row

    MIN_CARD_WIDTH = 220

    _DAY_ABBREV = {
        "Monday": "Mon", "Tuesday": "Tue", "Wednesday": "Wed", "Thursday": "Thu",
        "Friday": "Fri", "Saturday": "Sat", "Sunday": "Sun",
    }

    def _format_schedule_caption(self, schedule):
        """Compact "Mon / Wed 09:00"-style caption, matching the reference's
        ClassCard/ClassListRow schedule line."""
        days = [day for day in _WEEKDAY_ORDER if any(s.selected for s in schedule.get(day, []))]
        if not days:
            return "No schedule set"
        first_slots = [s for s in schedule[days[0]] if s.selected]
        time_str = first_slots[0].start_time.toString("HH:mm") if first_slots else ""
        return f"{' / '.join(self._DAY_ABBREV[d] for d in days)} {time_str}".strip()

    def _get_class_stats(self, cls):
        """(attended, missed, total, percent) for one class - present+late
        both count as "attended" per the same convention the roster table
        and PDF report already use elsewhere."""
        try:
            stats = self.class_manager.get_statistics(cls.class_id)
        except ApiError:
            return 0, 0, 0, 0
        attended = stats.get("present", 0) + stats.get("late", 0)
        missed = stats.get("absent", 0)
        total = attended + missed
        percent = int(attended / total * 100) if total else 0
        return attended, missed, total, percent

    def _num_grid_columns(self, container):
        width = container.width()
        if width <= 0:
            return 3
        return max(1, width // self.MIN_CARD_WIDTH)

    def _add_class_cards_to_grid(self, layout, classes, container):
        columns = self._num_grid_columns(container)
        for index, cls in enumerate(classes):
            row, col = divmod(index, columns)
            layout.addWidget(self._make_dashboard_class_card_widget(cls), row, col)

    def _make_class_detail_panel(self, cls, attended, missed, total):
        """Expandable "Properties" detail - a compact label/value grid plus
        Duplicate/Archive actions, shared by the Dashboard card and the My
        Classes row so both "expand for more" affordances look the same."""
        panel = QFrame()
        panel.setObjectName("class_detail_panel")
        grid = QGridLayout(panel)
        grid.setContentsMargins(14, 10, 14, 10)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(6)

        entries = [
            ("Section", cls.section),
            ("Schedule", self._format_schedule_caption(cls.schedule)),
            ("Total Sessions", str(total)),
            ("Attended", str(attended)),
            ("Missed", str(missed)),
            ("Archived", "Yes" if cls.archived else "No"),
        ]
        for index, (label, value) in enumerate(entries):
            row, col = divmod(index, 2)
            cell = QVBoxLayout()
            cell.setSpacing(0)
            key_lbl = QLabel(label)
            key_lbl.setProperty("fieldLabel", True)
            value_lbl = QLabel(value)
            value_lbl.setProperty("fieldValue", True)
            cell.addWidget(key_lbl)
            cell.addWidget(value_lbl)
            grid.addLayout(cell, row, col)

        actions_row = QHBoxLayout()
        duplicate_btn = QPushButton("Duplicate")
        set_dynamic_property(duplicate_btn, "variant", "ghost")
        duplicate_btn.setCursor(Qt.PointingHandCursor)
        duplicate_btn.setToolTip("Create a new class with the same schedule and policy")
        duplicate_btn.clicked.connect(lambda _, c=cls: self.open_duplicate_class_window(c))
        actions_row.addWidget(duplicate_btn)
        actions_row.addStretch(1)

        archive_btn = QPushButton("Unarchive" if cls.archived else "Archive")
        set_dynamic_property(archive_btn, "variant", "secondary" if cls.archived else "destructive")
        archive_btn.setCursor(Qt.PointingHandCursor)
        if cls.archived:
            archive_btn.clicked.connect(lambda _, c=cls: self.unarchive_class(c))
        else:
            archive_btn.clicked.connect(lambda _, c=cls: self.archive_class(c))
        actions_row.addWidget(archive_btn)
        grid.addLayout(actions_row, (len(entries) + 1) // 2, 0, 1, 2)

        return panel

    def _make_expand_toggle(self, detail_panel, collapsed_text, expanded_text):
        toggle_btn = QPushButton(collapsed_text)
        set_dynamic_property(toggle_btn, "variant", "ghost")
        toggle_btn.setCheckable(True)
        toggle_btn.setCursor(Qt.PointingHandCursor)
        detail_panel.setVisible(False)

        def on_toggled(checked):
            detail_panel.setVisible(checked)
            toggle_btn.setText(expanded_text if checked else collapsed_text)

        toggle_btn.toggled.connect(on_toggled)
        return toggle_btn

    def _make_dashboard_class_card_widget(self, cls):
        """AttendU-style ClassCard: a colored top accent bar, name, pin,
        schedule caption, an attendance-rate progress bar, an ACTIVE/
        INACTIVE status pill, and an expandable Properties panel."""
        attended, missed, total, percent = self._get_class_stats(cls)
        color = cls.color or class_tag_color(cls.class_code)
        tier = attendance_tier(percent, cls.attendance_policy)

        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        card = QFrame()
        card.setObjectName("dashboard_class_card")
        card.setFixedWidth(self.MIN_CARD_WIDTH - 10)
        apply_card_shadow(card, strength="sm")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 4, 14, 14)
        card_layout.setSpacing(6)

        accent_bar = QFrame()
        accent_bar.setFixedHeight(4)
        accent_bar.setStyleSheet(f"background-color: {color}; border: none; border-radius: 2px;")
        card_layout.addWidget(accent_bar)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 6, 0, 0)
        title_btn = QPushButton()
        title_btn.setObjectName("class_card_title_btn")
        available_width = self.MIN_CARD_WIDTH - 10 - 28 - 30  # card width minus margins minus pin button
        elided = title_btn.fontMetrics().elidedText(cls.class_name, Qt.ElideRight, available_width)
        title_btn.setText(elided)
        title_btn.setCursor(Qt.PointingHandCursor)
        title_btn.setToolTip(f"{cls.class_name} ({cls.class_code})")
        title_btn.clicked.connect(lambda _, c=cls: self.open_class_window(c))
        top_row.addWidget(title_btn, 1)

        pin_btn = QPushButton("★" if cls.pinned else "☆")
        pin_btn.setObjectName("card_icon_btn")
        pin_btn.setFixedSize(22, 22)
        pin_btn.setCursor(Qt.PointingHandCursor)
        pin_btn.setToolTip("Unpin class" if cls.pinned else "Pin class to the top")
        pin_btn.clicked.connect(lambda _, c=cls: self.toggle_pin_class(c))
        top_row.addWidget(pin_btn)
        card_layout.addLayout(top_row)

        caption_lbl = QLabel(f"{cls.class_code} · {self._format_schedule_caption(cls.schedule)}")
        caption_lbl.setObjectName("class_row_caption_lbl")
        card_layout.addWidget(caption_lbl)

        attendance_row = QHBoxLayout()
        attendance_lbl = QLabel("Attendance")
        attendance_lbl.setObjectName("class_row_caption_lbl")
        attendance_row.addWidget(attendance_lbl)
        attendance_row.addStretch(1)
        percent_lbl = QLabel(f"{percent}%")
        percent_lbl.setObjectName("class_card_percent_lbl")
        percent_lbl.setProperty("tier", tier)
        attendance_row.addWidget(percent_lbl)
        card_layout.addLayout(attendance_row)

        bar = QProgressBar()
        bar.setObjectName("class_card_progress_bar")
        bar.setRange(0, 100)
        bar.setValue(max(0, min(100, percent)))
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        bar.setProperty("tier", tier)
        card_layout.addWidget(bar)

        status_row = QHBoxLayout()
        status_row.addWidget(make_tag_pill("INACTIVE" if cls.archived else "ACTIVE", "slate" if cls.archived else "green"))
        status_row.addStretch(1)
        card_layout.addLayout(status_row)

        detail = self._make_class_detail_panel(cls, attended, missed, total)
        card_layout.addWidget(self._make_expand_toggle(detail, "›  Properties", "⌄  Less"))

        outer_layout.addWidget(card)
        outer_layout.addWidget(detail)
        return outer

    def _make_class_list_row_widget(self, cls):
        """AttendU-style ClassListRow: a colored left accent bar, name and
        schedule caption, a class-code tag pill, attendance fraction + %,
        pin toggle, and an expandable Properties panel (My Classes page)."""
        compact = self.compact_view_cb.isChecked()
        attended, missed, total, percent = self._get_class_stats(cls)
        color = cls.color or class_tag_color(cls.class_code)
        tier = attendance_tier(percent, cls.attendance_policy)

        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 4)
        outer_layout.setSpacing(0)

        row = QFrame()
        row.setObjectName("class_row_widget")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 8, 14, 8)
        row_layout.setSpacing(12)

        accent_bar = QFrame()
        accent_bar.setFixedWidth(4)
        accent_bar.setStyleSheet(f"background-color: {color}; border: none;")
        row_layout.addWidget(accent_bar)

        select_cb = QCheckBox()
        select_cb.setToolTip("Select for bulk actions")
        select_cb.setChecked(cls.class_id in self.selected_class_ids)
        select_cb.toggled.connect(lambda checked, c=cls: self.toggle_class_selection(c, checked))
        row_layout.addWidget(select_cb)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        title_btn = QPushButton(cls.class_name)
        title_btn.setObjectName("class_row_name_btn")
        title_btn.setCursor(Qt.PointingHandCursor)
        title_btn.setToolTip(f"{cls.class_name} ({cls.class_code})")
        title_btn.clicked.connect(lambda _, c=cls: self.open_class_window(c))
        text_layout.addWidget(title_btn)
        caption_lbl = QLabel(f"{cls.class_code} · {self._format_schedule_caption(cls.schedule)}")
        caption_lbl.setObjectName("class_row_caption_lbl")
        caption_lbl.setVisible(not compact)
        text_layout.addWidget(caption_lbl)
        row_layout.addLayout(text_layout, 1)

        row_layout.addWidget(make_tag_pill(cls.class_code, class_tag_color_key(cls.class_code)))

        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(0)
        percent_lbl = QLabel(f"{percent}%")
        percent_lbl.setObjectName("class_card_percent_lbl")
        percent_lbl.setProperty("tier", tier)
        percent_lbl.setAlignment(Qt.AlignRight)
        stats_layout.addWidget(percent_lbl)
        fraction_lbl = QLabel(f"{attended}/{total}")
        fraction_lbl.setObjectName("class_row_caption_lbl")
        fraction_lbl.setAlignment(Qt.AlignRight)
        stats_layout.addWidget(fraction_lbl)
        row_layout.addLayout(stats_layout)

        pin_btn = QPushButton("★" if cls.pinned else "☆")
        pin_btn.setObjectName("card_icon_btn")
        pin_btn.setFixedSize(24, 24)
        pin_btn.setCursor(Qt.PointingHandCursor)
        pin_btn.setToolTip("Unpin class" if cls.pinned else "Pin class to the top")
        pin_btn.clicked.connect(lambda _, c=cls: self.toggle_pin_class(c))
        row_layout.addWidget(pin_btn)

        detail = self._make_class_detail_panel(cls, attended, missed, total)
        expand_btn = self._make_expand_toggle(detail, "›", "⌄")
        expand_btn.setFixedSize(24, 24)
        row_layout.addWidget(expand_btn)

        outer_layout.addWidget(row)
        outer_layout.addWidget(detail)
        return outer

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
        set_dynamic_property(unarchive_btn, "variant", "secondary")
        unarchive_btn.setCursor(Qt.PointingHandCursor)
        unarchive_btn.clicked.connect(lambda _, c=cls: self.unarchive_class(c))
        row_layout.addWidget(unarchive_btn)

        delete_btn = QPushButton("Delete Permanently")
        set_dynamic_property(delete_btn, "variant", "destructive")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(lambda _, c=cls: self.permanently_delete_class(c))
        row_layout.addWidget(delete_btn)

        return class_widget

    def toggle_class_selection(self, cls, checked):
        if checked:
            self.selected_class_ids.add(cls.class_id)
        else:
            self.selected_class_ids.discard(cls.class_id)

    def bulk_archive_selected(self):
        if not self.selected_class_ids:
            QMessageBox.information(self, "Nothing Selected", "Select one or more classes first.")
            return

        reply = QMessageBox.question(
            self, "Archive Selected Classes",
            f"Archive {len(self.selected_class_ids)} selected class(es)? They will be hidden "
            "from My Classes but their data is kept.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        failures = [
            class_id for class_id in self.selected_class_ids
            if not self.class_manager.archive_class(class_id)
        ]
        self.load_classes()
        if failures:
            QMessageBox.warning(self, "Partially Completed", f"Could not archive {len(failures)} class(es).")

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

    def show_statistics_for_class(self, cls):
        """Jump to Statistics pre-filtered to one class - used by Class
        Window's Info panel "View Full Statistics" action."""
        self.show_statistics()
        for i in range(self.statistics_class_combo.count()):
            item_cls = self.statistics_class_combo.itemData(i)
            if item_cls is not None and item_cls.class_id == cls.class_id:
                self.statistics_class_combo.setCurrentIndex(i)
                break

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

    _IMPORT_REQUIRED_COLUMNS = (
        "class_code", "class_name", "section", "attendance_policy",
        "late_threshold", "total_weeks", "total_hours", "weekly_hours",
    )

    def import_classes_from_spreadsheet(self):
        """Bulk-creates classes from a spreadsheet with one row per class
        (header row required); schedule isn't included, use Edit Class
        afterwards to set it."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Classes", "", "Spreadsheet Files (*.csv *.xlsx *.xls)"
        )
        if not file_path:
            return

        try:
            if file_path.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read spreadsheet:\n{e}")
            return

        missing = set(self._IMPORT_REQUIRED_COLUMNS) - set(df.columns)
        if missing:
            QMessageBox.critical(
                self, "Invalid Spreadsheet",
                f"Missing required column(s): {', '.join(sorted(missing))}",
            )
            return

        created = 0
        errors = []
        for _, row in df.iterrows():
            new_class = Class(
                class_code=str(row["class_code"]),
                class_name=str(row["class_name"]),
                instructor_id=self.user_id,
                section=str(row["section"]),
                attendance_policy=float(row["attendance_policy"]),
                late_threshold=int(row["late_threshold"]),
                total_weeks=int(row["total_weeks"]),
                total_hours=float(row["total_hours"]),
                weekly_hours=float(row["weekly_hours"]),
                schedule={},
            )
            try:
                self.class_manager.add_class(new_class)
                created += 1
            except ApiError as e:
                errors.append(f"{new_class.class_code}: {e}")

        self.load_classes()
        if errors:
            QMessageBox.warning(
                self, "Partially Completed",
                f"Created {created} class(es). Errors:\n" + "\n".join(errors),
            )
        else:
            QMessageBox.information(self, "Success", f"Created {created} class(es).")

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
        self._settings_password_toggle.setIcon(qta.icon(glyph, color="#6B6B76"))
        self._settings_password_toggle.setToolTip("Hide password" if checked else "Show password")

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
        self.sidebar_user_name_lbl.setText(f"{self.user.name} {self.user.surname}")
        self.sidebar_user_email_lbl.setText(self.user.email)
        self.sidebar_avatar_lbl.setPixmap(
            self._make_initials_avatar(self.user.name, self.user.surname, size=36)
        )
        self._set_profile_editing(False)
        QMessageBox.information(self, "Profile Updated", "Your profile has been updated successfully!")

    # --- Settings ---

    # --- Notifications ---

    def _flush_offline_queue_on_startup(self):
        flushed = self.class_manager.flush_offline_queue()
        if flushed:
            self.add_notification(
                f"Resubmitted {flushed} attendance record batch(es) saved offline earlier."
            )

    def _maybe_show_whats_new(self):
        if not should_show_whats_new():
            return
        bullet_list = "\n".join(f"• {item}" for item in CHANGELOG)
        QMessageBox.information(self, f"What's New in v{APP_VERSION}", bullet_list)
        save_last_seen_version(APP_VERSION)

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
        if self._last_chart_builder is not None:
            self._last_chart_builder()

    def toggle_list_density(self, checked):
        save_list_density("compact" if checked else "comfortable")
        self.load_classes()

    def _apply_translations(self):
        self.dashboard_btn.setText(t("dashboard"))
        self.my_classes_btn.setText(t("my_classes"))
        self.settings_btn.setText(t("settings"))
        self.statistics_btn.setText(t("statistics"))
        self.log_out_btn.setText(t("log_out"))
        self.create_new_class_btn.setText(t("create_new_class"))
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
            self.settings_answer_le, self.settings_answer_2_le,
            self.settings_current_password_for_question_le,
        ):
            line_edit.clear()
        self._clear_error(self.new_password_le, self.new_password_error_lbl)
        self._clear_error(self.confirm_new_password_le, self.confirm_new_password_error_lbl)
        self._clear_error(self.settings_answer_le, self.security_question_error_lbl)
        self.settings_security_question_combo.setCurrentIndex(0)
        if len(SECURITY_QUESTIONS) > 1:
            self.settings_security_question_2_combo.setCurrentIndex(1)
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

    def update_security_questions(self):
        current_password = self.settings_current_password_for_question_le.text()
        question_1 = self.settings_security_question_combo.currentText()
        answer_1 = self.settings_answer_le.text().strip()
        question_2 = self.settings_security_question_2_combo.currentText()
        answer_2 = self.settings_answer_2_le.text().strip()

        if not current_password:
            QMessageBox.warning(self, "Missing Information",
                                 "Please enter your current password to confirm.")
            return
        if not answer_1 or not answer_2:
            self._set_error(self.settings_answer_le, self.security_question_error_lbl,
                             "Please provide an answer to both security questions.")
            return
        if question_1 == question_2:
            self._set_error(self.settings_answer_le, self.security_question_error_lbl,
                             "Please choose two different security questions.")
            return
        self._clear_error(self.settings_answer_le, self.security_question_error_lbl)

        success, error = self.account_manager.update_security_questions(
            self.user_id, current_password, question_1, answer_1, question_2, answer_2
        )
        if not success:
            QMessageBox.critical(self, "Update Failed", error)
            return

        self._clear_settings_form()
        QMessageBox.information(self, "Security Questions Updated",
                                 "Your security questions have been updated.")

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
        clear_layout(self.search_results_layout)

        query = self.search_bar_le.text().strip().lower()
        classes = self.fetch_classes()
        matches = [c for c in classes if self._class_matches_query(c, query)] if query else classes

        if not matches:
            self.search_status_lbl.setText("No matching classes found.")
        else:
            self.search_status_lbl.setText(f"{len(matches)} class(es) found:")
            for cls in sorted(matches, key=self._class_sort_key):
                self.search_results_layout.addWidget(self._make_class_list_row_widget(cls))

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

        palette = active_palette()
        figure = Figure(figsize=(8, 4))
        figure.patch.set_facecolor(palette["bg_card"])
        axes_pie = figure.add_subplot(121)
        axes_trend = figure.add_subplot(122)
        axes_pie.set_facecolor(palette["bg_card"])
        axes_trend.set_facecolor(palette["bg_card"])
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
                colors=[palette["success"], palette["warning"], palette["error"]],
                textprops={"color": palette["text_primary"]},
            )
            axes_pie.set_title(f"Attendance for {cls.class_code}", color=palette["text_primary"])
            self._render_attendance_trend(axes_trend, cls)

        self.statistics_canvas = FigureCanvasQTAgg(figure)
        self.statistics_chart_layout.addWidget(self.statistics_canvas)
        self._last_chart_builder = self.render_statistics

    def show_class_comparison(self):
        """Bar chart comparing attendance rate across all of the
        instructor's classes side by side, instead of one class at a time."""
        classes = self.fetch_classes()
        if not classes:
            QMessageBox.information(self, "No Classes", "You have no classes to compare.")
            return

        if self.statistics_canvas is not None:
            self.statistics_chart_layout.removeWidget(self.statistics_canvas)
            self.statistics_canvas.deleteLater()
            self.statistics_canvas = None

        labels = []
        rates = []
        for cls in classes:
            try:
                stats = self.class_manager.get_statistics(cls.class_id)
            except ApiError:
                continue
            total = stats["present"] + stats["late"] + stats["absent"]
            if total == 0:
                continue
            rates.append((stats["present"] + stats["late"]) / total * 100)
            labels.append(cls.class_code)

        if not rates:
            self.statistics_empty_lbl.setText("No attendance data yet across your classes.")
            self.statistics_empty_lbl.setVisible(True)
            return
        self.statistics_empty_lbl.setVisible(False)

        palette = active_palette()
        figure = Figure(figsize=(8, 4))
        figure.patch.set_facecolor(palette["bg_card"])
        axes = figure.add_subplot(111)
        axes.set_facecolor(palette["bg_card"])
        axes.bar(labels, rates, color=palette["accent"])
        axes.set_ylim(0, 100)
        axes.set_ylabel("Attendance Rate (%)", color=palette["text_primary"])
        axes.set_title("Attendance Comparison Across Classes", color=palette["text_primary"])
        axes.tick_params(colors=palette["text_primary"])

        self.statistics_canvas = FigureCanvasQTAgg(figure)
        self.statistics_chart_layout.addWidget(self.statistics_canvas)
        self._last_chart_builder = self.show_class_comparison

    def show_attendance_heatmap(self):
        """Heatmap of attendance rate by day-of-week/time-slot for the
        currently selected class, averaged across all sessions that share
        the same day+slot combination."""
        cls = self.statistics_class_combo.currentData()
        if cls is None:
            QMessageBox.information(self, "No Class Selected", "Select a class first.")
            return

        try:
            table = self.class_manager.get_student_table(cls.class_id)
        except ApiError as e:
            QMessageBox.critical(self, "Server Error", str(e))
            return

        if self.statistics_canvas is not None:
            self.statistics_chart_layout.removeWidget(self.statistics_canvas)
            self.statistics_canvas.deleteLater()
            self.statistics_canvas = None

        fixed_columns = {"Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours"}
        session_columns = [c for c in table["columns"] if c not in fixed_columns]
        num_students = len(table["rows"])

        cell_totals = defaultdict(lambda: [0.0, 0])  # (day, time_slot) -> [rate_sum, count]
        if num_students:
            for col in session_columns:
                date_part, _, time_slot = col.partition(" - ")
                try:
                    day_name = datetime.strptime(date_part, "%d-%m-%Y").strftime("%A")
                except ValueError:
                    continue
                col_index = table["columns"].index(col)
                attended = sum(1 for row in table["rows"] if str(row[col_index]).startswith("1 "))
                rate = attended / num_students * 100
                totals = cell_totals[(day_name, time_slot)]
                totals[0] += rate
                totals[1] += 1

        if not cell_totals:
            self.statistics_empty_lbl.setText(f"No attendance recorded yet for {cls.class_code}.")
            self.statistics_empty_lbl.setVisible(True)
            return
        self.statistics_empty_lbl.setVisible(False)

        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        days_present = sorted({day for day, _ in cell_totals}, key=days_order.index)
        time_slots_present = sorted({slot for _, slot in cell_totals})

        grid = np.full((len(time_slots_present), len(days_present)), np.nan)
        for (day, slot), (rate_sum, count) in cell_totals.items():
            grid[time_slots_present.index(slot), days_present.index(day)] = rate_sum / count

        palette = active_palette()
        figure = Figure(figsize=(8, 4))
        figure.patch.set_facecolor(palette["bg_card"])
        axes = figure.add_subplot(111)
        axes.set_facecolor(palette["bg_card"])
        image = axes.imshow(grid, cmap="RdYlGn", vmin=0, vmax=100, aspect="auto")
        axes.set_xticks(range(len(days_present)))
        axes.set_xticklabels(days_present, color=palette["text_primary"])
        axes.set_yticks(range(len(time_slots_present)))
        axes.set_yticklabels(time_slots_present, color=palette["text_primary"])
        axes.set_title(f"Attendance Heatmap - {cls.class_code}", color=palette["text_primary"])
        figure.colorbar(image, ax=axes, label="Attendance Rate (%)")

        self.statistics_canvas = FigureCanvasQTAgg(figure)
        self.statistics_chart_layout.addWidget(self.statistics_canvas)
        self._last_chart_builder = self.show_attendance_heatmap

    def export_statistics_pdf(self):
        """Combines class policy, present/late/absent rates, the
        at-risk-students list, and the trend chart into a single-page PDF."""
        cls = self.statistics_class_combo.currentData()
        if cls is None:
            QMessageBox.information(self, "No Class Selected", "Select a class first.")
            return

        try:
            stats = self.class_manager.get_statistics(cls.class_id)
            table = self.class_manager.get_student_table(cls.class_id)
        except ApiError as e:
            QMessageBox.critical(self, "Server Error", str(e))
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Download PDF Report", f"{cls.class_code}_report.pdf", "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        at_risk_lines = self._at_risk_lines_for_report(cls, table)

        figure = Figure(figsize=(8.5, 11))
        gs = figure.add_gridspec(3, 2, height_ratios=[1, 2, 2])

        ax_text = figure.add_subplot(gs[0, :])
        ax_text.axis("off")
        summary = "\n".join([
            f"Attendance Report - {cls.class_name} ({cls.class_code})",
            f"Attendance Policy: {cls.attendance_policy}%   Late Threshold: {cls.late_threshold} min",
            f"Present: {stats['present']}   Late: {stats['late']}   Absent: {stats['absent']}",
        ])
        ax_text.text(0, 1, summary, va="top", fontsize=11)

        ax_pie = figure.add_subplot(gs[1, 0])
        values = [stats["present"], stats["late"], stats["absent"]]
        if sum(values):
            ax_pie.pie(
                values, labels=["Present", "Late", "Absent"], autopct="%1.1f%%",
                colors=[PALETTE["success"], PALETTE["warning"], PALETTE["error"]],
            )
        else:
            ax_pie.axis("off")

        ax_trend = figure.add_subplot(gs[1, 1])
        self._render_attendance_trend(ax_trend, cls, palette=PALETTE)

        ax_risk = figure.add_subplot(gs[2, :])
        ax_risk.axis("off")
        risk_text = "At-Risk Students:\n" + ("\n".join(at_risk_lines) if at_risk_lines else "None")
        ax_risk.text(0, 1, risk_text, va="top", fontsize=10)

        try:
            figure.savefig(file_path, format="pdf")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to write PDF:\n{e}")
            return

        QMessageBox.information(self, "Success", f"Report exported to:\n{file_path}")

    def _at_risk_lines_for_report(self, cls, table):
        if "Not Attended Hours" not in table["columns"]:
            return []

        failure = math.ceil(cls.total_hours * (100 - cls.attendance_policy) / 100)
        safe = failure * 0.5
        not_attended_idx = table["columns"].index("Not Attended Hours")
        name_idx = table["columns"].index("Student Name Surname")
        number_idx = table["columns"].index("Student Number")

        lines = []
        for row in table["rows"]:
            try:
                not_attended = float(row[not_attended_idx])
            except (ValueError, TypeError):
                continue
            if not_attended >= safe:
                label = "FAILING RISK" if not_attended >= failure else "at risk"
                lines.append(f"{row[name_idx]} ({row[number_idx]}) - {not_attended:g} missed - {label}")
        return lines

    def _render_attendance_trend(self, axes, cls, palette=None):
        """Plots the per-session attendance rate (% Present+Late) over
        time, reusing the same pivoted student table the roster page
        already fetches rather than adding a parallel server aggregate.

        `palette` defaults to the active (theme-aware) palette for on-screen
        rendering; export_statistics_pdf passes the light PALETTE explicitly
        so exported reports stay print-friendly regardless of app theme."""
        palette = palette or active_palette()
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

        axes.plot(range(1, len(rates) + 1), rates, marker="o", color=palette["accent"])
        axes.set_ylim(0, 100)
        axes.set_xlabel("Session", color=palette["text_primary"])
        axes.set_ylabel("Attendance Rate (%)", color=palette["text_primary"])
        axes.set_title("Attendance Trend", color=palette["text_primary"])
        axes.tick_params(colors=palette["text_primary"])

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
