import logging
import math

import pandas as pd
import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QTableWidgetItem,
    QWidget,
)

from services.api_client import ApiError
from shared.dialogs import ChoiceDialog, DetailDialog
from shared.palette import attendance_tier, qcolor
from shared.qt_style import set_dynamic_property
from shared.widgets import clear_layout

logger = logging.getLogger(__name__)


class ClassWindow(QWidget):
    def __init__(self, class_obj, main_window, class_manager):
        super().__init__()
        uic.loadUi("ui/class_window.ui", self)

        self.class_obj = class_obj
        self.main_window = main_window
        self.class_manager = class_manager
        self.failure = math.ceil((self.class_obj.total_hours) * (100 - self.class_obj.attendance_policy) / 100)
        self.safe = self.failure * 50 / 100
        self._last_roster_df = None
        self.student_list_tableWidget.setAlternatingRowColors(True)
        self._setup_icons()
        self.display_class_details()
        self.setup_connections()
        self.load_student_list()

    def _setup_icons(self):
        self.take_attendance_btn.setIcon(qta.icon("fa5s.clipboard-check", color="white"))
        self.refresh_student_list_btn.setIcon(qta.icon("fa5s.sync-alt", color="#6B6B76"))
        self.refresh_student_list_btn.setToolTip("Refresh roster")
        self.refresh_student_list_btn.setAccessibleName("Refresh roster")
        self.back_to_my_classes_btn.setIcon(qta.icon("fa5s.arrow-left", color="#6B6B76"))
        self.class_settings_btn.setIcon(qta.icon("fa5s.cog", color="#2F5CF0"))

        set_dynamic_property(self.take_attendance_btn, "variant", "primary")
        set_dynamic_property(self.class_settings_btn, "variant", "secondary")
        set_dynamic_property(self.merge_students_btn, "variant", "ghost")
        set_dynamic_property(self.copy_roster_btn, "variant", "ghost")
        set_dynamic_property(self.export_roster_btn, "variant", "ghost")
        set_dynamic_property(self.roster_retry_btn, "variant", "secondary")
        set_dynamic_property(self.save_notes_btn, "variant", "secondary")

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
        self._last_roster_df = df

        if df.shape[0] == 0:
            self._show_roster_status("No students in this class's roster yet.", show_retry=False)
            self.at_risk_widget.setVisible(False)
            self._update_attendance_rate(df)
            return

        self._render_at_risk_list(df)
        self._update_attendance_rate(df)

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

                # Per-session status is plain colored text, not a tinted
                # background - matches the AttendU spec's convention for
                # per-student status inside tables (§4.1), distinct from
                # the filled-pill treatment used for class/session-level
                # state elsewhere (e.g. the ACTIVE/INACTIVE class pill).
                if value.lower() == "1 present":
                    item.setForeground(qcolor("success"))
                elif value.lower() == "1 late":
                    item.setForeground(qcolor("warning"))

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

    def _render_at_risk_list(self, df):
        """Surfaces students whose absence count has reached the "safe"
        threshold used elsewhere for the roster table's color coding, so
        the instructor doesn't have to scan the whole table to spot them.
        Returns the at-risk count, so callers (the Info panel stat card)
        don't need to recompute it."""
        if "Not Attended Hours" not in df.columns:
            self.at_risk_widget.setVisible(False)
            return 0

        at_risk = []
        for _, row in df.iterrows():
            try:
                not_attended = float(row["Not Attended Hours"])
            except (ValueError, TypeError):
                continue
            if not_attended >= self.safe:
                at_risk.append((not_attended, row["Student Name Surname"], row["Student Number"]))

        if not at_risk:
            self.at_risk_widget.setVisible(False)
            return 0

        at_risk.sort(key=lambda item: item[0], reverse=True)
        lines = []
        for not_attended, name, number in at_risk:
            label = "FAILING RISK" if not_attended >= self.failure else "at risk"
            lines.append(f"{name} ({number}) - {not_attended:g} missed - {label}")

        self.at_risk_students_lbl.setText("\n".join(lines))
        self.at_risk_widget.setVisible(True)
        self.main_window.add_notification(
            f"{len(at_risk)} student(s) at risk in {self.class_obj.class_code}"
        )
        return len(at_risk)

    def _update_attendance_rate(self, df):
        """The Class Details card's tinted "Your attendance rate" strip -
        an aggregate across the whole roster, computed straight from the
        already-loaded roster table rather than a second API call."""
        attended = total = 0
        if not df.empty and "Attended Hours" in df.columns and "Not Attended Hours" in df.columns:
            attended = pd.to_numeric(df["Attended Hours"], errors="coerce").fillna(0).sum()
            not_attended = pd.to_numeric(df["Not Attended Hours"], errors="coerce").fillna(0).sum()
            total = attended + not_attended

        rate = int(attended / total * 100) if total else 0
        self.attendance_rate_bar.setValue(rate)
        self.attendance_rate_fraction_lbl.setText(f"{rate}% — {int(attended)}/{int(total)} sessions")
        set_dynamic_property(self.attendance_rate_bar, "tier", attendance_tier(rate, self.class_obj.attendance_policy))

    def display_class_details(self):
        """Displays class details in the UI."""
        self.class_name_header_lbl.setText(self.class_obj.class_name)
        self.class_code_lbl.setText(f"{self.class_obj.class_code} · Section {self.class_obj.section}")
        self.attendance_policy_lbl.setText(f"{self.class_obj.attendance_policy}%")
        self.late_threshold_lbl.setText(f"{self.class_obj.late_threshold} min")
        self.number_of_weeks_lbl.setText(str(self.class_obj.total_weeks))
        self.total_hours_lbl.setText(str(self.class_obj.total_hours))
        self.weekly_hours_lbl.setText(str(self.class_obj.weekly_hours))
        self.render_schedule_grid(self.class_obj.schedule)
        self.class_notes_edit.setPlainText(self.class_obj.notes)

    def save_class_notes(self):
        notes = self.class_notes_edit.toPlainText()
        try:
            self.class_manager.update_class(self.class_obj.class_id, {"notes": notes})
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Could not save notes:\n{e}")
            return
        self.class_obj.notes = notes
        QMessageBox.information(self, "Success", "Notes saved.")

    def setup_connections(self):
        self.back_to_my_classes_btn.clicked.connect(self.return_to_main_window)
        self.refresh_student_list_btn.clicked.connect(self.load_student_list)
        self.roster_retry_btn.clicked.connect(self.load_student_list)
        self.take_attendance_btn.clicked.connect(self.attendance_page_show)
        self.class_settings_btn.clicked.connect(self.open_edit_class_window)
        self.save_notes_btn.clicked.connect(self.save_class_notes)
        self.student_list_tableWidget.cellDoubleClicked.connect(self.handle_roster_cell_double_click)
        self.export_roster_btn.clicked.connect(self.export_roster)
        self.copy_roster_btn.clicked.connect(self.copy_roster_from_class)
        self.merge_students_btn.clicked.connect(self.merge_students)

    _FIRST_SESSION_COLUMN = 4  # Student Number, Name Surname, Not Attended, Attended

    def handle_roster_cell_double_click(self, row, col):
        """Session columns open the attendance-correction prompt (#15);
        the Student Number/Name/hours columns open a per-student detail
        view (#23) instead."""
        if col < self._FIRST_SESSION_COLUMN:
            self.show_student_detail(row)
        else:
            self.correct_attendance_cell(row, col)

    def show_student_detail(self, row):
        student_number_item = self.student_list_tableWidget.item(row, 0)
        student_name_item = self.student_list_tableWidget.item(row, 1)
        if student_number_item is None or student_name_item is None:
            return
        student_number = student_number_item.text()
        student_name = student_name_item.text()

        lines = [f"{student_name} ({student_number})", ""]

        not_attended_item = self.student_list_tableWidget.item(row, 2)
        attended_item = self.student_list_tableWidget.item(row, 3)
        if attended_item is not None and not_attended_item is not None:
            try:
                attended = float(attended_item.text())
                not_attended = float(not_attended_item.text())
                total = attended + not_attended
                pct = (attended / total * 100) if total else 0
                lines.append(f"Attended: {attended_item.text()}  |  Not Attended: {not_attended_item.text()}"
                              f"  |  Attendance Rate: {pct:.0f}%")
            except ValueError:
                lines.append(f"Attended: {attended_item.text()}  |  Not Attended: {not_attended_item.text()}")
            lines.append("")

        session_rows = []
        for col in range(self._FIRST_SESSION_COLUMN, self.student_list_tableWidget.columnCount()):
            header_item = self.student_list_tableWidget.horizontalHeaderItem(col)
            cell_item = self.student_list_tableWidget.item(row, col)
            if header_item is None or cell_item is None:
                continue
            value = cell_item.text()
            status = value.split(" ", 1)[1] if value.startswith("1 ") else "Absent"
            lines.append(f"{header_item.text()}: {status}")
            session_rows.append((header_item.text(), status))

        dialog = DetailDialog(self, "Student Detail", "\n".join(lines), action_label="Export CSV")
        dialog.exec_()
        if dialog.action_triggered:
            self.export_student_attendance_csv(student_name, student_number, session_rows)

    def export_student_attendance_csv(self, student_name, student_number, session_rows):
        if not session_rows:
            QMessageBox.information(self, "Nothing to Export", "No session history for this student yet.")
            return

        default_name = f"{student_number}_{student_name.replace(' ', '_')}_attendance.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Attendance History", default_name, "CSV Files (*.csv)"
        )
        if not file_path:
            return

        df = pd.DataFrame(session_rows, columns=["Session", "Status"])
        try:
            df.to_csv(file_path, index=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to write file:\n{e}")
            return

        QMessageBox.information(self, "Success", f"Attendance history exported to:\n{file_path}")

    def correct_attendance_cell(self, row, col):
        """Double-clicking a session cell in the roster table lets the
        instructor correct a past attendance record (e.g. it was marked
        wrong during the live session)."""
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
        new_status, ok = ChoiceDialog.get_item(
            self, "Correct Attendance",
            f"{student_name} - {date} {time_slot}:",
            statuses, default_index,
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

    def copy_roster_from_class(self):
        """Adds every student from a chosen other class into this class's
        roster, as a lighter alternative to full class duplication when
        only the roster should carry over."""
        try:
            classes = self.class_manager.load_classes_for_instructor(
                self.class_obj.instructor_id, include_archived=True
            )
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Could not load classes:\n{e}")
            return

        other_classes = [c for c in classes if c.class_id != self.class_obj.class_id]
        if not other_classes:
            QMessageBox.information(self, "Nothing to Copy", "You have no other classes to copy a roster from.")
            return

        labels = [f"{c.class_name} ({c.class_code})" for c in other_classes]
        selected_label, ok = QInputDialog.getItem(
            self, "Copy Roster", "Copy roster from:", labels, 0, False
        )
        if not ok:
            return
        source_class = other_classes[labels.index(selected_label)]

        try:
            source_roster = self.class_manager.get_roster(source_class.class_id)
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Could not load source roster:\n{e}")
            return

        if not source_roster:
            QMessageBox.information(self, "Nothing to Copy", f"{source_class.class_code} has no students.")
            return

        reply = QMessageBox.question(
            self, "Confirm Copy",
            f"Copy {len(source_roster)} student(s) from {source_class.class_code} into "
            f"{self.class_obj.class_code}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        added = 0
        errors = []
        for student in source_roster:
            try:
                self.class_manager.add_student(
                    self.class_obj.class_id, student["student_number"], student["name_surname"]
                )
                added += 1
            except ApiError as e:
                errors.append(f"{student['name_surname']}: {e}")

        self.load_student_list()
        if errors:
            QMessageBox.warning(
                self, "Partially Completed",
                f"Copied {added} student(s). Errors:\n" + "\n".join(errors),
            )
        else:
            QMessageBox.information(
                self, "Success", f"Copied {added} student(s) from {source_class.class_code}."
            )

    def export_roster(self):
        try:
            roster = self.class_manager.get_roster(self.class_obj.class_id)
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Could not load roster:\n{e}")
            return

        if not roster:
            QMessageBox.information(self, "Nothing to Export", "This class has no students yet.")
            return

        default_name = f"{self.class_obj.class_code}_roster.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Roster", default_name, "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not file_path:
            return

        df = pd.DataFrame(
            [{"Student Number": s["student_number"], "Name Surname": s["name_surname"]} for s in roster]
        )
        try:
            if file_path.endswith(".csv"):
                df.to_csv(file_path, index=False)
            else:
                df.to_excel(file_path, index=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to write file:\n{e}")
            return

        QMessageBox.information(self, "Success", f"Roster exported to:\n{file_path}")

    def merge_students(self):
        """Merges an accidental duplicate roster entry into the correct
        one: attendance history moves onto the kept student, then the
        duplicate entry is deleted."""
        try:
            roster = self.class_manager.get_roster(self.class_obj.class_id)
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Could not load roster:\n{e}")
            return

        if len(roster) < 2:
            QMessageBox.information(
                self, "Nothing to Merge", "Need at least two students in the roster to merge."
            )
            return

        labels = [f"{s['name_surname']} ({s['student_number']})" for s in roster]

        keep_label, ok = ChoiceDialog.get_item(
            self, "Merge Students", "Keep this student (the correct entry):", labels
        )
        if not ok:
            return
        keep_student = roster[labels.index(keep_label)]

        remaining_labels = [label for label in labels if label != keep_label]
        remove_label, ok = ChoiceDialog.get_item(
            self, "Merge Students", "Merge and remove this duplicate entry:", remaining_labels
        )
        if not ok:
            return
        remove_student = next(
            s for s in roster if f"{s['name_surname']} ({s['student_number']})" == remove_label
        )

        reply = QMessageBox.question(
            self, "Confirm Merge",
            f"Merge '{remove_label}' into '{keep_label}'? This moves all attendance history onto "
            f"'{keep_label}' and permanently deletes the '{remove_label}' entry.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        if self.class_manager.merge_students(keep_student["student_id"], remove_student["student_id"]):
            self.load_student_list()
            QMessageBox.information(self, "Success", "Students merged.")
        else:
            QMessageBox.critical(self, "Error", "Could not merge students.")

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
        # The Edit Class wizard's Roster step adds/removes students directly
        # against the server as each button is clicked, so the roster may
        # have changed even though that's not part of `fields` above.
        self.load_student_list()
        self.main_window.load_classes()

    def attendance_page_show(self):
        from views.take_attendance_window import TakeAttendance
        self.take_attendance_page = TakeAttendance(self.class_obj, self, self.class_manager)
        self.take_attendance_page.show()

    _WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def render_schedule_grid(self, schedule):
        """Renders the weekly schedule as a real day-by-day grid instead of
        a plain 'Day: HH:mm-HH:mm' text block."""
        layout = self.schedule_grid_widget.layout()
        clear_layout(layout)

        days_with_slots = [day for day in self._WEEK_DAYS if any(s.selected for s in schedule.get(day, []))]
        if not days_with_slots:
            no_schedule_lbl = QLabel("No schedule set")
            layout.addWidget(no_schedule_lbl, 0, 0)
            return

        for col, day in enumerate(days_with_slots):
            day_lbl = QLabel(day)
            day_lbl.setObjectName("schedule_day_header_lbl")
            day_lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(day_lbl, 0, col)

            slots = [s for s in schedule[day] if s.selected]
            for row, slot in enumerate(slots, start=1):
                slot_lbl = QLabel(f"{slot.start_time.toString('HH:mm')} - {slot.end_time.toString('HH:mm')}")
                slot_lbl.setObjectName("schedule_slot_chip_lbl")
                slot_lbl.setAlignment(Qt.AlignCenter)
                layout.addWidget(slot_lbl, row, col)

    def return_to_main_window(self):
        """Returns to 'My Classes' view in the main window."""
        self.main_window.show_my_classes()
        self.close()

