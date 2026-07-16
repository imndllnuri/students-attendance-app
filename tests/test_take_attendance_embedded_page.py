"""Take Attendance is embedded as a MainWindow.stackedWidget page (like
ClassWindow), not opened as a separate top-level window - none of the
other take-attendance tests exercise this, since they all construct
TakeAttendance directly against lightweight fakes without a real
MainWindow/ClassWindow behind them."""

import types

import views.main_window as mw
from models.classes import Class
from views.take_attendance_window import TakeAttendance


class FakeClassManager:
    def __init__(self, cls, roster):
        self._cls = cls
        self._roster = roster

    def check_server_health(self, *a, **k):
        return True

    def flush_offline_queue(self, *a, **k):
        return 0

    def load_classes_for_instructor(self, user_id, include_archived=False):
        return [self._cls]

    def get_student_table(self, class_id):
        return {"columns": ["Student Number", "Student Name Surname"], "rows": []}

    def get_statistics(self, class_id):
        return {"present": 0, "late": 0, "absent": 0}

    def get_roster(self, class_id):
        return self._roster

    def submit_attendance(self, class_id, records):
        pass


class FakeAccountManager:
    def get_login_history(self, user_id, limit=10):
        return []


def make_class():
    return Class(
        class_code="COMP101", class_name="Intro to Programming", instructor_id="u1",
        section="1", attendance_policy=70, late_threshold=15, total_weeks=14,
        total_hours=42, weekly_hours=3, schedule={}, class_id="c1",
    )


def build_main_window(qtbot, monkeypatch, class_manager):
    monkeypatch.setattr(mw, "ClassManager", lambda: class_manager)
    monkeypatch.setattr(mw, "AccountManager", FakeAccountManager)
    monkeypatch.setattr(
        "views.take_attendance_window.serial.tools.list_ports.comports", lambda: []
    )

    user = types.SimpleNamespace(user_id="u1", name="Ada", surname="Lovelace")
    window = mw.MainWindow(user)
    qtbot.addWidget(window)
    window._inactivity_timer.stop()
    from PyQt5.QtWidgets import QApplication
    QApplication.instance().removeEventFilter(window)
    window.show()
    return window


def make_roster():
    return [{"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper", "card_id": None}]


def test_take_attendance_is_embedded_as_a_stacked_widget_page(qtbot, monkeypatch):
    cls = make_class()
    window = build_main_window(qtbot, monkeypatch, FakeClassManager(cls, make_roster()))

    class_page = window.open_class_window(cls)
    class_page.attendance_page_show()

    attendance_page = class_page.take_attendance_page
    assert isinstance(attendance_page, TakeAttendance)
    assert window.stackedWidget.indexOf(attendance_page) != -1
    assert window.stackedWidget.currentWidget() is attendance_page


def test_back_button_returns_to_the_class_page_and_tears_down(qtbot, monkeypatch):
    cls = make_class()
    window = build_main_window(qtbot, monkeypatch, FakeClassManager(cls, make_roster()))

    class_page = window.open_class_window(cls)
    class_page.attendance_page_show()
    attendance_page = class_page.take_attendance_page

    attendance_page._return_to_class()

    assert window.stackedWidget.currentWidget() is class_page
    assert window.stackedWidget.indexOf(attendance_page) == -1


def test_declining_the_unsubmitted_records_prompt_stays_on_the_page(qtbot, monkeypatch):
    cls = make_class()
    window = build_main_window(qtbot, monkeypatch, FakeClassManager(cls, make_roster()))

    class_page = window.open_class_window(cls)
    class_page.attendance_page_show()
    attendance_page = class_page.take_attendance_page
    attendance_page.staged_records = [{"student_id": 1, "status": "Present"}]

    from PyQt5.QtWidgets import QMessageBox
    monkeypatch.setattr(
        "views.take_attendance_window.QMessageBox.question", lambda *a, **k: QMessageBox.No
    )

    attendance_page._return_to_class()

    assert window.stackedWidget.currentWidget() is attendance_page
    assert window.stackedWidget.indexOf(attendance_page) != -1
