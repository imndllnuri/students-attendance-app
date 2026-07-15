"""Covers #22: attendance session templates in the Take Attendance window."""

import types
from datetime import datetime

from PyQt5.QtCore import QTime

from views.take_attendance_window import TakeAttendance


class FakeSlot:
    def __init__(self, start_time, end_time, selected=True):
        self.start_time = start_time
        self.end_time = end_time
        self.selected = selected


class FakeClassObj:
    def __init__(self, late_threshold=15, schedule=None):
        self.class_id = "c1"
        self.class_code = "COMP101"
        self.class_name = "COMP101"
        self.late_threshold = late_threshold
        self.schedule = schedule or {}


class FakeClassManager:
    def get_roster(self, class_id):
        return []


def build_window(qtbot, monkeypatch, fake_serial, schedule=None, late_threshold=15):
    monkeypatch.setattr(
        "views.take_attendance_window.serial.tools.list_ports.comports",
        lambda: [types.SimpleNamespace(device="COM_FAKE", description="RFID Reader")],
    )
    monkeypatch.setattr(
        "views.take_attendance_window.serial.Serial", lambda *a, **k: fake_serial
    )
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.information", lambda *a, **k: None)
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.critical", lambda *a, **k: None)
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.warning", lambda *a, **k: None)

    window = TakeAttendance(
        FakeClassObj(late_threshold, schedule), class_window=None, class_manager=FakeClassManager()
    )
    qtbot.addWidget(window)
    return window


def two_slot_schedule():
    today_name = datetime.now().strftime("%A")
    return {today_name: [
        FakeSlot(QTime(9, 0), QTime(10, 50)),
        FakeSlot(QTime(13, 0), QTime(14, 50)),
    ]}


def test_saving_a_template_persists_time_slot_and_override(qtbot, monkeypatch, fake_serial, tmp_path):
    import shared.session_templates as stpl
    monkeypatch.setattr(stpl, "SESSION_TEMPLATES_PATH", tmp_path / ".session_templates.json")

    window = build_window(qtbot, monkeypatch, fake_serial, schedule=two_slot_schedule())
    window.hours_comboBox.setCurrentIndex(1)  # 13:00-14:50
    window.late_threshold_override_le.setText("20")

    window.save_current_as_template()

    saved = stpl.load_session_template("c1")
    assert saved == {"time_slot": "13:00-14:50", "late_threshold_override": 20}


def test_opening_again_applies_the_saved_template(qtbot, monkeypatch, fake_serial, tmp_path):
    import shared.session_templates as stpl
    path = tmp_path / ".session_templates.json"
    monkeypatch.setattr(stpl, "SESSION_TEMPLATES_PATH", path)
    stpl.save_session_template("c1", "13:00-14:50", 25)

    window = build_window(qtbot, monkeypatch, fake_serial, schedule=two_slot_schedule())

    assert window.hours_comboBox.currentText() == "13:00-14:50"
    assert window.late_threshold_override_le.text() == "25"


def test_effective_late_threshold_prefers_override(qtbot, monkeypatch, fake_serial):
    window = build_window(qtbot, monkeypatch, fake_serial, late_threshold=15)
    window.late_threshold_override_le.setText("30")

    assert window._effective_late_threshold() == 30


def test_effective_late_threshold_falls_back_to_class_default(qtbot, monkeypatch, fake_serial):
    window = build_window(qtbot, monkeypatch, fake_serial, late_threshold=15)
    window.late_threshold_override_le.setText("")

    assert window._effective_late_threshold() == 15


def test_saving_with_no_time_slot_shows_nothing_to_save(qtbot, monkeypatch, fake_serial):
    window = build_window(qtbot, monkeypatch, fake_serial, schedule={})
    informed = []
    monkeypatch.setattr(
        "views.take_attendance_window.QMessageBox.information",
        lambda *a, **k: informed.append(True),
    )

    window.save_current_as_template()

    assert informed == [True]
