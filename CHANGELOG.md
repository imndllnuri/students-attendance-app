# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/), dates in
YYYY-MM-DD.

## [Unreleased]

### Changed
- **Take Attendance is no longer a separate window.** `TakeAttendance` changed from a `QDialog`
  shown via `.show()` to a `QWidget` embedded as a `MainWindow.stackedWidget` page, exactly like
  `ClassWindow` already was - opening it now navigates within the same window instead of popping
  up a second one. Unlike `ClassWindow`'s cached per-class tabs, a Take Attendance page is torn
  down (`removeWidget()` + `deleteLater()`) on the way out rather than kept around, since its
  roster snapshot and serial/RFID connection would go stale if reused across sessions. The
  "discard unsubmitted records?" confirmation and reader/timer cleanup in `closeEvent()` are
  unchanged - back-navigation still runs through `close()` first and only proceeds if that's
  accepted.
- Renamed the last 3 `.ui` widget-naming outliers to match the dominant convention (ROADMAP.md
  Phase 3): `security_question_ComboBox`/`security_question_2_ComboBox` → `security_question_combo`/
  `security_question_2_combo`, `hours_comboBox` → `hours_combo`.

### Added
- **Offline/local-storage backend (ROADMAP.md Phase 2)**: `services/local_storage_client.py`'s
  `LocalStorageClient` implements the full `ApiClient` method surface against local JSON +
  per-class `.xlsx` files instead of the Flask/SQLite server - zero server process required.
  `shared/backend_config.py`'s `create_client()` decides which backend `AccountManager`/
  `ClassManager` get by default, via `.backend_config.json` (defaults to the server backend,
  unchanged unless explicitly configured); this is also where `ApiClient`'s `base_url`
  became configurable instead of hardcoded. See `ARCHITECTURE.md`.
- `shared/dialogs.py`: `ChoiceDialog` and `DetailDialog`, real `QDialog` subclasses replacing the
  RFID card-registration combo box and the student-detail "Export CSV" button that had previously
  been hand-inserted into a `QMessageBox`'s own layout - the registration dialog also gained a
  proper Cancel path it never had before.

### Changed
- App renamed from "AttendU" to **TapIn**, with a generated contactless-tap
  icon wired into the taskbar/title-bar, sidebar wordmark, and auth screens.
  See `reference-theme/ASSUMPTIONS.md` §18.
- Roster add/remove moved off Class Detail's page and into a new "Roster"
  step of the Edit Class wizard (`views/add_new_class_window.py`); the
  roster table itself still lives on Class Detail, only the mutation
  controls moved. See `reference-theme/ASSUMPTIONS.md` §17.

### Removed
- **Dark mode removed entirely** — the light/dark toggle, `DARK_PALETTE`,
  `shared/theme.py`, `theme_dark.qss`, and every dynamic theme-preference
  code path were deleted rather than left dormant. `FEATURE_BACKLOG.md`
  #27 is corrected to reflect this. See `reference-theme/ASSUMPTIONS.md` §16.

### Fixed
- `qcolor()` (`shared/palette.py`) previously always read the light
  palette regardless of the active theme, so table-cell tints (e.g. Class
  Detail's "Not Attended Hours" column) rendered with light-mode colors in
  dark mode. Fixed before dark mode was removed. See
  `reference-theme/ASSUMPTIONS.md` §15.

## [0.2.0] - feature batch (see FEATURE_BACKLOG.md for the full itemized list)

Roughly 80 features landed across two backlog passes (the original 30 in
`FEATURE_BACKLOG.md` plus all 50 ideas from `ideas.md`), each as its own
commit. Grouped highlights rather than a full duplicate listing — see
`FEATURE_BACKLOG.md` for the authoritative per-item checklist and scope
notes:

- **Login & Account**: password strength indicator, session timeout,
  recent-logins log, two-of-three security questions.
- **Dashboard / My Classes / Search**: Today's Classes + Recently Viewed
  widgets, sort/filter/pin/archive/duplicate/bulk-actions, color tags,
  drag-and-drop custom ordering, compact density toggle, Jump-to-Class
  (Ctrl+K), multi-class spreadsheet import.
- **Class Detail & Roster**: edit-class, roster add/remove, CSV/Excel
  roster export, roster copy-from-another-class, student merge tool,
  visual weekly schedule grid, class notes, at-risk students list,
  attendance record correction.
- **Take Attendance**: manual attendance mode, Mark All Present / Undo
  Last Scan / Mark Selected Absent, live recorded-count, duplicate-card
  warning, session templates, offline submission queueing, unsubmitted-
  records close confirmation.
- **Statistics**: per-student detail, attendance trend line chart,
  cross-class comparison, day/time heatmap, PNG/PDF export.
- **Settings & Profile**: dark mode (later removed, see Unreleased above),
  English/Turkish language selector, font-scale accessibility option,
  settings export/import as JSON, type-your-email delete confirmation.
- **Cross-cutting**: notification/activity feed, keyboard shortcuts,
  admin audit log, scheduled daily DB backup, server connectivity health
  indicator, RFID/ESP8266 hardware plugin hook (`services/card_reader.py`).

## [0.1.0] - initial prototype (Phase 1: hygiene, docs, tests, CI)

### Added
- `tests/` suite (pytest + pytest-qt): server route tests, model/manager
  tests against a fake API client, validation tests, and a widget test
  covering the RFID dedup fix and malformed-serial-data handling.
- `.github/workflows/build.yml` CI, running the test suite on push/PR.
- `.github/` PR and issue templates.
- `scripts/seed_mock_data.py` to populate a fresh dev database with sample
  data for manual GUI exploration.
- `shared/validation.py` centralizing email/password/security-question
  rules previously duplicated across three views.
- `logging_config.py` + basic `logging` setup, called from `main.py`.
- `ARCHITECTURE.md`, `CONTRIBUTING.md`, `DEVELOPMENT.md`, `TESTING.md`,
  `ROADMAP.md`.
- `class_created` signal on `AddNewClassWindow` so a newly created class
  appears immediately in "My Classes" without navigating away and back.

### Changed
- `ClassWindow` and `TakeAttendance` now go through `ClassManager` instead
  of instantiating `ApiClient` directly, matching every other view.
- Delete-class button styling moved from an inline `setStyleSheet()` call
  into the shared `theme.qss`.
- `.ui` files for the class window, login window, and take-attendance
  window had their root widget class renamed from the Qt Designer default
  `Form` to a proper name, matching the other `.ui` files in the project.
- README: removed the stale "Settings is a stub" note (it's been wired up
  for a while) and added pointers to the new docs.

### Fixed
- RFID attendance dedup: re-scanning a card already recorded in the current
  session no longer inserts a duplicate staged attendance row.
- A malformed (non-UTF-8) serial read no longer crashes the attendance
  window's polling timer.
- Password reset now enforces the same letter+digit+length rule as account
  creation and the settings password change (it previously only checked
  length).

### Removed
- Local `accounts.json` (contained real plaintext credentials), `data/`
  (legacy per-instructor JSON/Excel storage), `IoT.zip`, and
  `server/attendance.db` deleted from disk — all were already gitignored
  and never part of git history.

- Working PyQt5 GUI + Flask/SQLite server: accounts, classes, rosters,
  RFID-over-serial attendance capture, per-class attendance table,
  statistics chart.
