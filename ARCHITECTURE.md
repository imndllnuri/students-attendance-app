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
  add_new_class_window.py  # create/edit/duplicate wizard; when editing an
                            # existing class this also gains a "Roster" step
                            # for adding/removing students (mutation only —
                            # see class_window.py below)
  class_window.py          # per-class detail page: roster table (read-only
                            # display + attendance-status coloring; add/remove
                            # of students happens via the Edit Class wizard's
                            # Roster step), launches TakeAttendance
  take_attendance_window.py# RFID/manual attendance capture, embedded as a
                            # MainWindow.stackedWidget page (like
                            # ClassWindow) rather than a separate window -
                            # torn down (removeWidget + deleteLater()) on
                            # the way out instead of cached, since a
                            # session's roster/serial connection goes
                            # stale if kept around

ui/                       # Qt Designer .ui files, one per view above

models/                   # data containers + thin server-backed managers
  accounts.py              # Account, AccountManager
  classes.py               # Class, ScheduleSlot, ClassManager

services/
  api_client.py            # ApiClient: HTTP client wrapping every server route
  local_storage_client.py  # LocalStorageClient: same method surface as
                            # ApiClient, backed by local JSON/.xlsx files
                            # instead of the Flask server (Phase 2)

shared/
  validation.py             # EMAIL_RE, MIN_PASSWORD_LENGTH, SECURITY_QUESTIONS,
                             # is_valid_email(), is_valid_password() - the single
                             # source of truth so views don't redefine these
  backend_config.py         # create_client(): builds the ApiClient or
                             # LocalStorageClient AccountManager/ClassManager
                             # use by default, per .backend_config.json

server/                    # Flask + SQLite backend, runs as its own process
  app.py                    # all REST routes
  db.py                     # sqlite3 connection helper (DB_PATH, get_connection, init_db)
  schema.sql                # table definitions
  migrate_legacy_data.py    # one-off importer from the pre-server JSON/Excel storage

resources/
  styles/theme.qss           # single shared stylesheet, loaded once in main.py
  images/                    # qrc.py/qrc.qrc bundle the university logo,
                              # app_icon.png is the generated TapIn app icon;
                              # everything else is a qtawesome icon drawn at
                              # runtime

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

## Offline / local-storage backend (Phase 2)

`services/local_storage_client.py`'s `LocalStorageClient` implements the
exact same method surface as `ApiClient` — every view/model call goes
through `AccountManager`/`ClassManager` either way, so nothing above the
client boundary needs to know or care which backend is active. Which one
`AccountManager()`/`ClassManager()` construct by default is decided once,
in `shared/backend_config.py`'s `create_client()`, driven by
`.backend_config.json` (`{"backend": "server"|"local", "base_url": ...,
"local_data_dir": ...}` — mirrors `shared/hardware_config.py`'s pattern).
Defaults to `"server"` (today's `ApiClient` behavior, unchanged unless
explicitly configured).

`LocalStorageClient` stores everything as plain files under a data
directory (default `local_data/`, gitignored): `accounts.json`,
`login_history.json`, and one `classes/<class_id>.json` (metadata/schedule)
+ `classes/<class_id>.xlsx` (a "Roster" sheet and a long-form "Attendance"
sheet — one row per recorded scan, not a pivoted crosstab) per class.
`get_student_table()`/`get_statistics()` pivot/aggregate that long-form
sheet in Python, mirroring `server/app.py`'s SQL logic step for step rather
than reinventing the shape. See the module docstring for the full layout
and why it's a fresh JSON schema rather than a literal reuse of the old
pre-server `data/<instructor>/<class>/` format (that format stored
plaintext passwords, which this one deliberately does not).

## Config / known limitations

These are known, intentional simplifications for the current prototype
stage, not oversights — tracked in `ROADMAP.md` where relevant:

- `services/api_client.py`'s `base_url` (and, since the LAN-deployment work
  below, `api_key`) are configurable via `.backend_config.json` (see above)
  but still default to `"http://127.0.0.1:5000"` / no key if unconfigured
  or constructed directly.
- `server/db.py`'s `DB_PATH` defaults to `server/attendance.db` next to the
  code, but is overridable via the `TAPIN_DB_PATH` env var (tests still
  override it directly via `monkeypatch`, see `tests/conftest.py`).
- Auth is opt-in via the `TAPIN_API_KEY` env var: unset (the default), the
  server behaves exactly as before — every request from whoever can reach
  the port is trusted, fine for a single instructor running both processes
  on one laptop. Set, every route except `/health` requires a matching
  `X-API-Key` header. This is a single shared secret, not sessions/JWT/CSRF
  protection — proportional to a small single-instructor-class LAN app, not
  a public service.
- `app.run(debug=True)` in `server/app.py`'s `__main__` block remains
  development-only (host/port/debug are now also env-configurable via
  `TAPIN_HOST`/`TAPIN_PORT`/`TAPIN_DEBUG`, but the defaults reproduce
  today's behavior unchanged). The production path is `server/wsgi.py`
  under gunicorn — see `DEPLOYMENT.md` for running the server as an
  always-on LAN service on its own machine.

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
