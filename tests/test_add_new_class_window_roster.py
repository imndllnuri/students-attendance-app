"""Covers #12: add/remove individual roster students, now done from the
Edit Class wizard's Roster step instead of Class Detail directly."""

import types

from PyQt5.QtCore import QTime, Qt

import views.add_new_class_window as acw
from models.classes import Class, ScheduleSlot

ROSTER_STEP = acw.ROSTER_STEP


class FakeClassManager:
    def __init__(self, roster=None):
        self._roster = roster if roster is not None else []
        self.added = None
        self.removed_ids = []

    def get_roster(self, class_id):
        return self._roster

    def add_student(self, class_id, student_number, name_surname):
        self.added = (class_id, student_number, name_surname)
        return {"student_id": 99, "student_number": student_number, "name_surname": name_surname}

    def remove_student(self, student_id):
        self.removed_ids.append(student_id)
        return True


def make_class():
    return Class(
        class_code="COMP101",
        class_name="Intro to Programming",
        instructor_id="instr-1",
        section="1",
        attendance_policy=70,
        late_threshold=15,
        total_weeks=14,
        total_hours=42,
        weekly_hours=3,
        schedule={
            "Monday": [
                ScheduleSlot(day="Monday", start_time=QTime(9, 0), end_time=QTime(10, 50), selected=True)
            ]
        },
        class_id="c1",
    )


def build_edit_window(qtbot, monkeypatch, roster=None):
    manager = FakeClassManager(roster)
    monkeypatch.setattr(acw, "ClassManager", lambda: manager)
    monkeypatch.setattr(acw.QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(acw.QMessageBox, "warning", lambda *a, **k: None)
    monkeypatch.setattr(acw.QMessageBox, "critical", lambda *a, **k: None)
    window = acw.AddNewClassWindow("instr-1", existing_class=make_class())
    qtbot.addWidget(window)
    window.show()
    return window


def test_roster_step_is_reachable_when_editing_a_class(qtbot, monkeypatch):
    window = build_edit_window(qtbot, monkeypatch)

    assert window.step_dot_3_lbl.isVisible()
    assert ROSTER_STEP in window._step_sequence()


def test_roster_step_is_skipped_when_creating_a_new_class(qtbot, monkeypatch):
    manager = FakeClassManager()
    monkeypatch.setattr(acw, "ClassManager", lambda: manager)
    window = acw.AddNewClassWindow("instr-1")
    qtbot.addWidget(window)
    window.show()

    assert not window.step_dot_3_lbl.isVisible()
    assert ROSTER_STEP not in window._step_sequence()

    for _ in range(len(window._step_sequence()) - 1):
        window.go_to_next_step()
    assert window._current_step != ROSTER_STEP
    assert window.create_class_btn.isVisible()


def test_navigating_to_roster_step_loads_the_class_roster(qtbot, monkeypatch):
    roster = [{"student_id": 5, "student_number": "20230001", "name_surname": "Grace Hopper"}]
    window = build_edit_window(qtbot, monkeypatch, roster=roster)

    window._go_to_step(ROSTER_STEP)

    assert window.wizard_roster_tableWidget.rowCount() == 1
    assert window.wizard_roster_tableWidget.item(0, 0).text() == "20230001"
    assert window.wizard_roster_tableWidget.item(0, 1).text() == "Grace Hopper"
    assert window.wizard_roster_tableWidget.item(0, 0).data(Qt.UserRole) == 5


def test_add_student_calls_manager_and_clears_fields(qtbot, monkeypatch):
    window = build_edit_window(qtbot, monkeypatch)
    window._go_to_step(ROSTER_STEP)

    window.wizard_new_student_number_le.setText("20230099")
    window.wizard_new_student_name_le.setText("New Student")
    window.add_wizard_roster_student()

    assert window.class_manager.added == ("c1", "20230099", "New Student")
    assert window.wizard_new_student_number_le.text() == ""
    assert window.wizard_new_student_name_le.text() == ""


def test_add_student_rejects_missing_fields(qtbot, monkeypatch):
    window = build_edit_window(qtbot, monkeypatch)
    window._go_to_step(ROSTER_STEP)

    window.wizard_new_student_number_le.setText("")
    window.wizard_new_student_name_le.setText("New Student")
    window.add_wizard_roster_student()

    assert window.class_manager.added is None


def test_remove_selected_student_removes_matching_roster_entry(qtbot, monkeypatch):
    from PyQt5.QtWidgets import QMessageBox

    roster = [{"student_id": 5, "student_number": "20230001", "name_surname": "Grace Hopper"}]
    window = build_edit_window(qtbot, monkeypatch, roster=roster)
    window._go_to_step(ROSTER_STEP)
    monkeypatch.setattr(acw.QMessageBox, "question", lambda *a, **k: QMessageBox.Yes)

    window.wizard_roster_tableWidget.setCurrentCell(0, 0)
    window.remove_wizard_roster_student()

    assert window.class_manager.removed_ids == [5]


def test_remove_selected_student_requires_a_selection(qtbot, monkeypatch):
    warned = []
    window = build_edit_window(qtbot, monkeypatch)
    window._go_to_step(ROSTER_STEP)
    monkeypatch.setattr(acw.QMessageBox, "warning", lambda *a, **k: warned.append(True))

    window.remove_wizard_roster_student()

    assert window.class_manager.removed_ids == []
    assert warned == [True]
