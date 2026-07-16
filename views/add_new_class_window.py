import qtawesome as qta
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QColorDialog,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidgetItem,
    QTimeEdit,
    QWidget,
)
from PyQt5 import uic
import pandas as pd

from models.classes import Class, ClassManager, ScheduleSlot
from services.api_client import ApiError
from shared.qt_style import set_dynamic_property

ROSTER_STEP = 2

_STEP_TITLES = ("Create New Class", "Edit Class", "Duplicate Class")


class AddNewClassWindow(QDialog):
    class_created = pyqtSignal()
    roster_load_failed = pyqtSignal(str)

    def __init__(self, user_id, existing_class=None, duplicate_from=None):
        super().__init__()
        uic.loadUi("ui/add_new_class.ui", self)
        for col, stretch in enumerate((0, 1)):
            self.gridLayout.setColumnStretch(col, stretch)
        self.user_id = user_id
        self.class_manager = ClassManager()
        self.students = []
        self.roster = []
        self.existing_class = existing_class
        self.selected_color = None
        self._current_step = 0
        self._show_roster_step = existing_class is not None
        self._step_labels = [
            self.step_dot_1_lbl, self.step_dot_2_lbl, self.step_dot_3_lbl, self.step_dot_4_lbl,
        ]

        self.spreadsheet_file_btn.clicked.connect(self.load_spreadsheet)
        self.create_class_btn.clicked.connect(self.create_class)
        self.choose_color_btn.clicked.connect(self.choose_class_color)
        self.reset_color_btn.clicked.connect(self.reset_class_color)
        self.wizard_next_btn.clicked.connect(self.go_to_next_step)
        self.wizard_back_btn.clicked.connect(self.go_to_previous_step)
        self.archive_class_btn.clicked.connect(self.archive_current_class)
        self.delete_class_btn.clicked.connect(self.delete_current_class)
        self.wizard_add_student_btn.clicked.connect(self.add_wizard_roster_student)
        self.wizard_remove_selected_student_btn.clicked.connect(self.remove_wizard_roster_student)
        self.wizard_roster_tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for day in days:
            add_btn = getattr(self, f"add_slot_{day.lower()}_btn")
            remove_btn = getattr(self, f"remove_slot_{day.lower()}_btn")
            add_btn.clicked.connect(lambda _, d=day: self.add_time_slot(d))
            remove_btn.clicked.connect(lambda _, d=day: self.remove_time_slot(d))
            add_btn.setIcon(qta.icon("fa5s.plus", color="#2F5CF0"))
            remove_btn.setIcon(qta.icon("fa5s.minus", color="#DC2626"))
            set_dynamic_property(add_btn, "variant", "secondary")
            set_dynamic_property(remove_btn, "variant", "destructive")

        set_dynamic_property(self.choose_color_btn, "variant", "secondary")
        set_dynamic_property(self.reset_color_btn, "variant", "ghost")
        set_dynamic_property(self.spreadsheet_file_btn, "variant", "secondary")
        set_dynamic_property(self.create_class_btn, "variant", "primary")
        set_dynamic_property(self.wizard_next_btn, "variant", "primary")
        set_dynamic_property(self.wizard_back_btn, "variant", "ghost")
        set_dynamic_property(self.archive_class_btn, "variant", "secondary")
        set_dynamic_property(self.delete_class_btn, "variant", "destructive")
        set_dynamic_property(self.wizard_add_student_btn, "variant", "secondary")
        set_dynamic_property(self.wizard_remove_selected_student_btn, "variant", "destructive")
        self._update_color_swatch()

        self.spreadsheet_file_btn.setIcon(qta.icon("fa5s.file-upload", color="#2F5CF0"))
        self.create_class_btn.setIcon(qta.icon("fa5s.check", color="white"))

        self.time_slots = {day: [] for day in days}

        # Danger Zone and the Roster step only make sense once a class
        # already exists - a brand-new class has no class_id yet to add
        # students against, and that's what the Schedule step's spreadsheet
        # upload is for instead.
        self.danger_zone_card.setVisible(existing_class is not None)
        self.step_dot_3_lbl.setVisible(self._show_roster_step)

        if existing_class is not None:
            self._prefill_for_edit(existing_class)
        elif duplicate_from is not None:
            self._prefill_for_duplicate(duplicate_from)

        self._go_to_step(0)

    def _step_sequence(self):
        """The reachable step indices, in order - skips the Roster step for
        a brand-new class (see the comment in __init__)."""
        all_steps = range(self.wizard_stack.count())
        if self._show_roster_step:
            return list(all_steps)
        return [step for step in all_steps if step != ROSTER_STEP]

    def _go_to_step(self, step):
        self._current_step = step
        self.wizard_stack.setCurrentIndex(step)
        for index, label in enumerate(self._step_labels):
            set_dynamic_property(label, "active", index == step)

        sequence = self._step_sequence()
        self.wizard_back_btn.setVisible(step != sequence[0])
        is_last_step = step == sequence[-1]
        self.wizard_next_btn.setVisible(not is_last_step)
        self.create_class_btn.setVisible(is_last_step)

        if step == ROSTER_STEP:
            self._load_wizard_roster()

    def go_to_next_step(self):
        sequence = self._step_sequence()
        position = sequence.index(self._current_step)
        self._go_to_step(sequence[min(position + 1, len(sequence) - 1)])

    def go_to_previous_step(self):
        sequence = self._step_sequence()
        position = sequence.index(self._current_step)
        self._go_to_step(sequence[max(position - 1, 0)])

    def archive_current_class(self):
        reply = QMessageBox.question(
            self, "Archive Class",
            f"Archive {self.existing_class.class_name}? It will be hidden from your active "
            "class list, but its data and history are kept.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        if self.class_manager.archive_class(self.existing_class.class_id):
            self.class_created.emit()
            self.close()
        else:
            QMessageBox.critical(self, "Error", "Could not archive this class.")

    def delete_current_class(self):
        typed_name, ok = QInputDialog.getText(
            self, "Delete Class Permanently",
            "This cannot be undone - all attendance history for "
            f"{self.existing_class.class_name} will be lost.\n\n"
            f"Type the class name ({self.existing_class.class_name}) to confirm:",
            QLineEdit.Normal,
        )
        if not ok:
            return
        if typed_name.strip() != self.existing_class.class_name:
            QMessageBox.warning(self, "Names Didn't Match", "Class not deleted.")
            return
        if self.class_manager.delete_class(self.existing_class.class_id):
            self.class_created.emit()
            self.close()
        else:
            QMessageBox.critical(self, "Error", "Could not delete this class.")

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
        from shared.palette import PALETTE

        color = self.selected_color or PALETTE["border_strong"]
        self.class_color_swatch.setStyleSheet(f"background-color: {color}; border-radius: 6px;")

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
        title = f"Edit Class - {cls.class_code}"
        self.setWindowTitle(title)
        self.wizard_title_lbl.setText(title)
        self.create_class_btn.setText("Save Changes")
        self.class_code_le.setText(cls.class_code)
        self.class_code_le.setReadOnly(True)
        self._prefill_fields(cls)

        # New students are added one at a time on the Roster step instead
        # (see _load_wizard_roster) - the spreadsheet bulk-upload only makes
        # sense once, when a class doesn't have a roster yet.
        self.spreadsheet_row_widget.setVisible(False)

    def _prefill_for_duplicate(self, cls):
        title = f"Duplicate Class - Based on {cls.class_code}"
        self.setWindowTitle(title)
        self.wizard_title_lbl.setText(title)
        self._prefill_fields(cls)
        # class_code_le is left blank/editable: the copy needs its own unique code.

    def _load_wizard_roster(self):
        try:
            self.roster = self.class_manager.get_roster(self.existing_class.class_id)
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Could not load roster:\n{e}")
            self.roster = []
        self._populate_wizard_roster_table()

    def _populate_wizard_roster_table(self):
        table = self.wizard_roster_tableWidget
        table.setRowCount(len(self.roster))
        for row, student in enumerate(self.roster):
            number_item = QTableWidgetItem(student["student_number"])
            number_item.setData(Qt.UserRole, student["student_id"])
            table.setItem(row, 0, number_item)
            table.setItem(row, 1, QTableWidgetItem(student["name_surname"]))

    def add_wizard_roster_student(self):
        student_number = self.wizard_new_student_number_le.text().strip()
        name_surname = self.wizard_new_student_name_le.text().strip()
        if not student_number or not name_surname:
            QMessageBox.warning(self, "Missing Field", "Student number and name are required.")
            return

        try:
            self.class_manager.add_student(self.existing_class.class_id, student_number, name_surname)
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Could not add student:\n{e}")
            return

        self.wizard_new_student_number_le.clear()
        self.wizard_new_student_name_le.clear()
        self._load_wizard_roster()

    def remove_wizard_roster_student(self):
        row = self.wizard_roster_tableWidget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Select a student row to remove first.")
            return
        student = self.roster[row]

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove {student['name_surname']} ({student['student_number']}) from the roster? "
            "This also deletes their attendance history for this class.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        if self.class_manager.remove_student(student["student_id"]):
            self._load_wizard_roster()
        else:
            QMessageBox.critical(self, "Error", "Could not remove that student.")

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
