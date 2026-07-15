"""Pluggable card-reader backends for Take Attendance (#50).

The serial RFID reader used in views/take_attendance_window.py is one
concrete hardware backend. This module defines the interface a real
hardware integration should implement - including a WiFi-based reader
such as an ESP8266 running its own small TCP server - so new backends can
be swapped in via shared/hardware_config.py without touching
TakeAttendance's scanning logic.
"""

import socket
from abc import ABC, abstractmethod
from typing import Optional


class CardReader(ABC):
    """A source of RFID card-ID strings, decoupled from the transport
    (serial, TCP/WiFi, etc.) that produces them."""

    @abstractmethod
    def connect(self):
        """Open the underlying connection. May raise on failure."""

    @abstractmethod
    def poll(self) -> Optional[str]:
        """Return a newly scanned card ID, or None if nothing is waiting."""

    @abstractmethod
    def close(self):
        """Release the underlying connection."""


class SerialCardReader(CardReader):
    """Wraps a pyserial connection - the reader backend used by default."""

    def __init__(self, port, baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

    def connect(self):
        import serial
        self.ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=self.timeout)

    def poll(self):
        if not self.ser or self.ser.in_waiting <= 0:
            return None
        try:
            return self.ser.readline().decode().strip()
        except UnicodeDecodeError:
            return None

    def close(self):
        if self.ser:
            self.ser.close()


class ESP8266CardReader(CardReader):
    """Plugin hook for a WiFi RFID reader (e.g. an ESP8266 running a small
    TCP server on the reader's firmware): connects as a TCP client and
    treats each newline-delimited line received as one scanned card ID.

    This is the integration point for real ESP8266 hardware - point it at
    the device's host/port via shared/hardware_config.py."""

    def __init__(self, host, port=8888, timeout=0.1):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None
        self._buffer = b""

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=2)
        self.sock.settimeout(self.timeout)

    def poll(self):
        if not self.sock:
            return None
        try:
            chunk = self.sock.recv(256)
        except socket.timeout:
            return None
        except OSError:
            return None
        if not chunk:
            return None
        self._buffer += chunk
        if b"\n" not in self._buffer:
            return None
        line, _, self._buffer = self._buffer.partition(b"\n")
        try:
            return line.decode().strip()
        except UnicodeDecodeError:
            return None

    def close(self):
        if self.sock:
            self.sock.close()


def create_card_reader(backend, **kwargs) -> CardReader:
    """Factory selecting a CardReader implementation by the configured
    backend name (see shared/hardware_config.py)."""
    if backend == "esp8266":
        return ESP8266CardReader(kwargs["host"], port=kwargs.get("port", 8888))
    return SerialCardReader(kwargs["port"], baudrate=kwargs.get("baudrate", 9600))
