import os

# Must be set before any PyQt5 import happens (directly or via a fixture),
# so the widget tests can run in CI / over SSH without a real display.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

import server.db as db
from server.app import app as flask_app


@pytest.fixture
def sqlite_db(tmp_path, monkeypatch):
    """Point server.db at a throwaway SQLite file and initialize the schema.

    get_connection() re-reads the DB_PATH module attribute on every call,
    so monkeypatching it here is enough to isolate each test - no
    production code changes needed.
    """
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db()
    return db_path


@pytest.fixture
def client(sqlite_db):
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as test_client:
        yield test_client


class FakeSerial:
    """Minimal stand-in for serial.Serial, used to drive TakeAttendance
    without real RFID hardware attached."""

    def __init__(self, lines=None):
        self._lines = list(lines or [])
        self.closed = False

    def push(self, line: bytes):
        self._lines.append(line)

    @property
    def in_waiting(self):
        return len(self._lines)

    def readline(self):
        return self._lines.pop(0) if self._lines else b""

    def close(self):
        self.closed = True


@pytest.fixture
def fake_serial():
    return FakeSerial()
