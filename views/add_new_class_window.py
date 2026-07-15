import qtawesome as qta
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QColorDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTimeEdit,
    QWidget,
)
from PyQt5 import uic
import pandas as pd

from models.classes import Class, ClassManager, ScheduleSlot
from services.api_client import ApiError


class AddNewClassWindow(QWidget):
    class_created = pyqtSignal()
    roster_load_failed = pyqtSignal(str)

    def __init__(self, user_id, existing_class=None, duplicate_from=None):
        super().__init__()
        uic.loadUi("ui/add_new_class.ui", self)
        for col, stretch in enumerate((0, 1, 0, 0, 1)):
            self.gridLayout.setColumnStretch(col, stretch)
        self.user_id = user_id
        self.class_manager = ClassManager()
        self.students = []
        self.existing_class = existing_class
        self.selected_color = None

        self.spreadsheet_file_btn.clicked.connect(self.load_spreadsheet)
        self.create_class_btn.clicked.connect(self.create_class)
        self.choose_color_btn.clicked.connect(self.choose_class_color)
        self.reset_color_btn.clicked.connect(self.reset_class_color)

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for day in days:
            add_btn = getattr(self, f"add_slot_{day.lower()}_btn")
            remove_btn = getattr(self, f"remove_slot_{day.lower()}_btn")
            add_btn.clicked.connect(lambda _, d=day: self.add_time_slot(d))
            remove_btn.clicked.connect(lambda _, d=day: self.remove_time_slot(d))
            add_btn.setIcon(qta.icon("fa5s.plus", color="#4F46E5"))
            remove_btn.setIcon(qta.icon("fa5s.minus", color="white"))

        self.spreadsheet_file_btn.setIcon(qta.icon("fa5s.file-upload", color="#4F46E5"))
        self.create_class_btn.setIcon(qta.icon("fa5s.check", color="white"))

        self.time_slots = {day: [] for day in days}

        if existing_class is not None:
            self._prefill_for_edit(existing_class)
        elif duplicate_from is not None:
            self._prefill_for_duplicate(duplicate_from)

    def choose_class_color(self):
        initial = QColor(self.selected_color) if self.selected_color else QColor("#4F46E5")
        color = QColorDialog.getColor(initial, self, "Choose Class Color")
        if not color.isValid():
            return
        self.selected_color = color.name()
        self._update_color_swatch()

    def reset_class_color(self):
        self.selected_color = None
        self._update_color_swatch()

    def _update_color_swatch(self):
        if self.selected_color:
            self.choose_color_btn.setStyleSheet(
                f"background-color: {self.selected_color}; color: white;"
            )
        else:
            self.choose_color_btn.setStyleSheet("")

    def _prefill_fields(self, cls):
        self.class_name_le.setText(cls.class_name)
        self.class_section_le.setText(cls.section)
        self.attendance_policy_le.setText(str(cls.attendance_policy))
        self.late_threshold_le.setText(str(cls.late_threshold))
        self.number_of_weeks_le.setText(str(cls.total_weeks))
        self.total_hours_le.setText(str(cls.total_hours))
        self.weekly_hours_le.setText(str(cls.weekly_hours))
        self.selected_color = cls.color
        self._update_color_swatch()

        for day, slots in cls.schedule.items():
            if not any(slot.selected for slot in slots):
                continue
            checkbox = getattr(self, f"{day.lower()}_cb", None)
            if checkbox is None:
                continue
            checkbox.setChecked(True)
            for slot in slots:
                if not slot.selected:
                    continue
                self.add_time_slot(day)
                start_edit, end_edit = self.time_slots[day][-1]
                start_edit.setTime(slot.start_time)
                end_edit.setTime(slot.end_time)

    def _prefill_for_edit(self, cls):
        self.setWindowTitle(f"Edit Class - {cls.class_code}")
        self.create_class_btn.setText("Save Changes")
        self.class_code_le.setText(cls.class_code)
        self.class_code_le.setReadOnly(True)
        self._prefill_fields(cls)

        # Roster edits are handled separately (add/remove individual students);
        # this dialog only edits schedule/policy fields when editing a class.
        self.spreadsheet_lbl.setVisible(False)
        self.spreadsheet_file_btn.setVisible(False)

    def _prefill_for_duplicate(self, cls):
        self.setWindowTitle(f"Duplicate Class - Based on {cls.class_code}")
        self._prefill_fields(cls)
        # class_code_le is left blank/editable: the copy needs its own unique code.

    def add_time_slot(self, day):
        container = self.findChild(QWidget, f"{day.lower()}GroupBox")
        layout = container.layout()

        time_slot_layout = QHBoxLayout()
        start_edit = QTimeEdit()
        start_edit.setDisplayFormat("HH:mm")
        end_edit = QTimeEdit()
        end_edit.setDisplayFormat("HH:mm")

        time_slot_layout.addWidget(QLabel("Start:"))
        time_slot_layout.addWidget(start_edit)
        time_slot_layout.addWidget(QLabel("End:"))
        time_slot_layout.addWidget(end_edit)
        layout.addLayout(time_slot_layout)

        self.time_slots[day].append((start_edit, end_edit))

    def remove_time_slot(self, day):
        group_box = getattr(self, f"{day.lower()}GroupBox")
        main_layout = group_box.layout()

        if not self.time_slots[day]:
            return

        self.time_slots[day].pop()

        for i in reversed(range(main_layout.count())):
            item = main_layout.itemAt(i)
            if isinstance(item, QHBoxLayout):
                layout = main_layout.takeAt(i).layout()
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                break

    def _collect_schedule(self):
        schedule = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for day in days:
            checkbox = getattr(self, f"{day.lower()}_cb")
            if checkbox.isChecked():
                slots = []
                for start_edit, end_edit in self.time_slots[day]:
                    slots.append(ScheduleSlot(
                        day=day,
                        start_time=start_edit.time(),
                        end_time=end_edit.time(),
                        selected=True
                    ))
                schedule[day] = slots
        return schedule

    def create_class(self):
        if not self.validate_inputs():
            return

        schedule = self._collect_schedule()

        if self.existing_class is not None:
            self._save_edits(schedule)
            return

        new_class = Class(
            class_code=self.class_code_le.text(),
            class_name=self.class_name_le.text(),
            instructor_id=self.user_id,
            section=self.class_section_le.text(),
            attendance_policy=float(self.attendance_policy_le.text()),
            late_threshold=int(self.late_threshold_le.text()),
            total_weeks=int(self.number_of_weeks_le.text()),
            total_hours=float(self.total_hours_le.text()),
            weekly_hours=float(self.weekly_hours_le.text()),
            schedule=schedule,
            students=self.students,
            color=self.selected_color,
        )

        try:
            self.class_manager.add_class(new_class)
        except ApiError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        QMessageBox.information(self, "Success", "Class created successfully!")
        self.class_created.emit()
        self.close()

    def _save_edits(self, schedule):
        fields = {
            "class_name": self.class_name_le.text(),
            "section": self.class_section_le.text(),
            "attendance_policy": float(self.attendance_policy_le.text()),
            "late_threshold": int(self.late_threshold_le.text()),
            "total_weeks": int(self.number_of_weeks_le.text()),
            "total_hours": float(self.total_hours_le.text()),
            "weekly_hours": float(self.weekly_hours_le.text()),
            "color": self.selected_color,
            "schedule": {
                day: [
                    {
                        "start_time": slot.start_time.toString("HH:mm"),
                        "end_time": slot.end_time.toString("HH:mm"),
                        "selected": slot.selected,
                    }
                    for slot in slots
                ]
                for day, slots in schedule.items()
            },
        }

        try:
            self.class_manager.update_class(self.existing_class.class_id, fields)
        except ApiError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        QMessageBox.information(self, "Success", "Class updated successfully!")
        self.class_created.emit()
        self.close()

    def load_spreadsheet(self):
        """Parse the student spreadsheet into memory; sent to the server on class creation."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Student Spreadsheet", "",
            "Spreadsheet Files (*.csv *.xlsx *.ods *.xls)"
        )
        if not file_path:
            return

        try:
            if file_path.endswith(".xls"):
                df = pd.read_excel(file_path, skiprows=8, header=None, engine="xlrd")
            else:
                df = pd.read_csv(file_path, skiprows=8, header=None)

            students = []
            for _, row in df.iterrows():
                student_number = f"{row[2]}{row[3]}".strip().replace(".0nan", "").replace("nannan", "")
                name_parts = [str(row[col]) for col in [4, 5, 6] if not pd.isna(row[col])]
                full_name = " ".join(name_parts).replace("nan", "").strip()

                if student_number and full_name:
                    students.append({
                        "student_number": student_number,
                        "name_surname": full_name,
                    })

            duplicates = self._find_duplicate_student_numbers(students)
            if duplicates:
                reply = QMessageBox.warning(
                    self, "Duplicate Student Numbers",
                    "These student numbers appear more than once in the spreadsheet: "
                    f"{', '.join(sorted(duplicates))}. Load anyway?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return

            self.students = students
            QMessageBox.information(self, "Success",
                                  f"Loaded {len(students)} students. They'll be saved with the class.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Spreadsheet processing failed: {str(e)}")
            self.roster_load_failed.emit(str(e))

    def _find_duplicate_student_numbers(self, students):
        seen = set()
        duplicates = set()
        for student in students:
            number = student["student_number"]
            if number in seen:
                duplicates.add(number)
            seen.add(number)
        return duplicates

    def validate_inputs(self):
        required_fields = [
            (self.class_code_le.text(), "Class Code"),
            (self.class_name_le.text(), "Class Name"),
            (self.class_section_le.text(), "Class Section"),
            (self.attendance_policy_le.text(), "Attendance Policy"),
            (self.late_threshold_le.text(), "Late Threshold"),
            (self.number_of_weeks_le.text(), "Number of Weeks"),
            (self.total_hours_le.text(), "Total Hours"),
            (self.weekly_hours_le.text(), "Weekly Hours")
        ]

        for value, field_name in required_fields:
            if not value:
                QMessageBox.warning(self, "Missing Field", f"{field_name} is required!")
                return False

        try:
            float(self.attendance_policy_le.text())
            int(self.late_threshold_le.text())
            int(self.number_of_weeks_le.text())
            float(self.total_hours_le.text())
            float(self.weekly_hours_le.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers in numeric fields")
            return False

        return True
