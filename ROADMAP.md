# Roadmap

A living document — check items off as they land, and add new ones as scope
becomes clearer. Phases are ordered because later ones build on earlier
ones (notably: the design report in Phase 4 depends on Phases 2-3 settling
first, to avoid rewriting large sections twice).

## Phase 1 — Foundation: hygiene, docs, critical fixes, test/CI scaffolding

- [x] Remove untracked legacy/sensitive files (`accounts.json`, `data/`,
      `IoT.zip`, `server/attendance.db`) from local disk; confirm none were
      ever in git history.
- [x] Full doc set: this file, `ARCHITECTURE.md`, `CONTRIBUTING.md`,
      `DEVELOPMENT.md`, `TESTING.md`, `CHANGELOG.md`, `.github/` PR/issue
      templates + CI workflow.
- [x] Centralize email/password/security-question validation into
      `shared/validation.py` (was duplicated and had drifted out of sync
      across three views).
- [x] Fix the RFID re-scan dedup bug (`views/take_attendance_window.py`) —
      scanning an already-recorded card no longer inserts a duplicate row.
- [x] Catch malformed (non-UTF-8) serial reads instead of crashing.
- [x] Fix "new class doesn't appear without navigating away and back" via a
      `class_created` signal.
- [x] Route `class_window.py`/`take_attendance_window.py` through
      `ClassManager` instead of instantiating `ApiClient` directly.
- [x] Move the inline-styled delete-class button into `theme.qss`.
- [x] Rename inconsistent `.ui` root widget classes (`Form` → real names).
- [x] Add basic `logging` setup, replacing stray `print()`s.
- [x] `tests/` scaffold: pytest + pytest-qt, mocked serial + throwaway
      SQLite fixtures, mock data module, GitHub Actions CI.
- [x] `scripts/seed_mock_data.py` for populating a fresh dev DB without
      hand-entering data or needing RFID hardware.

## Phase 2 — Offline / local-storage backend

Goal: run the whole app with **zero Flask server involvement**, per-class
attendance stored in `.xlsx` files.

- [ ] Design a `LocalStorageClient` implementing the same method surface as
      `ApiClient` (`authenticate`, `create_class`, `get_roster`,
      `submit_attendance`, etc.) so `AccountManager`/`ClassManager` don't
      need to change — only which client they're constructed with.
- [ ] Accounts/classes stored as local files (JSON, reusing the shape
      `server/migrate_legacy_data.py` already knows how to read); attendance
      per class as one `.xlsx` per class via `openpyxl` (already a
      dependency).
- [ ] A config flag/env var to choose backend (`ApiClient` vs
      `LocalStorageClient`) — also the point where `ApiClient`'s hardcoded
      `base_url` should become configurable (see `ARCHITECTURE.md` known
      limitations).
- [ ] Test suite mirroring `tests/test_server_routes.py` but against the
      local adapter, reusing the CI harness from Phase 1.
- [ ] Document the file/folder naming convention chosen.

## Phase 3 — Remaining GUI/architecture fixes

- [ ] Replace `ClassWindow(QMainWindow)` being embedded as a
      `QStackedWidget` page (unsupported pattern — a `QMainWindow` isn't
      meant to be a non-top-level child widget) with a proper widget-based
      page.
- [ ] Introduce a formal `Session`/`AppState` object once the above
      navigation rework happens — doing it earlier would be redundant with
      this change.
- [ ] Consistent modal-vs-non-modal rule across dialogs (currently mixed:
      e.g. account creation is non-modal, password reset is modal, with no
      stated reason for the difference).
- [ ] Remaining `.ui` widget-naming-convention cleanup
      (`security_question_ComboBox` vs `hours_comboBox` vs
      `statistics_class_combo` — pick one convention).

## Phase 4 — Software design/architecture report

- [ ] Write a professional report (architecture, data model, GUI, offline
      mode, API) in LaTeX, compiled to PDF, with a pandoc-generated `.docx`
      alongside it.
- [ ] Source material: `ARCHITECTURE.md`, kept in sync incrementally through
      Phases 1-3, so this is largely a transcription/formatting pass rather
      than fresh technical writing.

## Phase 5 — Hardware tutorial + mocked-hardware-in-the-loop testing

- [ ] RFID RC522 + ESP32 wiring and firmware tutorial (the hardware side of
      this project), written as a learning document.
- [ ] Extend the Phase 1 `FakeSerial` test pattern into a fuller
      hardware-in-the-loop test mode, so GUI changes can be validated
      without physical hardware attached, and real hardware can be swapped
      in for final validation.

## Possible future additions (not yet scoped into a phase)

- Packaging/distribution (e.g. PyInstaller) — would justify adding
  `BUILDING.md`, `VERSIONING.md`, and `RELEASE_PROCESS.md`, intentionally
  skipped in Phase 1 since there's currently no compiled/packaged release
  process to document.
