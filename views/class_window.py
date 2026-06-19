from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView
from PyQt5.QtGui import QColor
from PyQt5 import uic
from pathlib import Path
import pandas as pd
import math

class ClassWindow(QMainWindow):
    def __init__(self, class_obj, main_window):
        super().__init__()
        uic.loadUi("ui/class_window.ui", self)

        self.class_obj = class_obj
        self.main_window = main_window  # Store reference to MainWindow for navigation
        self.failure = math.ceil((self.class_obj.total_hours) * (100 - self.class_obj.attendance_policy) / 100)
        self.safe = self.failure * 50 / 100
        self.display_class_details()
        self.setup_connections()
        self.load_student_list()
    

    def load_student_list(self):
        """Load student list from spreadsheet into table widget with colored status cells."""
        try:
            # Construct file path
            file_path = Path("data") / self.class_obj.instructor_id / self.class_obj.class_code / "student_list.xlsx"
            
            if not file_path.exists():
                QMessageBox.warning(self, "File Missing", "Student list spreadsheet not found!")
                return

            # Read Excel file
            df = pd.read_excel(file_path, engine='openpyxl')

            # Remove the "Card ID" column if it exists
            if "Card ID" in df.columns:
                df = df.drop(columns=["Card ID"])

            # Clear existing data
            self.student_list_tableWidget.clear()

            # Setup table dimensions
            self.student_list_tableWidget.setRowCount(df.shape[0])
            self.student_list_tableWidget.setColumnCount(df.shape[1])

            # Set headers
            self.student_list_tableWidget.setHorizontalHeaderLabels(df.columns)

            # Identify the "Not Attended Hours" column index
            not_attended_col_index = None
            if "Not Attended Hours" in df.columns:
                not_attended_col_index = df.columns.get_loc("Not Attended Hours")

            # Populate data with color conditions
            for row in range(df.shape[0]):
                for col in range(df.shape[1]):
                    value = str(df.iloc[row, col]).strip()  # Get cell value as string
                    item = QTableWidgetItem(value)

                    # Apply color based on attendance status
                    if value.lower() == "1 present":
                        item.setBackground(QColor(144, 238, 144))  # Light green
                    elif value.lower() == "1 late":
                        item.setBackground(QColor(255, 223, 128))  # Light yellow

                    # Apply color for "Not Attended Hours" column
                    if col == not_attended_col_index:
                        try:
                            num_value = float(value)  # Convert to number for comparison
                            if num_value < int(self.safe):
                                item.setBackground(QColor(144, 238, 144))  # Light green
                            elif int(self.safe) <= num_value < int(self.failure):
                                item.setBackground(QColor(255, 223, 128))  # Light yellow
                            elif num_value >= int(self.failure):
                                item.setBackground(QColor(255, 150, 150))  # Light red
                        except ValueError:
                            pass  # Ignore non-numeric values

                    self.student_list_tableWidget.setItem(row, col, item)

            # Stretch columns to fill table width
                # Conditional resizing based on the number of columns
            if self.student_list_tableWidget.columnCount() <= 10:
                # Stretch columns to fill table width
                self.student_list_tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            else:
                # Resize columns to fit content and enable horizontal scrolling
                self.student_list_tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
                self.student_list_tableWidget.setHorizontalScrollMode(QHeaderView.ScrollPerPixel)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load student list:\n{str(e)}")
            
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
        self.take_attendance_page = TakeAttendance(self.class_obj, self)
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
