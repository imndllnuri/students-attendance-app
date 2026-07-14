# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/), dates in
YYYY-MM-DD.

## [Unreleased]

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

## [0.1.0] - initial prototype

- Working PyQt5 GUI + Flask/SQLite server: accounts, classes, rosters,
  RFID-over-serial attendance capture, per-class attendance table,
  statistics chart.
