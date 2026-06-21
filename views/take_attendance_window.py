import qtawesome as qta
from PyQt5.QtWidgets import QDialog, QMessageBox, QComboBox, QTableWidgetItem, QInputDialog, QHeaderView
from PyQt5.QtCore import QTimer, QDateTime, QTime
from PyQt5.QtGui import QColor
from PyQt5 import uic
import serial
import serial.tools.list_ports

from services.api_client import ApiClient, ApiError


class TakeAttendance(QDialog):
    def __init__(self, class_obj, class_window):
        super().__init__()
        uic.loadUi("ui/take_attendance_window.ui", self)

        self.class_obj = class_obj
        self.class_window = class_window
        self.api_client = ApiClient()
        self.current_card_id = None
        self.roster = []
        self.staged_records = []
        self.ser = None

        self.load_roster()
        self.setup_ui()
        self.setup_serial()

    def load_roster(self):
        """Load the class roster (with registered card IDs) from the server."""
        try:
            self.roster = self.api_client.get_roster(self.class_obj.class_id)
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Failed to load roster: {e}")
            self.close()

    def setup_ui(self):
        self.class_name_lbl.setText(f"Taking attendance for {self.class_obj.class_name}")
        self.start_attendance_btn.clicked.connect(self.start_attendance)
        self.submit_attendance_btn.clicked.connect(self.submit_attendance)
        self.calendarWidget.selectionChanged.connect(self.update_date_info)

        self.export_to_excel_btn.setIcon(qta.icon("fa5s.file-excel", color="#4F46E5"))
        self.start_attendance_btn.setIcon(qta.icon("fa5s.play", color="white"))
        self.submit_attendance_btn.setIcon(qta.icon("fa5s.check-circle", color="white"))

        self.take_attendance_tableWidget.setAlternatingRowColors(True)
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

        for port in ports:
            if 'RFID' in port.description.upper() or 'SCM' in port.description.upper():
                rfid_port = port.device
                break

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

    def find_student_by_card(self, card_id):
        return next((s for s in self.roster if s.get("card_id") == card_id), None)

    def process_card(self, card_id):
        """Process detected RFID card with late check"""
        student = self.find_student_by_card(card_id)
        if student:
            self.mark_attendance(student)
        else:
            self.register_card(card_id)

    def compute_status(self, time_slot):
        now = QDateTime.currentDateTime()
        start_time_str = time_slot.split('-')[0].strip()
        start_time = QTime.fromString(start_time_str, "HH:mm")
        time_diff = start_time.secsTo(now.time()) / 60  # minutes
        status = "Late" if time_diff > self.class_obj.late_threshold else "Present"
        return status, now.toString("HH:mm")

    def mark_attendance(self, student):
        selected_date = self.calendarWidget.selectedDate().toString("dd-MM-yyyy")
        time_slot = self.hours_comboBox.currentText()
        status, exact_time_str = self.compute_status(time_slot)
        self.record_attendance(student, selected_date, time_slot, exact_time_str, status)

    def register_card(self, card_id):
        """Register new RFID card to student and add to attendance"""
        if not self.roster:
            QMessageBox.warning(self, "Error", "No students in roster to register this card to.")
            return

        msg = QMessageBox()
        msg.setWindowTitle("Register New Card")
        msg.setText("Card not registered. Select student:")

        combo = QComboBox()
        combo.addItems([s["name_surname"] for s in self.roster])
        msg.layout().addWidget(combo)
        msg.exec_()

        selected_student = combo.currentText()
        student = next(s for s in self.roster if s["name_surname"] == selected_student)

        try:
            self.api_client.register_card(student["student_id"], card_id)
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Failed to register card: {e}")
            return
        student["card_id"] = card_id

        self.mark_attendance(student)
        QMessageBox.information(self, "Registered",
                            f"Card {card_id} registered to {selected_student}")

    def record_attendance(self, student, date, time_slot, exact_time, status):
        """Stage attendance row in the table (sent to the server on submit)"""
        try:
            self.staged_records.append({
                "student_id": student["student_id"],
                "date": date,
                "time_slot": time_slot,
                "time": exact_time,
                "status": status,
            })

            row_position = self.take_attendance_tableWidget.rowCount()
            self.take_attendance_tableWidget.insertRow(row_position)

            items = [
                QTableWidgetItem(str(student["name_surname"])),
                QTableWidgetItem(date),
                QTableWidgetItem(time_slot),
                QTableWidgetItem(exact_time),
                QTableWidgetItem(status)
            ]

            for col, item in enumerate(items):
                self.take_attendance_tableWidget.setItem(row_position, col, item)

            color = QColor(255, 223, 128) if status == "Late" else QColor(144, 238, 144)
            for col in range(len(items)):
                self.take_attendance_tableWidget.item(row_position, col).setBackground(color)

        except Exception as e:
            print(f"Error adding to table: {str(e)}")

    def submit_attendance(self):
        """Send staged attendance records to the server."""
        if not self.staged_records:
            QMessageBox.information(self, "Nothing to Submit", "No attendance has been recorded yet.")
            return

        try:
            self.api_client.submit_attendance(self.class_obj.class_id, self.staged_records)
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Failed to submit attendance:\n{e}")
            return

        self.class_window.load_student_list()
        QMessageBox.information(self, "Success", "Attendance submitted successfully!")
        self.close()

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
