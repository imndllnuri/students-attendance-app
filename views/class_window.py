import logging
import math

import pandas as pd
import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtWidgets import QHeaderView, QInputDialog, QMainWindow, QMessageBox, QTableWidgetItem

from services.api_client import ApiError
from shared.palette import qcolor

logger = logging.getLogger(__name__)


class ClassWindow(QMainWindow):
    def __init__(self, class_obj, main_window, class_manager):
        super().__init__()
        uic.loadUi("ui/class_window.ui", self)

        self.class_obj = class_obj
        self.main_window = main_window
        self.class_manager = class_manager
        self.failure = math.ceil((self.class_obj.total_hours) * (100 - self.class_obj.attendance_policy) / 100)
        self.safe = self.failure * 50 / 100
        self.student_list_tableWidget.setAlternatingRowColors(True)
        self._setup_icons()
        self.display_class_details()
        self.setup_connections()
        self.load_student_list()

    def _setup_icons(self):
        self.take_attendance_btn.setIcon(qta.icon("fa5s.clipboard-check", color="white"))
        self.refresh_student_list_btn.setIcon(qta.icon("fa5s.sync-alt", color="#4F46E5"))
        self.refresh_student_list_btn.setToolTip("Refresh roster")
        self.refresh_student_list_btn.setAccessibleName("Refresh roster")
        self.back_to_my_classes_btn.setIcon(qta.icon("fa5s.arrow-left", color="#4F46E5"))
        self.class_settings_btn.setIcon(qta.icon("fa5s.cog", color="#4F46E5"))

    def _show_roster_status(self, message, show_retry):
        self.roster_status_lbl.setText(message)
        self.roster_retry_btn.setVisible(show_retry)
        self.roster_status_widget.setVisible(True)
        self.student_list_tableWidget.setVisible(False)

    def load_student_list(self):
        """Load student list + attendance history from the server into the table widget."""
        try:
            table = self.class_manager.get_student_table(self.class_obj.class_id)
        except ApiError as e:
            logger.warning("Failed to load student list for class %s: %s", self.class_obj.class_id, e)
            QMessageBox.critical(self, "Server Error", f"Failed to load student list:\n{e}")
            self._show_roster_status(f"Couldn't load the roster: {e}", show_retry=True)
            return

        df = pd.DataFrame(table["rows"], columns=table["columns"])

        if df.shape[0] == 0:
            self._show_roster_status("No students in this class's roster yet.", show_retry=False)
            return

        self.roster_status_widget.setVisible(False)
        self.student_list_tableWidget.setVisible(True)

        self.student_list_tableWidget.clear()
        self.student_list_tableWidget.setRowCount(df.shape[0])
        self.student_list_tableWidget.setColumnCount(df.shape[1])
        self.student_list_tableWidget.setHorizontalHeaderLabels(df.columns)

        not_attended_col_index = None
        if "Not Attended Hours" in df.columns:
            not_attended_col_index = df.columns.get_loc("Not Attended Hours")

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                value = str(df.iloc[row, col]).strip()
                item = QTableWidgetItem(value)

                if value.lower() == "1 present":
                    item.setBackground(qcolor("success_tint"))
                elif value.lower() == "1 late":
                    item.setBackground(qcolor("warning_tint"))

                if col == not_attended_col_index:
                    try:
                        num_value = float(value)
                        if num_value < int(self.safe):
                            item.setBackground(qcolor("success_tint"))
                        elif int(self.safe) <= num_value < int(self.failure):
                            item.setBackground(qcolor("warning_tint"))
                        elif num_value >= int(self.failure):
                            item.setBackground(qcolor("error_tint"))
                    except ValueError:
                        pass

                self.student_list_tableWidget.setItem(row, col, item)

        if self.student_list_tableWidget.columnCount() <= 10:
            self.student_list_tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        else:
            self.student_list_tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.student_list_tableWidget.setHorizontalScrollMode(QHeaderView.ScrollPerPixel)

    def display_class_details(self):
        """Displays class details in the UI."""
        self.class_name_header_lbl.setText(self.class_obj.class_name)
        self.class_code_lbl.setText(f"{self.class_obj.class_code} · Section {self.class_obj.section}")
        self.attendance_policy_lbl.setText(f"Attendance Policy: {self.class_obj.attendance_policy}%")
        self.late_threshold_lbl.setText(f"Late Threshold: {self.class_obj.late_threshold} minutes")
        self.number_of_weeks_lbl.setText(f"Weeks: {self.class_obj.total_weeks}")
        self.total_hours_lbl.setText(f"Total Hours: {self.class_obj.total_hours}")
        self.weekly_hours_lbl.setText(f"Weekly Hours: {self.class_obj.weekly_hours}")
        formatted_schedule = self.format_schedule(self.class_obj.schedule)
        self.schedule_lbl.setText(f"Schedule:\n{formatted_schedule}")

    def setup_connections(self):
        self.back_to_my_classes_btn.clicked.connect(self.return_to_main_window)
        self.refresh_student_list_btn.clicked.connect(self.load_student_list)
        self.roster_retry_btn.clicked.connect(self.load_student_list)
        self.take_attendance_btn.clicked.connect(self.attendance_page_show)
        self.class_settings_btn.clicked.connect(self.open_edit_class_window)
        self.add_student_btn.clicked.connect(self.add_roster_student)
        self.remove_selected_student_btn.clicked.connect(self.remove_selected_student)
        self.student_list_tableWidget.cellDoubleClicked.connect(self.correct_attendance_cell)

    _FIRST_SESSION_COLUMN = 4  # Student Number, Name Surname, Not Attended, Attended

    def correct_attendance_cell(self, row, col):
        """Double-clicking a session cell in the roster table lets the
        instructor correct a past attendance record (e.g. it was marked
        wrong during the live session)."""
        if col < self._FIRST_SESSION_COLUMN:
            return
        header_item = self.student_list_tableWidget.horizontalHeaderItem(col)
        if header_item is None or " - " not in header_item.text():
            return
        date, time_slot = header_item.text().split(" - ", 1)

        student_number_item = self.student_list_tableWidget.item(row, 0)
        student_name_item = self.student_list_tableWidget.item(row, 1)
        if student_number_item is None or student_name_item is None:
            return
        student_number = student_number_item.text()
        student_name = student_name_item.text()

        current_cell = self.student_list_tableWidget.item(row, col)
        current_text = current_cell.text() if current_cell else "0"
        current_status = current_text.split(" ", 1)[1] if current_text.startswith("1 ") else "Absent"

        statuses = ["Present", "Late", "Absent"]
        default_index = statuses.index(current_status) if current_status in statuses else 0
        new_status, ok = QInputDialog.getItem(
            self, "Correct Attendance",
            f"{student_name} - {date} {time_slot}:",
            statuses, default_index, False,
        )
        if not ok or new_status == current_status:
            return

        try:
            roster = self.class_manager.get_roster(self.class_obj.class_id)
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Could not load roster:\n{e}")
            return
        match = next((s for s in roster if s["student_number"] == student_number), None)
        if match is None:
            QMessageBox.critical(self, "Error", "Could not find that student in the roster.")
            return

        try:
            self.class_manager.correct_attendance(
                self.class_obj.class_id, match["student_id"], date, time_slot, new_status
            )
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Could not update attendance:\n{e}")
            return

        self.load_student_list()

    def add_roster_student(self):
        student_number = self.new_student_number_le.text().strip()
        name_surname = self.new_student_name_le.text().strip()
        if not student_number or not name_surname:
            QMessageBox.warning(self, "Missing Field", "Student number and name are required.")
            return

        try:
            self.class_manager.add_student(self.class_obj.class_id, student_number, name_surname)
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Could not add student:\n{e}")
            return

        self.new_student_number_le.clear()
        self.new_student_name_le.clear()
        self.load_student_list()

    def remove_selected_student(self):
        row = self.student_list_tableWidget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Select a student row to remove first.")
            return
        student_number = self.student_list_tableWidget.item(row, 0).text()

        try:
            roster = self.class_manager.get_roster(self.class_obj.class_id)
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Could not load roster:\n{e}")
            return

        match = next((s for s in roster if s["student_number"] == student_number), None)
        if match is None:
            QMessageBox.critical(self, "Error", "Could not find that student in the roster.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove {match['name_surname']} ({match['student_number']}) from the roster? "
            "This also deletes their attendance history for this class.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        if self.class_manager.remove_student(match["student_id"]):
            self.load_student_list()
        else:
            QMessageBox.critical(self, "Error", "Could not remove that student.")

    def open_edit_class_window(self):
        from views.add_new_class_window import AddNewClassWindow
        self.edit_class_window = AddNewClassWindow(
            self.class_obj.instructor_id, existing_class=self.class_obj
        )
        self.edit_class_window.class_created.connect(self._reload_after_edit)
        self.edit_class_window.show()

    def _reload_after_edit(self):
        classes = self.class_manager.load_classes_for_instructor(
            self.class_obj.instructor_id, include_archived=True
        )
        updated = next((c for c in classes if c.class_id == self.class_obj.class_id), None)
        if updated is not None:
            self.class_obj = updated
            self.failure = math.ceil(self.class_obj.total_hours * (100 - self.class_obj.attendance_policy) / 100)
            self.safe = self.failure * 50 / 100
            self.display_class_details()
        self.main_window.load_classes()

    def attendance_page_show(self):
        from views.take_attendance_window import TakeAttendance
        self.take_attendance_page = TakeAttendance(self.class_obj, self, self.class_manager)
        self.take_attendance_page.show()

    def format_schedule(self, schedule):
        """Formats the schedule dictionary into a readable string."""
        schedule_str = []
        for day, slots in schedule.items():
            slot_strs = [
                f"{slot.start_time.toString('HH:mm')} - {slot.end_time.toString('HH:mm')}"
                for slot in slots if slot.selected
            ]
            if slot_strs:
                schedule_str.append(f"{day}: {', '.join(slot_strs)}")
        return "\n".join(schedule_str) if schedule_str else "No schedule set"

    def return_to_main_window(self):
        """Returns to 'My Classes' view in the main window."""
        self.main_window.stackedWidget.setCurrentIndex(0)
        self.close()
