"""Covers #13: "Export Report" button wiring the /attendance_sheet endpoint."""

import types

from views.take_attendance_window import TakeAttendance


class FakeClassObj:
    def __init__(self):
        self.class_id = "c1"
        self.class_code = "COMP101"
        self.class_name = "COMP101"
        self.late_threshold = 15
        self.schedule = {}


class FakeClassManager:
    def __init__(self, roster, sheet_rows):
        self._roster = roster
        self._sheet_rows = sheet_rows

    def get_roster(self, class_id):
        return self._roster

    def get_attendance_sheet(self, class_id, date):
        return self._sheet_rows


def build_window(qtbot, monkeypatch, fake_serial, sheet_rows):
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

    class_manager = FakeClassManager([], sheet_rows)
    window = TakeAttendance(FakeClassObj(), class_window=None, class_manager=class_manager)
    qtbot.addWidget(window)
    return window


def test_export_with_no_rows_shows_nothing_to_export_and_skips_save_dialog(
    qtbot, monkeypatch, fake_serial, tmp_path
):
    window = build_window(qtbot, monkeypatch, fake_serial, sheet_rows=[])

    save_dialog_called = []
    monkeypatch.setattr(
        "views.take_attendance_window.QFileDialog.getSaveFileName",
        lambda *a, **k: save_dialog_called.append(True),
    )

    window.export_attendance_sheet()

    assert save_dialog_called == []


def test_export_writes_rows_to_chosen_csv_file(qtbot, monkeypatch, fake_serial, tmp_path):
    rows = [
        {"time_slot": "09:00-10:50", "time": "09:05", "status": "Present",
         "student_number": "1", "name_surname": "Grace Hopper"},
    ]
    window = build_window(qtbot, monkeypatch, fake_serial, sheet_rows=rows)

    out_file = tmp_path / "report.csv"
    monkeypatch.setattr(
        "views.take_attendance_window.QFileDialog.getSaveFileName",
        lambda *a, **k: (str(out_file), "CSV Files (*.csv)"),
    )

    window.export_attendance_sheet()

    assert out_file.exists()
    content = out_file.read_text()
    assert "Grace Hopper" in content
    assert "Present" in content


def test_export_cancelled_dialog_does_not_write_file(qtbot, monkeypatch, fake_serial, tmp_path):
    rows = [{"time_slot": "09:00-10:50", "time": "09:05", "status": "Present",
             "student_number": "1", "name_surname": "Grace Hopper"}]
    window = build_window(qtbot, monkeypatch, fake_serial, sheet_rows=rows)

    monkeypatch.setattr(
        "views.take_attendance_window.QFileDialog.getSaveFileName",
        lambda *a, **k: ("", ""),
    )

    window.export_attendance_sheet()  # should not raise
