"""Verifies TakeAttendance can be switched to the ESP8266/WiFi card-reader
backend (#50) via shared/hardware_config.py, without touching the default
serial path exercised by the other take_attendance tests.
"""

from views.take_attendance_window import TakeAttendance


class FakeClassObj:
    def __init__(self):
        self.class_id = "c1"
        self.class_name = "COMP101"
        self.late_threshold = 15
        self.schedule = {}


class FakeClassManager:
    def __init__(self, roster):
        self._roster = roster

    def get_roster(self, class_id):
        return self._roster

    def register_card(self, student_id, card_id):
        pass

    def submit_attendance(self, class_id, records):
        pass


class FakeCardReader:
    def __init__(self, host, port=8888):
        self.host = host
        self.port = port
        self.connected = False
        self.closed = False
        self._queue = []

    def connect(self):
        self.connected = True

    def push(self, card_id):
        self._queue.append(card_id)

    def poll(self):
        return self._queue.pop(0) if self._queue else None

    def close(self):
        self.closed = True


def make_roster():
    return [
        {"student_id": 1, "student_number": "1", "name_surname": "Grace Hopper", "card_id": "CARD-A"},
    ]


def build_window(qtbot, monkeypatch, fake_reader):
    monkeypatch.setattr(
        "views.take_attendance_window.load_hardware_config",
        lambda: {"backend": "esp8266", "host": "192.168.1.50", "port": 9000},
    )
    monkeypatch.setattr(
        "views.take_attendance_window.create_card_reader",
        lambda backend, **kwargs: fake_reader,
    )
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.information", lambda *a, **k: None)
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.critical", lambda *a, **k: None)
    monkeypatch.setattr("views.take_attendance_window.QMessageBox.warning", lambda *a, **k: None)

    class_manager = FakeClassManager(make_roster())
    window = TakeAttendance(FakeClassObj(), class_window=None, class_manager=class_manager)
    qtbot.addWidget(window)
    return window


def test_esp8266_backend_connects_on_setup(qtbot, monkeypatch):
    fake_reader = FakeCardReader("192.168.1.50")
    window = build_window(qtbot, monkeypatch, fake_reader)

    assert window.card_reader is fake_reader
    assert fake_reader.connected is True
    assert window.ser is None


def test_esp8266_backend_check_rfid_marks_attendance(qtbot, monkeypatch):
    fake_reader = FakeCardReader("192.168.1.50")
    window = build_window(qtbot, monkeypatch, fake_reader)

    fake_reader.push("CARD-A")
    window.check_rfid()

    assert len(window.staged_records) == 1
    assert window.staged_records[0]["student_id"] == 1


def test_esp8266_backend_close_closes_the_reader(qtbot, monkeypatch):
    fake_reader = FakeCardReader("192.168.1.50")
    window = build_window(qtbot, monkeypatch, fake_reader)

    window.close()

    assert fake_reader.closed is True
