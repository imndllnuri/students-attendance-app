from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox, QTimeEdit, QCheckBox, QLabel, QHBoxLayout
from PyQt5 import uic
from models.classes import Class, ClassManager, ScheduleSlot
import pandas as pd
from pathlib import Path

class AddNewClassWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        uic.loadUi("ui/add_new_class.ui", self)
        self.user_id = user_id
        self.class_manager = ClassManager()
        self.spreadsheet_path = ""

        # Connect buttons
        self.spreadsheet_file_btn.clicked.connect(self.load_spreadsheet)
        self.create_class_btn.clicked.connect(self.create_class)

        # Connect add and remove buttons
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for day in days:
            add_btn = getattr(self, f"add_slot_{day.lower()}_btn")
            remove_btn = getattr(self, f"remove_slot_{day.lower()}_btn")
            add_btn.clicked.connect(lambda _, d=day: self.add_time_slot(d))
            remove_btn.clicked.connect(lambda _, d=day: self.remove_time_slot(d))

        # Initialize time_slots to store QTimeEdit pairs
        self.time_slots = {day: [] for day in days}

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

        # Store QTimeEdit references
        self.time_slots[day].append((start_edit, end_edit))

    def remove_time_slot(self, day):
        group_box = getattr(self, f"{day.lower()}GroupBox")
        main_layout = group_box.layout()

        if not self.time_slots[day]:
            return

        # Remove the last QTimeEdit pair
        self.time_slots[day].pop()

        # Find and remove the last QHBoxLayout
        for i in reversed(range(main_layout.count())):
            item = main_layout.itemAt(i)
            if isinstance(item, QHBoxLayout):
                layout = main_layout.takeAt(i).layout()
                # Clear widgets from the layout
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                break

    def create_class(self):
        if not self.validate_inputs():
            return

        # Build the schedule based on checked days
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
            spreadsheet_path=self.spreadsheet_path
        )

        if self.class_manager.get_class_by_code(new_class.class_code):
            QMessageBox.warning(self, "Error", "Class code already exists!")
            return

        self.class_manager.add_class(new_class)
        QMessageBox.information(self, "Success", "Class created successfully!")
        self.close()
            
    def load_spreadsheet(self):
        """Load and process student spreadsheet, integrated with ClassManager"""
        # Get required class information first
        class_code = self.class_code_le.text().strip()
        if not class_code:
            QMessageBox.warning(self, "Missing Information", "Please enter class code first")
            return

        # Get spreadsheet file
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Student Spreadsheet", "",
            "Spreadsheet Files (*.csv *.xlsx *.ods *.xls)"
        )
        if not file_path:
            return

        try:
            # Read and process spreadsheet
            if file_path.endswith(".xls"):
                df = pd.read_excel(file_path, skiprows=8, header=None, engine="xlrd")
            else:
                df = pd.read_csv(file_path, skiprows=8, header=None)

            # Process student data
            processed_data = []
            for _, row in df.iterrows():
                # Extract student number components
                student_number = f"{row[2]}{row[3]}".strip().replace(".0nan", "").replace("nannan", "")
                
                # Extract full name components
                name_parts = [str(row[col]) for col in [4, 5, 6] if not pd.isna(row[col])]
                full_name = " ".join(name_parts).replace("nan", "").strip()

                if student_number and full_name:
                    processed_data.append({
                        "Student Number": student_number,
                        "Student Name Surname": full_name,
                        "Not Attended Hours": 0,
                        "Attended Hours": 0,
                        "Card ID": None
                    })

            # Create final DataFrame
            processed_df = pd.DataFrame(processed_data)

            # Create class directory structure
            class_dir = Path("data") / str(self.user_id) / class_code
            class_dir.mkdir(parents=True, exist_ok=True)

            # Save student list
            spreadsheet_path = class_dir / "student_list.xlsx"
            processed_df.to_excel(spreadsheet_path, index=False, engine="openpyxl")

            # Store path in class instance
            self.spreadsheet_path = str(spreadsheet_path)

            QMessageBox.information(self, "Success", 
                                  "Student list processed and saved with class data!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Spreadsheet processing failed: {str(e)}")

    def validate_inputs(self):
        print("Validating input fields...")

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
                print(f"Validation failed: {field_name} is missing!")
                QMessageBox.warning(self, "Missing Field", f"{field_name} is required!")
                return False

        try:
            float(self.attendance_policy_le.text())
            int(self.late_threshold_le.text())
            int(self.number_of_weeks_le.text())
            float(self.total_hours_le.text())
            float(self.weekly_hours_le.text())
        except ValueError as e:
            print(f"Validation failed: Invalid number input - {e}")
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers in numeric fields")
            return False

        print("Validation passed.")
        return True