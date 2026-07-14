import logging

import qtawesome as qta
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QGraphicsOpacityEffect,
    QHeaderView,
    QInputDialog,
    QMessageBox,
    QTableWidgetItem,
)
from PyQt5.QtCore import QDateTime, QEasingCurve, QPropertyAnimation, QTime, QTimer
from PyQt5 import uic
import serial
import serial.tools.list_ports

from services.api_client import ApiError
from shared.palette import qcolor

logger = logging.getLogger(__name__)

_SCAN_ICONS = {"idle": "●", "success": "✓", "warning": "!", "error": "✗"}


class TakeAttendance(QDialog):
    def __init__(self, class_obj, class_window, class_manager):
        super().__init__()
        uic.loadUi("ui/take_attendance_window.ui", self)

        self.class_obj = class_obj
        self.class_window = class_window
        self.class_manager = class_manager
        self.current_card_id = None
        self.roster = []
        self.staged_records = []
        self.staged_student_ids = set()
        self.ser = None
        self._listening = False
        self._closed = False

        self.load_roster()
        self.setup_ui()
        self.setup_serial()

    def load_roster(self):
        """Load the class roster (with registered card IDs) from the server."""
        try:
            self.roster = self.class_manager.get_roster(self.class_obj.class_id)
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

        self._scan_opacity_effect = QGraphicsOpacityEffect(self.scan_status_card)
        self.scan_status_card.setGraphicsEffect(self._scan_opacity_effect)
        self._scan_opacity_effect.setOpacity(1.0)
        self._scan_animation = None
        self._set_scan_status("idle", "Press Start Attendance to begin scanning.")

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
                self._set_scan_status(
                    "error", "No serial ports found - check your RFID reader connection."
                )
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
                self._set_scan_status("error", "No reader selected. Take Attendance won't work.")
                return

        try:
            self.ser = serial.Serial(
                rfid_port,
                baudrate=9600,
                timeout=1
            )
            self._set_scan_status(
                "idle", f"Reader connected ({rfid_port}). Press Start to begin scanning."
            )
        except Exception as e:
            logger.warning("Failed to connect to RFID reader %s: %s", rfid_port, e)
            self._set_scan_status("error", f"Couldn't connect to {rfid_port}: {e}")
            self.ser = None

    def start_attendance(self):
        """Start listening for RFID cards"""
        if not self.ser:
            QMessageBox.warning(self, "Error", "RFID reader not connected!")
            return

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_rfid)
        self.timer.start(100)  # Check every 100ms
        self._listening = True
        self._set_scan_status("idle", "Listening for scans...")

    def _set_scan_status(self, state, text, revert_after_ms=None):
        """Update the live scan-status card (idle/success/warning/error) and
        play a brief opacity pulse via QPropertyAnimation so a new event is
        noticeable even though the instructor is watching students, not the
        screen, most of the time."""
        self.scan_status_card.setProperty("state", state)
        self.scan_status_card.style().unpolish(self.scan_status_card)
        self.scan_status_card.style().polish(self.scan_status_card)
        self.scan_status_icon_lbl.setText(_SCAN_ICONS.get(state, ""))
        self.scan_status_text_lbl.setText(text)

        self._scan_opacity_effect.setOpacity(0.4)
        animation = QPropertyAnimation(self._scan_opacity_effect, b"opacity", self)
        animation.setDuration(250)
        animation.setStartValue(0.4)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start(QPropertyAnimation.DeleteWhenStopped)
        self._scan_animation = animation

        if revert_after_ms:
            QTimer.singleShot(revert_after_ms, self._revert_scan_status_to_idle)

    def _revert_scan_status_to_idle(self):
        if self._closed:
            return
        if self._listening:
            self._set_scan_status("idle", "Listening for scans...")
        else:
            self._set_scan_status("idle", "Press Start Attendance to begin scanning.")

    def check_rfid(self):
        """Check for RFID card presence"""
        if self.ser.in_waiting > 0:
            try:
                card_id = self.ser.readline().decode().strip()
            except UnicodeDecodeError:
                logger.warning("Discarding malformed RFID read (undecodable bytes)")
                return
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
            self.class_manager.register_card(student["student_id"], card_id)
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Failed to register card: {e}")
            return
        student["card_id"] = card_id

        # mark_attendance() -> record_attendance() flashes the scan-status
        # card with the attendance result, so no separate "Registered!"
        # confirmation is needed here.
        self.mark_attendance(student)

    def record_attendance(self, student, date, time_slot, exact_time, status):
        """Stage attendance row in the table (sent to the server on submit)"""
        student_id = student["student_id"]
        if student_id in self.staged_student_ids:
            self._set_scan_status(
                "warning",
                f"{student['name_surname']} was already recorded this session.",
                revert_after_ms=1500,
            )
            return

        try:
            self.staged_records.append({
                "student_id": student_id,
                "date": date,
                "time_slot": time_slot,
                "time": exact_time,
                "status": status,
            })
            self.staged_student_ids.add(student_id)

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

            color = qcolor("warning_tint") if status == "Late" else qcolor("success_tint")
            for col in range(len(items)):
                self.take_attendance_tableWidget.item(row_position, col).setBackground(color)

            self._set_scan_status(
                "success",
                f"✓ {student['name_surname']} — {status} at {exact_time}",
                revert_after_ms=1500,
            )

        except Exception:
            logger.exception("Error adding attendance row to table")
            self._set_scan_status(
                "error", "Couldn't record that scan - check the logs.", revert_after_ms=2500
            )

    def submit_attendance(self):
        """Send staged attendance records to the server."""
        if not self.staged_records:
            QMessageBox.information(self, "Nothing to Submit", "No attendance has been recorded yet.")
            return

        try:
            self.class_manager.submit_attendance(self.class_obj.class_id, self.staged_records)
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
        self._closed = True
        if hasattr(self, 'timer'):
            self.timer.stop()
        if self.ser:
            self.ser.close()
        super().closeEvent(event)
