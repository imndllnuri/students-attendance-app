"""Tests for the pluggable card-reader hardware backend (#50): the
CardReader interface, the default serial implementation, and the ESP8266
(WiFi) hook, which is exercised here against a real local TCP server so
the transport logic is genuinely verified without needing real hardware.
"""

import socket
import threading

import pytest

from services.card_reader import (
    ESP8266CardReader,
    SerialCardReader,
    create_card_reader,
)
from shared.hardware_config import load_hardware_config, save_hardware_config


class FakeSerial:
    def __init__(self):
        self._lines = []
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


def test_serial_card_reader_polls_and_decodes_lines(monkeypatch):
    fake = FakeSerial()
    monkeypatch.setattr("serial.Serial", lambda *a, **k: fake)

    reader = SerialCardReader(port="COM_FAKE")
    reader.connect()

    assert reader.poll() is None
    fake.push(b"CARD-123\n")
    assert reader.poll() == "CARD-123"


def test_serial_card_reader_discards_malformed_bytes(monkeypatch):
    fake = FakeSerial()
    monkeypatch.setattr("serial.Serial", lambda *a, **k: fake)

    reader = SerialCardReader(port="COM_FAKE")
    reader.connect()
    fake.push(b"\xff\xfe\x00")

    assert reader.poll() is None


def test_serial_card_reader_close_closes_underlying_connection(monkeypatch):
    fake = FakeSerial()
    monkeypatch.setattr("serial.Serial", lambda *a, **k: fake)

    reader = SerialCardReader(port="COM_FAKE")
    reader.connect()
    reader.close()

    assert fake.closed is True


class _LineServer:
    """Minimal TCP server standing in for an ESP8266 reader that writes
    one newline-delimited card ID per scan."""

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.host, self.port = self.sock.getsockname()
        self.conn = None
        self._thread = threading.Thread(target=self._accept, daemon=True)
        self._thread.start()

    def _accept(self):
        self.conn, _ = self.sock.accept()

    def wait_for_client(self, timeout=2):
        self._thread.join(timeout)

    def send_line(self, text):
        self.conn.sendall(text.encode() + b"\n")

    def close(self):
        if self.conn:
            self.conn.close()
        self.sock.close()


@pytest.fixture
def line_server():
    server = _LineServer()
    yield server
    server.close()


def test_esp8266_card_reader_reads_a_scanned_card_over_tcp(line_server):
    reader = ESP8266CardReader(line_server.host, port=line_server.port, timeout=1)
    reader.connect()
    line_server.wait_for_client()

    line_server.send_line("CARD-ESP-1")

    import time
    card_id = None
    for _ in range(20):
        card_id = reader.poll()
        if card_id:
            break
        time.sleep(0.05)

    assert card_id == "CARD-ESP-1"
    reader.close()


def test_esp8266_card_reader_poll_returns_none_when_idle(line_server):
    reader = ESP8266CardReader(line_server.host, port=line_server.port, timeout=0.1)
    reader.connect()
    line_server.wait_for_client()

    assert reader.poll() is None
    reader.close()


def test_create_card_reader_factory_selects_backend():
    assert isinstance(create_card_reader("serial", port="COM1"), SerialCardReader)
    assert isinstance(
        create_card_reader("esp8266", host="192.168.1.50"), ESP8266CardReader
    )


def test_hardware_config_defaults_to_serial_when_no_file_exists(tmp_path, monkeypatch):
    import shared.hardware_config as hc
    monkeypatch.setattr(hc, "HARDWARE_CONFIG_PATH", tmp_path / "missing.json")

    assert load_hardware_config() == {"backend": "serial"}


def test_hardware_config_round_trips_esp8266_settings(tmp_path, monkeypatch):
    import shared.hardware_config as hc
    monkeypatch.setattr(hc, "HARDWARE_CONFIG_PATH", tmp_path / "hardware.json")

    save_hardware_config({"backend": "esp8266", "host": "192.168.1.50", "port": 9000})

    assert load_hardware_config() == {
        "backend": "esp8266", "host": "192.168.1.50", "port": 9000
    }
