# Smart Attendance Automation System

A desktop + server app for instructors to manage classes and record student
attendance, originally built for the COMP413 Internet of Things course at
Abdullah Gül University (see `AttendanceAutomation.pdf` for the project
write-up).

## Architecture

The original project (described in the paper) was a full IoT pipeline:
**RFID RC522 + ESP8266 NodeMCU → Flask REST API → MySQL on Google Cloud →
PyQt5 GUI**, with RGB LED feedback on the edge device. The ESP8266/MySQL/Cloud
pieces from that build aren't available anymore, so this repo is the
buildable subset of that architecture:

- **`server/`** — a Flask + SQLite REST API standing in for the
  Flask + MySQL-on-Google-Cloud layer from the paper. Same role: owns
  accounts, classes, rosters and attendance records, and exposes endpoints
  for both the GUI and (in principle) an RFID edge device.
- **GUI (`views/`, `models/`, `ui/`)** — the PyQt5 instructor app. Talks to
  the server over HTTP via `services/api_client.py` instead of reading/writing
  local files directly.
- **RFID capture** — `views/take_attendance_window.py` reads card scans over
  a direct serial connection to an RFID reader (rather than through a
  networked ESP8266), then submits the session's attendance to the server.
  This is the one piece of the original hardware pipeline simplified for a
  no-hardware-required setup; swapping it for HTTP calls from a real ESP8266
  hitting `POST /attend` would restore the original design.

## Features

- Account creation / login, with hashed passwords (`werkzeug.security`)
- Create and manage classes (schedule, attendance policy, roster upload)
- Take attendance per class session (RFID over serial, with manual card
  registration on first scan)
- Per-class attendance table with pass/fail color coding
- Class search
- Attendance statistics (present/late/absent pie chart per class)

### Known stub

- The **Settings** sidebar page is still a placeholder — wiring it up to
  account/profile editing is a natural next step.

## Tech stack

- **GUI**: Python, PyQt5 (`.ui` files via Qt Designer), pandas/matplotlib for
  data display and charts, pyserial for the RFID reader.
- **Server**: Flask, sqlite3 (stdlib), werkzeug for password hashing.

## Running it

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Start the server (creates `server/attendance.db` on first run):
   ```
   python -m server.app
   ```
3. In another terminal, launch the GUI:
   ```
   python main.py
   ```

The GUI talks to `http://127.0.0.1:5000` by default
(`services/api_client.py`).

### Migrating old local data

If you have an existing `accounts.json` / `data/` directory from a previous
version of this app (the JSON/Excel-backed prototype), import it into the
server's database once with:

```
python -m server.migrate_legacy_data
```

## Layout

```
main.py              # GUI entry point, launches LoginWindow
server/               # Flask + SQLite backend
  app.py              # REST endpoints
  schema.sql          # table definitions
  migrate_legacy_data.py
services/
  api_client.py        # HTTP client used by the GUI to talk to the server
models/                 # Account, Class data containers + API-backed managers
views/                  # PyQt5 window controllers (login, class, attendance, etc.)
ui/                     # Qt Designer .ui files
resources/              # images / icons
```

## Status

Functional prototype: GUI + Flask/SQLite server working end to end without
real RFID/ESP8266 hardware required (a serial RFID reader is optional — the
attendance window prompts for manual port selection if one isn't found).
