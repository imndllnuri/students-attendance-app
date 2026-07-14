# Architecture

This document describes how the app is actually built today. If it drifts
from the code, the code wins — update this file in the same PR that changes
behavior described here (see the closing note).

## Module layout

```
main.py                 # entry point: sets up logging, loads theme.qss, opens LoginWindow
logging_config.py        # console logging setup

views/                   # PyQt5 window/dialog controllers (one per .ui file)
  login_window.py
  main_window.py          # sidebar + QStackedWidget: My Classes / Settings / Search / Profile / Statistics
  create_account_window.py
  reset_password_window.py
  add_new_class_window.py
  class_window.py          # per-class detail page (roster table, launches TakeAttendance)
  take_attendance_window.py# RFID/manual attendance capture dialog

ui/                       # Qt Designer .ui files, one per view above

models/                   # data containers + thin server-backed managers
  accounts.py              # Account, AccountManager
  classes.py               # Class, ScheduleSlot, ClassManager

services/
  api_client.py            # ApiClient: HTTP client wrapping every server route

shared/
  validation.py             # EMAIL_RE, MIN_PASSWORD_LENGTH, SECURITY_QUESTIONS,
                             # is_valid_email(), is_valid_password() - the single
                             # source of truth so views don't redefine these

server/                    # Flask + SQLite backend, runs as its own process
  app.py                    # all REST routes
  db.py                     # sqlite3 connection helper (DB_PATH, get_connection, init_db)
  schema.sql                # table definitions
  migrate_legacy_data.py    # one-off importer from the pre-server JSON/Excel storage

resources/
  styles/theme.qss           # single shared stylesheet, loaded once in main.py
  images/                    # qrc.py/qrc.qrc bundle the university logo; everything
                              # else is a qtawesome icon drawn at runtime

tests/                     # pytest + pytest-qt suite (see TESTING.md)
scripts/                   # dev helper scripts (seed_mock_data.py)
```

## Client/server separation

This is a **client-server desktop app**, not a GUI-only tool: two processes,
started separately, expected to run on the same machine during development.

1. `python -m server.app` starts a Flask process on `127.0.0.1:5000`
   (hardcoded in `services/api_client.py` — see Known limitations below) and
   creates/opens `server/attendance.db` (SQLite) on first run.
2. `python main.py` starts the PyQt5 GUI. Every view constructs (or receives)
   an `AccountManager`/`ClassManager`, never talks to `ApiClient` directly —
   this boundary is intentional and enforced by convention (see
   CONTRIBUTING.md), not by the type system.
3. Call chain for any server interaction:
   `views/*.py` → `models/accounts.py` or `models/classes.py`
   (`AccountManager`/`ClassManager`) → `services/api_client.py` (`ApiClient`,
   raw `requests` calls) → `server/app.py` (Flask route) → `server/db.py`
   (raw `sqlite3`, no ORM) → `server/schema.sql`.
4. Errors from the server surface as `ApiError` from `ApiClient._request()`
   (HTTP status >= 400, or a `ConnectionError` if the server isn't running).
   Managers catch `ApiError` and return `(success, message)` tuples or
   `None`/empty results; views turn that into a `QMessageBox`.

## Data model

Five SQLite tables (`server/schema.sql`), all keyed by UUID strings except
the two autoincrement tables:

- `accounts` (user_id PK, email UNIQUE, password_hash, name, surname,
  security_question, answer_hash) — passwords/answers hashed with
  `werkzeug.security`, never stored or transmitted as reusable hashes to the
  client.
- `classes` (class_id PK, class_code, class_name, instructor_id → accounts,
  section, attendance_policy, late_threshold, total_weeks, total_hours,
  weekly_hours).
- `schedule_slots` (class_id → classes ON DELETE CASCADE, day, start_time,
  end_time, selected) — one row per weekly time block.
- `students` (student_id PK autoincrement, class_id → classes ON DELETE
  CASCADE, student_number, name_surname, card_id nullable) — `card_id` is
  populated the first time a student's RFID card is scanned and not yet
  registered.
- `attendance_records` (id PK autoincrement, class_id, student_id → students
  ON DELETE CASCADE, date, time_slot, time, status).

`GET /students` (`get_student_table` in `server/app.py`) pivots
`attendance_records` into a column-per-session table shaped exactly like the
legacy `student_list.xlsx` roster files did, so the GUI's table-rendering
code in `views/class_window.py` didn't need to change during the migration
off file-based storage.

## Config / known limitations

These are known, intentional simplifications for the current prototype
stage, not oversights — tracked in `ROADMAP.md` where relevant:

- `services/api_client.py` hardcodes `base_url="http://127.0.0.1:5000"`.
  There's no config file or environment variable yet; a real deployment or
  the planned offline mode would need this to be configurable.
- `server/db.py`'s `DB_PATH` is a module-level constant pointing at
  `server/attendance.db` next to the code. Tests override it via
  `monkeypatch` (see `tests/conftest.py`); production has no equivalent
  override mechanism yet.
- No sessions, auth tokens, or CSRF protection — the server trusts every
  request from whoever can reach port 5000. Fine for a single instructor
  running both processes on one laptop; not fine for any shared/networked
  deployment.
- `app.run(debug=True)` in `server/app.py`'s `__main__` block is
  development-only (Flask's debug reloader/debugger should never be exposed
  on a network).

## Hardware integration point

`views/take_attendance_window.py` is the one place hardware touches the app:
it opens a direct serial connection to an RFID reader (auto-detected by
description substring `RFID`/`SCM`, with a manual port-picker fallback) and
polls it via a 100ms `QTimer`. This stands in for the original
RFID RC522 + ESP8266 pipeline described in the project's write-up; a real
network-attached ESP32/ESP8266 would instead `POST /attend` directly against
the Flask server, bypassing this file entirely. See `ROADMAP.md` Phase 5 for
the planned hardware tutorial.

## Testing

See `TESTING.md` for what's covered (server routes, model/manager logic,
validation rules, one RFID-widget test) and the manual QA checklist to run
before considering a change done.

## Keeping this document in sync

This file describes the system as it exists, not as it's planned to become.
When a change to `server/`, `models/`, `services/`, or the client/server
boundary lands, update the relevant section here in the same PR — treat a
stale `ARCHITECTURE.md` as a bug.
