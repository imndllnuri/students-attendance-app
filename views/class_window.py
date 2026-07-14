import math

import pandas as pd
import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHeaderView, QMainWindow, QMessageBox, QTableWidgetItem

from services.api_client import ApiError


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
        self.back_to_my_classes_btn.setIcon(qta.icon("fa5s.arrow-left", color="#4F46E5"))
        self.class_settings_btn.setIcon(qta.icon("fa5s.cog", color="#4F46E5"))

    def load_student_list(self):
        """Load student list + attendance history from the server into the table widget."""
        try:
            table = self.class_manager.get_student_table(self.class_obj.class_id)
        except ApiError as e:
            QMessageBox.critical(self, "Server Error", f"Failed to load student list:\n{e}")
            return

        df = pd.DataFrame(table["rows"], columns=table["columns"])

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
                    item.setBackground(QColor(144, 238, 144))
                elif value.lower() == "1 late":
                    item.setBackground(QColor(255, 223, 128))

                if col == not_attended_col_index:
                    try:
                        num_value = float(value)
                        if num_value < int(self.safe):
                            item.setBackground(QColor(144, 238, 144))
                        elif int(self.safe) <= num_value < int(self.failure):
                            item.setBackground(QColor(255, 223, 128))
                        elif num_value >= int(self.failure):
                            item.setBackground(QColor(255, 150, 150))
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
        self.class_name_lbl.setText(f"Class Name: {self.class_obj.class_name}")
        self.class_code_lbl.setText(f"Class Code: {self.class_obj.class_code}")
        self.class_section_lbl.setText(f"Section: {self.class_obj.section}")
        self.attendance_policy_lbl.setText(f"Attendance Policy: {self.class_obj.attendance_policy}")
        self.late_threshold_lbl.setText(f"Late Threshold: {self.class_obj.late_threshold} minutes")
        self.number_of_weeks_lbl.setText(f"Weeks: {self.class_obj.total_weeks}")
        self.total_hours_lbl.setText(f"Total Hours: {self.class_obj.total_hours}")
        self.weekly_hours_lbl.setText(f"Weekly Hours: {self.class_obj.weekly_hours}")
        formatted_schedule = self.format_schedule(self.class_obj.schedule)
        self.schedule_lbl.setText(f"Schedule:\n{formatted_schedule}")

    def setup_connections(self):
        self.back_to_my_classes_btn.clicked.connect(self.return_to_main_window)
        self.refresh_student_list_btn.clicked.connect(self.load_student_list)
        self.take_attendance_btn.clicked.connect(self.attendance_page_show)

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
