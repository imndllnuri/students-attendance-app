"""Persists which card-reader hardware backend Take Attendance should use
(#50) - the default pyserial-based RFID reader, or an alternate backend
such as a WiFi ESP8266 reader (see services/card_reader.py)."""

import json
from pathlib import Path

HARDWARE_CONFIG_PATH = Path(__file__).resolve().parent.parent / ".hardware_config.json"

DEFAULT_CONFIG = {"backend": "serial"}


def load_hardware_config():
    if not HARDWARE_CONFIG_PATH.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with open(HARDWARE_CONFIG_PATH) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)
    config = dict(DEFAULT_CONFIG)
    config.update(data)
    return config


def save_hardware_config(config):
    with open(HARDWARE_CONFIG_PATH, "w") as f:
        json.dump(config, f)
