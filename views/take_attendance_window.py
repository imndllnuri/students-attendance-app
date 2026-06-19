from PyQt5.QtWidgets import QDialog, QMessageBox, QComboBox, QTableWidgetItem, QInputDialog, QHeaderView
from PyQt5.QtCore import QTimer, QDateTime, QTime
from PyQt5.QtGui import QColor
import pandas as pd
from PyQt5 import uic 
from pathlib import Path
import serial
import serial.tools.list_ports

class TakeAttendance(QDialog):
    def __init__(self, class_obj, ClassWindow):
        super().__init__()
        uic.loadUi("ui/take_attendance_window.ui", self)
        
        self.class_obj = class_obj
        self.class_window = ClassWindow
        self.current_card_id = None
        self.attendance_records = []
        self.ser = None
        self.df = None
        self.file_path = Path("data") / self.class_obj.instructor_id / self.class_obj.class_code / "student_list.xlsx"

        self.failure = self.class_obj.total_hours * (1 - self.class_obj.attendance_policy) / 100

        
        self.load_student_data()
        self.setup_ui()
        self.setup_serial()

    def load_student_data(self):
        #print(self.class_obj.late_threshold)
        """Load student data from spreadsheet"""
        try:
            self.df = pd.read_excel(self.file_path, engine='openpyxl')
            if 'Card ID' not in self.df.columns:
                self.df['Card ID'] = ''
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load student data: {str(e)}")
            self.close()

    def setup_ui(self):
        self.class_name_lbl.setText(f"Taking attendance for {self.class_obj.class_name}")
        self.start_attendance_btn.clicked.connect(self.start_attendance)
        self.submit_attendance_btn.clicked.connect(self.submit_attendance)
        self.calendarWidget.selectionChanged.connect(self.update_date_info)

        self.take_attendance_tableWidget.setColumnCount(5)
        self.take_attendance_tableWidget.setHorizontalHeaderLabels([
            "Student Name Surname", 
            "Date", 
            "Time Slot",
            "Time",
            "Status"
        ])
        self.take_attendance_tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.update_date_info()

    def setup_serial(self):
        """Improved serial connection setup with manual fallback"""
        ports = list(serial.tools.list_ports.comports())
        rfid_port = None
        
        # First try automatic detection
        for port in ports:
            # Check common RFID reader descriptors
            if 'RFID' in port.description.upper() or 'SCM' in port.description.upper():
                rfid_port = port.device
                break
        
        # If automatic detection failed, show port selection dialog
        if not rfid_port:
            port_names = [f"{p.device} ({p.description})" for p in ports]
            if not port_names:
                QMessageBox.critical(self, "Error", "No serial ports found!")
                return
                
            selected, ok = QInputDialog.getItem(
                self, 
                "Select Port", 
                "Choose RFID reader port:", 
                port_names, 
                0, 
                False
            )
            if ok:
                rfid_port = selected.split(" ")[0]
            else:
                return

        try:
            self.ser = serial.Serial(
                rfid_port,
                baudrate=9600,
                timeout=1
            )
            QMessageBox.information(self, "Connected", 
                                f"Connected to {rfid_port}!")
        except Exception as e:
            QMessageBox.critical(self, "Connection Failed", 
                                f"Failed to connect to {rfid_port}:\n{str(e)}")
            self.ser = None
            
    def start_attendance(self):
        """Start listening for RFID cards"""
        if not self.ser:
            QMessageBox.warning(self, "Error", "RFID reader not connected!")
            return
            
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_rfid)
        self.timer.start(100)  # Check every 100ms
        QMessageBox.information(self, "Started", "Listening for RFID cards...")

    def check_rfid(self):
        """Check for RFID card presence"""
        if self.ser.in_waiting > 0:
            card_id = self.ser.readline().decode().strip()
            if card_id and card_id != self.current_card_id:
                self.current_card_id = card_id
                self.process_card(card_id)

    def process_card(self, card_id):
        """Process detected RFID card with late check"""
        now = QDateTime.currentDateTime()
        exact_time = now.time()
        exact_time_str = now.toString("HH:mm")
        
        student = self.df[self.df['Card ID'] == card_id]
        selected_date = self.calendarWidget.selectedDate().toString("dd-MM-yyyy")
        time_slot = self.hours_comboBox.currentText()
        
        if not student.empty:
            # Get session start time from time slot
            start_time_str = time_slot.split('-')[0].strip()
            start_time = QTime.fromString(start_time_str, "HH:mm")
            
            # Calculate time difference
            time_diff = start_time.secsTo(exact_time) / 60  # Difference in minutes
            
            status = "Late" if time_diff > self.class_obj.late_threshold else "Present"
            self.record_attendance(student.iloc[0], selected_date, 
                                time_slot, exact_time_str, status)
        else:
            # New card - show registration dialog
            self.register_card(card_id)

    def register_card(self, card_id):
        """Register new RFID card to student and add to attendance"""
        msg = QMessageBox()
        msg.setWindowTitle("Register New Card")
        msg.setText("Card not registered. Select student:")
        
        combo = QComboBox()
        combo.addItems(self.df['Student Name Surname'].tolist())
        msg.layout().addWidget(combo)
        msg.exec_()
        
        selected_student = combo.currentText()
        student_idx = self.df[self.df['Student Name Surname'] == selected_student].index[0]
        self.df.at[student_idx, 'Card ID'] = str(card_id)
        self.df.to_excel(self.file_path, index=False)
        
        # Get attendance details
        selected_date = self.calendarWidget.selectedDate().toString("dd-MM-yyyy")
        time_slot = self.hours_comboBox.currentText()
        now = QDateTime.currentDateTime()
        exact_time_str = now.toString("HH:mm")
        
        # Calculate status
        start_time_str = time_slot.split('-')[0].strip()
        start_time = QTime.fromString(start_time_str, "HH:mm")
        current_time = now.time()
        time_diff = start_time.secsTo(current_time) / 60  # Difference in minutes
        status = "Late" if time_diff > self.class_obj.late_threshold else "Present"
        
        # Record attendance
        student_data = self.df.loc[student_idx]
        self.record_attendance(student_data, selected_date, time_slot, exact_time_str, status)
        
        QMessageBox.information(self, "Registered", 
                            f"Card {card_id} registered to {selected_student}\n"
                            f"Attendance marked as {status}")

    def record_attendance(self, student, date, time_slot, exact_time, status):
        """Record attendance with status"""
        try:
            row_position = self.take_attendance_tableWidget.rowCount()
            self.take_attendance_tableWidget.insertRow(row_position)

            items = [
                QTableWidgetItem(str(student['Student Name Surname'])),
                QTableWidgetItem(date),
                QTableWidgetItem(time_slot),
                QTableWidgetItem(exact_time),
                QTableWidgetItem(status)
            ]

            for col, item in enumerate(items):
                self.take_attendance_tableWidget.setItem(row_position, col, item)
                
            # Highlight late entries
            if status == "Late":
                for col in range(len(items)):
                    self.take_attendance_tableWidget.item(row_position, col).setBackground(QColor(255, 223, 128))
            else:
                for col in range(len(items)):
                    self.take_attendance_tableWidget.item(row_position, col).setBackground(QColor(144, 238, 144))
            
        except Exception as e:
            print(f"Error adding to table: {str(e)}")

    def submit_attendance(self):
        """Save attendance data to student list and create attendance record"""
        try:
            # Step 1: Extract data from take_attendance_tableWidget
            attendance_data = []
            for row in range(self.take_attendance_tableWidget.rowCount()):
                row_items = []
                for col in range(5):  # 5 columns: Student Name, Date, Time Slot, Time, Status
                    item = self.take_attendance_tableWidget.item(row, col)
                    row_items.append(item.text() if item else "")
                attendance_data.append(row_items)
            
            # Create DataFrame from attendance data
            attendance_df = pd.DataFrame(attendance_data, columns=[
                "Student Name", "Date", "Time Slot", "Time", "Status"
            ])
            
            # Step 2: Save attendance data to a new file in class directory
            class_dir = self.file_path.parent
            timestamp = QDateTime.currentDateTime().toString("ddMMyyyy_HHmmss")
            attendance_record_path = class_dir / f"attendance_{timestamp}.xlsx"
            attendance_df.to_excel(attendance_record_path, index=False)
            
            # Step 3: Update student list with new attendance columns
            # Collect unique Date-Time Slot combinations
            unique_combinations = attendance_df[['Date', 'Time Slot']].drop_duplicates()
            
            # Process each unique combination
            for _, combo in unique_combinations.iterrows():
                date = combo['Date']
                time_slot = combo['Time Slot']
                column_name = f"{date} - {time_slot}"
                
                # Add new column if it doesn't exist
                if column_name not in self.df.columns:
                    self.df[column_name] = 0  # Initialize with 0
                
                # Update attendance status for each student
                for index, student_row in self.df.iterrows():
                    student_name = student_row['Student Name Surname']
                    # Find matching attendance entries
                    mask = (attendance_df['Student Name'] == student_name) & \
                        (attendance_df['Date'] == date) & \
                        (attendance_df['Time Slot'] == time_slot)
                    matching_entries = attendance_df[mask]
                    
                    if not matching_entries.empty:
                        # Get the latest entry based on time
                        latest_entry = matching_entries.sort_values('Time', ascending=False).iloc[0]
                        status = latest_entry['Status']
                        self.df.at[index, column_name] = f"1 {status}"

                            # Increment "Attended Hours" if the student is present or late
                        if status in ["Present", "Late"]:
                            if "Attended Hours" in self.df.columns:
                                self.df.at[index, "Attended Hours"] += 1
                    else:
                        self.df.at[index, column_name] = 0
                        if "Not Attended Hours" in self.df.columns:
                            self.df.at[index, "Not Attended Hours"] += 1
             
            # Save the updated student list to Excel
            self.df.to_excel(self.file_path, index=False, engine='openpyxl')
            
            # Reload the student list in the ClassWindow
            self.class_window.load_student_list()
            
            QMessageBox.information(self, "Success", "Attendance submitted successfully!")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to submit attendance:\n{str(e)}")

    def update_date_info(self):
        """Update date-related information when calendar changes"""
        selected_date = self.calendarWidget.selectedDate()
        day_name = selected_date.toString("dddd")
        date_str = selected_date.toString("dd-MM-yyyy")
        
        self.selected_day_lbl.setText(f"{day_name} - {date_str}")
        self.update_hours_combobox(day_name)

    def update_hours_combobox(self, day_name):
        """Update hours combobox based on selected day's schedule"""
        self.hours_comboBox.clear()
        schedule = self.class_obj.schedule.get(day_name, [])
        
        for slot in schedule:
            if slot.selected:
                time_str = f"{slot.start_time.toString('HH:mm')}-{slot.end_time.toString('HH:mm')}"
                self.hours_comboBox.addItem(time_str)

    def closeEvent(self, event):
        """Cleanup when window closes"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        if self.ser:
            self.ser.close()
        super().closeEvent(event)